# Cinematch 🎬

Cinematch is an AI-augmented movie recommendation service that allows users to 'like' or 'dislike' films. User interactions build a personalized profile that tracks preferences. The app also features **Cinebot**, an AI chatbot that provides movie recommendations based on natural language queries.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0-green?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?logo=tailwind-css)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [AI/ML Models](#aiml-models)
- [Database Schema](#database-schema)
- [Frontend Pages](#frontend-pages)
- [Future Enhancements](#future-enhancements)

---

## Features

- **Swipe-Based Discovery**: Tinder-style movie browsing — like or dislike movies to build your taste profile
- **Personalized Watchlist**: Save liked movies to your watchlist for future viewing
- **AI-Powered Recommendations**: Cinebot uses BERT-based genre classification to recommend movies based on your text input
- **User Profiles**: Track your favorite genres and viewing statistics
- **Movie Search**: Search the OMDb database for any movie
- **User Authentication**: Secure registration and login with password hashing
- **Responsive Design**: Modern glassmorphism UI that works on desktop and mobile

---

## Tech Stack

### Backend
- **Flask** - Python web framework for building API endpoints
- **Flask-SQLAlchemy** - ORM for database interactions
- **Flask-Login** - User session management
- **Flask-Bcrypt** - Password hashing
- **Transformers (Hugging Face)** - AI model integration

### Frontend
- **HTML5** - Page structure
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript** - Client-side interactivity

### Database
- **PostgreSQL** - Relational database for user profiles and movie data

### External APIs
- **OMDb API** - Open Movie Database for movie information (posters, plots, ratings, etc.)

### AI/ML
- **AventIQ-AI/bert-movie-recommendation-system** - BERT model for genre classification
- **microsoft/DialoGPT-medium** - Fine-tuned chatbot model (Cinebot)

---

## Project Structure

```
Cinematch/
├── run.py                      # Application entry point
├── cinematch.html              # Main swipe interface
├── explore.html                # Movie search/exploration
├── watchlist.html              # User's saved movies
├── cinebot.html                # AI chatbot interface
├── profile.html                # User profile & stats
├── login.html                  # Login page
├── register.html               # Registration page
├── movie_dataset.txt           # Training data for Cinebot
├── backend/
│   ├── __init__.py             # Flask app factory & extensions
│   ├── models.py               # SQLAlchemy database models
│   ├── routes.py               # API endpoints & route handlers
│   ├── train_chatbot.py        # Script to fine-tune DialoGPT
│   ├── prepare_dataset.py      # Dataset preparation utilities
│   ├── requirements.txt        # Python dependencies
│   └── trained_chatbot/        # Fine-tuned model weights
├── static/
│   └── styles/
│       └── modern.css          # Custom CSS styles
```

---

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL installed and running
- OMDb API key (free at [omdbapi.com](http://www.omdbapi.com/apikey.aspx))

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/nulllpunkt/Cinematch.git
   cd Cinematch
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   pip install flask-sqlalchemy flask-bcrypt flask-login transformers torch psycopg2-binary
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create a database (default name: postgres)
   createdb postgres
   ```

---

## Configuration

Create a `.env` file in the project root:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://127.0.0.1:5432/postgres

# OMDb API
OMDB_API_KEY=your-omdb-api-key
```

---

## Running the Application

1. **Start the Flask server**
   ```bash
   python run.py
   ```

2. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5001`

3. **Train the Cinebot model (optional)**
   ```bash
   python backend/train_chatbot.py
   ```
   This fine-tunes DialoGPT on `movie_dataset.txt` and saves the model to `backend/trained_chatbot/`.

---

## API Endpoints

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/movies?title=<title>` | Get movie details by title |
| `GET` | `/api/movies?i=<imdb_id>` | Get movie details by IMDb ID |
| `GET` | `/api/search?q=<query>` | Search movies by keyword |
| `GET` | `/api/random` | Get random movies for discovery |

### User Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/like` | Like a movie (add to watchlist) |
| `POST` | `/api/dislike` | Dislike a movie |
| `GET` | `/api/watchlist` | Get user's watchlist |
| `DELETE` | `/api/like/<imdb_id>` | Remove movie from watchlist |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/register` | Create new account |
| `POST` | `/api/login` | Log in |
| `POST` | `/api/logout` | Log out |
| `GET` | `/api/session` | Check login status |

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/profile` | Get user profile |
| `POST` | `/api/profile` | Update username/email |
| `GET` | `/api/profile/stats` | Get favorite genres & stats |

### Cinebot

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/cinebot` | Get AI recommendations based on text |

---

## AI/ML Models

### Genre Classification (BERT)

The app uses **AventIQ-AI/bert-movie-recommendation-system** from Hugging Face to classify user text into movie genres:

- **Input**: Natural language text (e.g., "I want something scary and thrilling")
- **Output**: Predicted genre (Horror, Thriller, etc.)
- **Supported Genres**: Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, TV Movie, Thriller, War, Western

### Cinebot (DialoGPT)

The chatbot is based on **microsoft/DialoGPT-medium**, fine-tuned on movie-related conversations:

- Training script: `backend/train_chatbot.py`
- Training data: `movie_dataset.txt`
- Output directory: `backend/trained_chatbot/`

---

## Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `username` | String(80) | Unique username |
| `email` | String(120) | Unique email |
| `password_hash` | String(128) | Bcrypt hashed password |
| `created_at` | DateTime | Account creation timestamp |

### Movies Table
| Column | Type | Description |
|--------|------|-------------|
| `imdb_id` | String(20) | Primary key (IMDb ID) |
| `title` | String(255) | Movie title |
| `year` | Integer | Release year |
| `poster_url` | Text | URL to movie poster |
| `genre` | String(255) | Comma-separated genres |
| `plot` | Text | Movie plot summary |
| `imdb_rating` | String(10) | IMDb rating |
| `last_updated` | DateTime | Last data refresh |

### Association Tables
- **user_likes**: Links users to liked movies
- **user_dislikes**: Links users to disliked movies

---

## Frontend Pages

| Page | Description |
|------|-------------|
| `cinematch.html` | Main swipe interface for discovering movies |
| `explore.html` | Search and browse movies |
| `watchlist.html` | View and manage liked movies |
| `cinebot.html` | Chat with AI for recommendations |
| `profile.html` | User profile and viewing statistics |
| `login.html` | User login |
| `register.html` | New user registration |

---

## License

This project is for educational purposes.

---

## Acknowledgments

- [OMDb API](http://www.omdbapi.com/) for movie data
- [Hugging Face](https://huggingface.co/) for AI models
- [Tailwind CSS](https://tailwindcss.com/) for styling

