from flask import Blueprint, current_app, jsonify, request, send_from_directory, session
from flask_login import login_required, current_user, login_user, logout_user
from dotenv import load_dotenv
import requests
import random
import re
from pathlib import Path
import torch
import os

from . import db, bcrypt, models
from .models import User, Movie

from transformers import BertTokenizerFast, BertForSequenceClassification

# Load environment variables
load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_API_URL = "http://www.omdbapi.com/"

# --- Load Model and Tokenizer globally ---
try:
    model_name = "AventIQ-AI/bert-movie-recommendation-system"
    tokenizer = BertTokenizerFast.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name)
    model.eval()  # Set model to evaluation mode
    print("Hugging Face model loaded successfully.")
except Exception as e:
    print(f"Error loading Hugging Face model: {e}")
    tokenizer = None
    model = None
# -----------------------------------------

# Serve static files (html pages) from project root (one level up from backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

main = Blueprint('main', __name__)

@main.route("/api/movies", methods=["GET"])
def get_movie():
    movie_title = request.args.get("title")
    imdb_id = request.args.get("i")

    if not movie_title and not imdb_id:
        return jsonify({"error": "Movie title or imdb id is required"}), 400

    params = {"apikey": OMDB_API_KEY}
    if imdb_id:
        params["i"] = imdb_id
    else:
        params["t"] = movie_title
    response = requests.get(OMDB_API_URL, params=params)
    
    if response.status_code == 200:
        movie_data = response.json()
        if movie_data.get("Response") == "True":
            return jsonify(movie_data)
        else:
            return jsonify({"error": movie_data.get("Error", "Movie not found")}), 404
    else:
        return jsonify({"error": "Failed to fetch data from OMDb"}), 500


@main.route("/api/search", methods=["GET"])
def search_movies():
    """Search OMDb using the 's' parameter. Returns a list of brief movie objects."""
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    params = {
        "apikey": OMDB_API_KEY,
        "s": q,
        "type": "movie"
    }
    resp = requests.get(OMDB_API_URL, params=params)
    if resp.status_code != 200:
        return jsonify({"error": "OMDb search failed"}), 500
    data = resp.json()
    results = data.get("Search", [])
    return jsonify({"results": results})


@main.route("/api/random", methods=["GET"])
def random_movies():
    """Return a queue of movies from diverse seed phrases for varied browsing.
    
    Fetches from multiple seed phrases and deduplicates similar titles to ensure
    variety and prevent movies with similar words from appearing consecutively.
    Excludes movies the user has already liked or disliked.
    """
    seeds = ["star", "love", "matrix", "dark", "king", "war", "life", "space", "girl", "man", "boy", "night", "black", "dream", "time", "hero", "city", "world", "adventure", "journey", "quest", "legend", "myth", "future", "past", "ring", "ocean", "fire", "ice", "shadow", "light", "storm", "dragon", "wizard", "knight", "magic", "mystery", "crime", "action", "thriller", "romance", "comedy", "drama", "horror", "sci-fi", "western", "fantasy", "music", "sport", "history"]
    
    # Get set of already-seen movie IDs if user is logged in
    excluded_ids = set()
    if current_user.is_authenticated:
        # Get liked movies
        liked_ids = {m.imdb_id for m in current_user.likes}
        # Get disliked movies (if you have a dislikes relationship)
        disliked_ids = set()
        if hasattr(current_user, 'dislikes'):
            disliked_ids = {m.imdb_id for m in current_user.dislikes}
        excluded_ids = liked_ids | disliked_ids
    
    # Pick 4-6 diverse seeds for this batch to maximize variety
    num_seeds = random.randint(4, 6)
    selected_seeds = random.sample(seeds, min(num_seeds, len(seeds)))
    
    all_results = []
    
    # Fetch movies from each seed
    for seed in selected_seeds:
        params = {"apikey": OMDB_API_KEY, "s": seed, "type": "movie"}
        resp = requests.get(OMDB_API_URL, params=params)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("Search", [])
            # Tag each result with its seed for tracking
            for movie in results:
                movie['_seed'] = seed
            all_results.extend(results)
    
    # Filter: keep only movies with posters and not already seen (no extra API calls)
    all_results = [m for m in all_results 
                   if m.get("Poster") and m.get("Poster") != "N/A" 
                   and m.get("imdbID") not in excluded_ids]
    
    # Deduplicate: remove movies with too many overlapping words in titles
    def get_title_words(title):
        """Extract significant words from title (exclude common words)."""
        common_words = {"the", "a", "an", "and", "or", "in", "of", "to", "for", "is", "it", "be"}
        words = title.lower().split()
        return set(w for w in words if w not in common_words and len(w) > 2)
    
    deduplicated = []
    for movie in all_results:
        title = movie.get("Title", "")
        movie_words = get_title_words(title)
        
        # Check if this movie has too much overlap with recently added movies
        has_significant_overlap = False
        for recent_movie in deduplicated[-3:]:  # Check against last 3 movies
            recent_words = get_title_words(recent_movie.get("Title", ""))
            # If there's more than 1 significant word in common, consider it overlap
            overlap = movie_words & recent_words
            if len(overlap) > 1:
                has_significant_overlap = True
                break
        
        if not has_significant_overlap:
            deduplicated.append(movie)
    
    # Shuffle to randomize order
    random.shuffle(deduplicated)
    
    return jsonify({
        "results": deduplicated[:25],  # Return more results for a fuller queue
        "seeds_used": selected_seeds
    })


@main.route('/api/cinebot', methods=['POST'])
def cinebot_recommend():
    """
    Handles the chatbot interaction, using a Hugging Face model to classify
    the user's text into a movie genre and returning recommendations.
    """
    body = request.get_json(force=True, silent=True) or {}
    text = body.get("text")

    if not model or not tokenizer:
        return jsonify({"error": "Hugging Face model not loaded on server"}), 500

    if not text:
        return jsonify({"error": "Provide 'text' (string) in body"}), 400

    # Genre mapping for the model
    genre_to_label = {
        "Action": 0, "Adventure": 1, "Animation": 2, "Comedy": 3, "Crime": 4,
        "Documentary": 5, "Drama": 6, "Family": 7, "Fantasy": 8, "History": 9,
        "Horror": 10, "Music": 11, "Mystery": 12, "Romance": 13, "Science Fiction": 14,
        "TV Movie": 15, "Thriller": 16, "War": 17, "Western": 18
    }
    
    predicted_genre = "movie" # Default
    
    # Use the BERT model to predict the genre
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    
    predicted_class_id = torch.argmax(outputs.logits, dim=1).item()
    
    # Reverse mapping from id to genre name
    label_to_genre = {v: k for k, v in genre_to_label.items()}
    predicted_genre = label_to_genre.get(predicted_class_id, "movie")

    # Search for movies in that genre using OMDb
    params = {"apikey": OMDB_API_KEY, "s": predicted_genre, "type": "movie"}
    resp = requests.get(OMDB_API_URL, params=params)
    
    if resp.status_code != 200:
        return jsonify({"error": "OMDb search failed after recommendation"}), 500
    
    data = resp.json()
    search_results = data.get("Search", [])
    random.shuffle(search_results)

    # Fetch full details for a few of them
    details = []
    for item in search_results[:5]:
        if item.get("imdbID"):
            detail_params = {"apikey": OMDB_API_KEY, "i": item.get("imdbID")}
            r = requests.get(OMDB_API_URL, params=detail_params)
            if r.status_code == 200 and r.json().get("Response") == "True":
                details.append(r.json())

    return jsonify({
        "recommendations": details, 
        "predicted_genre": predicted_genre
    })


@main.route('/api/dislike', methods=['POST'])
@login_required
def dislike_movie():
    body = request.get_json(force=True, silent=True) or {}
    imdb_id = body.get('imdbID')

    if not imdb_id:
        return jsonify({"error": "imdbID is required"}), 400

    movie = models.Movie.query.filter_by(imdb_id=imdb_id).first()
    if not movie:
        # If the movie isn't in our DB, we don't need to fetch it, just record the dislike
        # This is a simplification; a fuller implementation might add it.
        # For now, we assume a movie must be "known" (liked by someone) to be disliked.
        # A better approach would be to add it to the movie table.
        # Let's add it for consistency.
        params = {"apikey": OMDB_API_KEY, "i": imdb_id}
        r = requests.get(OMDB_API_URL, params=params)
        if r.status_code == 200 and r.json().get('Response') == 'True':
            movie_data = r.json()
            year_str = movie_data.get('Year', '0').split('–')[0]
            year = int(year_str) if year_str.isdigit() else 0
            
            movie = models.Movie(
                imdb_id=movie_data.get('imdbID'),
                title=movie_data.get('Title'),
                year=year,
                poster_url=movie_data.get('Poster'),
                genre=movie_data.get('Genre'),
                plot=movie_data.get('Plot'),
                imdb_rating=movie_data.get('imdbRating')
            )
            db.session.add(movie)
            db.session.commit()
        else:
            return jsonify({"error": "Could not resolve movie from OMDb"}), 404


    if movie not in current_user.dislikes:
        current_user.dislikes.append(movie)
        db.session.commit()
        return jsonify({"disliked": {"imdbID": movie.imdb_id, "title": movie.title}})
    
    return jsonify({"message": "Movie already disliked"}), 200


@main.route('/api/like', methods=['POST'])
@login_required
def like_movie():
    body = request.get_json(force=True, silent=True) or {}
    imdb_id = body.get('imdbID')

    if not imdb_id:
        return jsonify({"error": "imdbID is required"}), 400

    # Check if movie exists in our DB, if not, add it
    movie = models.Movie.query.filter_by(imdb_id=imdb_id).first()
    if not movie:
        # Fetch details from OMDb to populate our database
        params = {"apikey": OMDB_API_KEY, "i": imdb_id}
        r = requests.get(OMDB_API_URL, params=params)
        if r.status_code == 200 and r.json().get('Response') == 'True':
            movie_data = r.json()
            # Convert year to integer, handle 'N/A' or other non-numeric values
            year_str = movie_data.get('Year', '0').split('–')[0]
            year = int(year_str) if year_str.isdigit() else 0
            
            movie = models.Movie(
                imdb_id=movie_data.get('imdbID'),
                title=movie_data.get('Title'),
                year=year,
                poster_url=movie_data.get('Poster'),
                genre=movie_data.get('Genre'),
                plot=movie_data.get('Plot'),
                imdb_rating=movie_data.get('imdbRating')
            )
            db.session.add(movie)
            db.session.commit()
        else:
            return jsonify({"error": "Could not resolve movie from OMDb"}), 404

    # Add the like relationship
    if movie not in current_user.likes:
        current_user.likes.append(movie)
        db.session.commit()
        return jsonify({"saved": {"imdbID": movie.imdb_id, "title": movie.title}})
    
    return jsonify({"message": "Movie already liked"}), 200


@main.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')

        # Basic validation
        if not username or not email:
            return jsonify({"error": "Username and email are required"}), 400

        # Check for uniqueness if username/email is changed
        if username != current_user.username and models.User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 409
        if email != current_user.email and models.User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        current_user.username = username
        current_user.email = email
        db.session.commit()
        return jsonify({"message": "Profile updated successfully", "user": {"username": current_user.username, "email": current_user.email}})

    # GET request
    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "member_since": current_user.created_at.strftime("%B %Y")
    })


@main.route('/api/profile/stats')
@login_required
def profile_stats():
    """Analyzes the user's watchlist to provide profile stats."""
    liked_movies = current_user.likes
    if not liked_movies:
        return jsonify({"favorite_genres": [], "total_movies": 0})

    genre_counts = {}
    for movie in liked_movies:
        genres = movie.genre.split(", ") if movie.genre else []
        for genre in genres:
            if genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    sorted_genres = sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)

    return jsonify({
        "favorite_genres": sorted_genres,
        "total_movies": len(liked_movies)
    })


@main.route('/api/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    watchlist_movies = current_user.likes
    watchlist_data = [
        {
            "imdbID": movie.imdb_id,
            "Title": movie.title,
            "Year": movie.year,
            "Poster": movie.poster_url,
            "Genre": movie.genre,
            "imdbRating": movie.imdb_rating
        } for movie in watchlist_movies
    ]
    return jsonify({"watchlist": watchlist_data})


@main.route('/api/like/<imdb_id>', methods=['DELETE'])
@login_required
def delete_like(imdb_id):
    movie = models.Movie.query.filter_by(imdb_id=imdb_id).first()
    if movie and movie in current_user.likes:
        current_user.likes.remove(movie)
        db.session.commit()
        return jsonify({"deleted": True})
    return jsonify({"deleted": False}), 404


@main.route("/favicon.ico")
def favicon():
    # If you have a favicon in project root, serve it; otherwise return 404
    favicon_path = os.path.join(PROJECT_ROOT, "favicon.ico")
    if os.path.exists(favicon_path):
        return send_from_directory(PROJECT_ROOT, "favicon.ico")
    return ("", 404)


@main.route("/", defaults={"path": "cinematch.html"})
@main.route("/<path:path>")
def serve_frontend(path):
    # Only allow serving files that exist in the project root for safety
    full_path = os.path.join(PROJECT_ROOT, path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return send_from_directory(PROJECT_ROOT, path)
    # If not found, try appending .html
    alt = full_path + ".html"
    if os.path.exists(alt) and os.path.isfile(alt):
        return send_from_directory(PROJECT_ROOT, path + ".html")
    return ("Not Found", 404)


# --- User Authentication Routes ---

@main.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    if models.User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    if models.User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = models.User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)

    return jsonify({
        "message": "Registration successful",
        "user": {"id": new_user.id, "username": new_user.username}
    }), 201

@main.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    # Accept either 'identifier' (username or email) or legacy 'email' field
    identifier = data.get('identifier') or data.get('email') or data.get('username')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier (email or username) and password are required"}), 400

    # Try to find user by email or username
    user = None
    try:
        user = models.User.query.filter((models.User.email == identifier) | (models.User.username == identifier)).first()
    except Exception:
        # Fallback to simple filter_by for older DB setups
        user = models.User.query.filter_by(email=identifier).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        return jsonify({
            "message": "Login successful",
            "user": {"id": user.id, "username": user.username}
        })

    return jsonify({"error": "Invalid credentials"}), 401

@main.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"})

@main.route('/api/session')
def session_status():
    if current_user.is_authenticated:
        return jsonify({
            "is_logged_in": True,
            "user": {"id": current_user.id, "username": current_user.username}
        })
    return jsonify({"is_logged_in": False})
