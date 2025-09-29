import streamlit as st
import requests
import json
import os

# Use Streamlit secrets for API keys
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
OMDB_API_KEY = st.secrets["OMDB_API_KEY"]

REVIEWS_FILE = "reviews.json"
if not os.path.exists(REVIEWS_FILE):
    with open(REVIEWS_FILE, "w") as f:
        json.dump({}, f)

def load_reviews():
    try:
        with open(REVIEWS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_reviews(reviews):
    with open(REVIEWS_FILE, "w") as f:
        json.dump(reviews, f, indent=2)

def fetch_trending_movies():
    try:
        response = requests.get(f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        return [{
            "Title": m["title"],
            "Year": m["release_date"].split("-")[0] if m.get("release_date") else "N/A",
            "Poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else "https://via.placeholder.com/150",
            "imdbID": f"tmdb_{m['id']}"
        } for m in data.get("results", [])]
    except:
        st.error("Failed to fetch trending movies. Check your TMDB API key.")
        return []

def fetch_default_movies():
    try:
        response = requests.get(f"http://www.omdbapi.com/?s=movie&apikey={OMDB_API_KEY}")
        data = response.json()
        if data.get("Response") == "True":
            return data.get("Search", [])
        return []
    except:
        st.error("Failed to fetch default movies. Check your OMDB API key.")
        return []

def fetch_movie_details(imdb_id):
    try:
        response = requests.get(f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}")
        data = response.json()
        if data.get("Response") == "True":
            return {"Plot": data.get("Plot", "N/A"), "imdbRating": data.get("imdbRating", "N/A")}
        return {"Plot": "N/A", "imdbRating": "N/A"}
    except:
        return {"Plot": "N/A", "imdbRating": "N/A"}

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    st.error("Error loading CSS")

st.markdown("<h1>🎬 Trending Movies & Public Reviews</h1>", unsafe_allow_html=True)

query = st.text_input("Search for a movie...", placeholder="Enter movie title...")
movies = []

if query:
    try:
        response = requests.get(f"http://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}")
        data = response.json()
        if data.get("Response") == "True":
            movies = data.get("Search", [])
        else:
            st.warning("No movies found for your search.")
    except:
        st.error("Error searching movies. Check your network or API key.")
else:
    movies = fetch_trending_movies()
    if not movies:
        movies = fetch_default_movies()

reviews = load_reviews()

# Display movies
for movie in movies:
    movie_id = movie["imdbID"]
    if movie_id not in reviews:
        reviews[movie_id] = {"comments": []}

    col1, col2 = st.columns([1, 2], gap="small")
    with col1:
        st.image(movie.get("Poster", "https://via.placeholder.com/150"), width=150)
    with col2:
        st.markdown(f"<h3>{movie.get('Title')} ({movie.get('Year')})</h3>", unsafe_allow_html=True)
        if movie_id.startswith("tt"):
            details = fetch_movie_details(movie_id)
            st.markdown(f"<p>{details['Plot']}</p>", unsafe_allow_html=True)
            st.markdown(f'<p class="rating">IMDb: {details["imdbRating"]}/10</p>', unsafe_allow_html=True)
        review_input = st.text_area(f"Leave a review for {movie.get('Title')}", key=f"review_{movie_id}", placeholder="Your review...")
        if st.button("Add Review", key=f"submit_{movie_id}"):
            if review_input.strip():
                reviews[movie_id]["comments"].append(review_input)
                save_reviews(reviews)
                st.success("Review added!")
            else:
                st.warning("Please enter a review.")

        for comment in reviews[movie_id]["comments"]:
            st.markdown(f'<div class="user-reviews"><p>{comment}</p></div>', unsafe_allow_html=True)
