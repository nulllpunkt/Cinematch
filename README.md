# Cinematch

Cinematch is an AI-augmented movie recommendation service that allows users to 'like' or 'dislike' films, and that data will be used to create a profile on the user that tracks their preferences. It will also feature a chatbot named Cinebot that the user can chat with and ask for movie reccomendations or other general inquiries about films.

I am looking into using Open Movie Database API (OPMDb) to gather information on movies (plot, poster, rating, etc.)
I will also be using a movie reccomendation model from Hugging Face, I have found these two models:

https://huggingface.co/datasets/sileod/movie_recommendation
https://huggingface.co/AventIQ-AI/bert-movie-recommendation-system

Using these models will require me to configure HuggingFace API within my app.

Backend considerations: Use Flask or FastAPI for building API endpoints, handling user requests, HuggingFace integration using Python.
Frontend considerations: Currently using HTML, Tailwind CSS, and JavaScript.
Database considerations: Considering PostgreSQL to build user profile + track their preferences.

