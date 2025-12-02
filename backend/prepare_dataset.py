import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_API_URL = "http://www.omdbapi.com/"

# A diverse list of movie titles to build our dataset
MOVIE_TITLES = [
    "Inception", "The Matrix", "The Godfather", "Pulp Fiction", "Forrest Gump",
    "The Dark Knight", "Fight Club", "Goodfellas", "Star Wars: Episode V", "Interstellar",
    "Parasite", "The Lion King", "Gladiator", "Saving Private Ryan", "Spirited Away",
    "Back to the Future", "The Prestige", "Whiplash", "Django Unchained", "Alien",
    "Blade Runner 2049", "Mad Max: Fury Road", "Get Out", "The Social Network", "Her",
    "Eternal Sunshine of the Spotless Mind", "No Country for Old Men", "There Will Be Blood",
    "A Separation", "Pan's Labyrinth", "City of God", "Amelie", "Oldboy", "WALL-E",
    "The Departed", "Memento", "Inglourious Basterds", "Snatch", "Lock, Stock and Two Smoking Barrels",
    "Jurassic Park", "Terminator 2: Judgment Day", "The Silence of the Lambs", "Se7en",
    "The Usual Suspects", "L.A. Confidential", "Fargo", "Reservoir Dogs", "Casablanca",
    "Citizen Kane", "Psycho", "Rear Window", "2001: A Space Odyssey", "Apocalypse Now",
    "Taxi Driver", "Raging Bull", "Good Will Hunting", "The Truman Show", "Jaws",
    "E.T. the Extra-Terrestrial", "Schindler's List", "The Green Mile", "The Shawshank Redemption"
]

def fetch_movie_data(title):
    """Fetches detailed data for a single movie title from OMDb."""
    try:
        params = {"apikey": OMDB_API_KEY, "t": title}
        response = requests.get(OMDB_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        movie_data = response.json()
        if movie_data.get("Response") == "True":
            return movie_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {title}: {e}")
    return None

def format_movie_as_text(movie):
    """Formats movie data into a structured text string for training."""
    # Create a descriptive text block for each movie
    text = (
        f"Movie Title: {movie.get('Title', 'N/A')}. "
        f"Year: {movie.get('Year', 'N/A')}. "
        f"Genre: {movie.get('Genre', 'N/A')}. "
        f"Director: {movie.get('Director', 'N/A')}. "
        f"Actors: {movie.get('Actors', 'N/A')}. "
        f"Plot: {movie.get('Plot', 'N/A')}. "
        f"IMDb Rating: {movie.get('imdbRating', 'N/A')}."
    )
    return text

def create_dataset():
    """Fetches data for all movies and saves them to a text file."""
    output_filename = "movie_dataset.txt"
    print(f"Starting dataset creation. Fetching {len(MOVIE_TITLES)} movies...")

    with open(output_filename, "w", encoding="utf-8") as f:
        for title in MOVIE_TITLES:
            print(f"Fetching data for: {title}")
            movie_data = fetch_movie_data(title)
            if movie_data:
                formatted_text = format_movie_as_text(movie_data)
                f.write(formatted_text + "\n")
            # Be respectful to the API and avoid getting rate-limited
            time.sleep(0.5)

    print(f"\nDataset creation complete. Data saved to {output_filename}.")

if __name__ == "__main__":
    if not OMDB_API_KEY:
        print("Error: OMDB_API_KEY not found in .env file. Please add it to proceed.")
    else:
        create_dataset()
