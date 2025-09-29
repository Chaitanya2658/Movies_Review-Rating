import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()  # For local development
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or st.secrets.get("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY") or st.secrets.get("OMDB_API_KEY")

# ----------------------------
# Initialize reviews file
# ----------------------------
REVIEWS_FILE = "reviews.json"
if not os.path.exists(REVIEWS_FILE):
    with open(REVIEWS_FILE, "w") as f:
        json.dump({}, f)

# ----------------------------
# Helper functions
# ----------------------------
def load_reviews():
    try:
        with open(REVIEWS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_reviews(reviews):
    try:
        with open(REVIEWS_FILE, "w") as f:
            json.dump(reviews, f, indent=2)
    except Exception as e:
        st.error(f"Error saving reviews: {str(e)}")

def show_error(message):
    st.error(message)

# ----------------------------
# Fetch TMDB trending movies
# ----------------------------
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_trending_movies():
    if not TMDB_API_KEY:
        show_error("TMDB API key is missing.")
        return None
    try:
        response = requests.get(f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return [
                {
                    "Title": movie["title"],
                    "Year": movie["release_date"].split("-")[0] if movie["release_date"] else "N/A",
                    "Poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else "https://via.placeholder.com/150",
                    "imdbID": f"tmdb_{movie['id']}"
                } for movie in data["results"]
            ]
        return None
    except requests.exceptions.HTTPError as e:
        show_error(f"TMDB API error: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        show_error(f"Network error fetching trending movies: {e}")
        return None
    except Exception as e:
        show_error(f"Error fetching trending movies: {e}")
        return None

# ----------------------------
# Fetch default OMDB movies
# ----------------------------
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_default_movies():
    if not OMDB_API_KEY:
        show_error("OMDB API key is missing.")
        return None
    try:
        response = requests.get(f"http://www.omdbapi.com/?s=movie&apikey={OMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data["Search"]
        return None
    except requests.exceptions.HTTPError as e:
        show_error(f"OMDB API error: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        show_error(f"Network error fetching default movies: {e}")
        return None
    except Exception as e:
        show_error(f"Error fetching default movies: {e}")
        return None

# ----------------------------
# Fetch movie details from OMDB
# ----------------------------
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_movie_details(imdb_id):
    if not OMDB_API_KEY:
        return {"Plot": "N/A", "imdbRating": "N/A"}
    try:
        response = requests.get(f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        return {"Plot": data.get("Plot", "N/A"), "imdbRating": data.get("imdbRating", "N/A")}
    except Exception:
        return {"Plot": "N/A", "imdbRating": "N/A"}

# ----------------------------
# Main app
# ----------------------------
def main():
    st.set_page_config(page_title="🎬 Trending Movies & Public Reviews", layout="wide")

    # Load CSS if exists
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # Ignore if style.css is missing

    st.title("🎬 Trending Movies & Public Reviews")

    # Search box
    query = st.text_input("Search for a movie...", placeholder="Enter movie title...")

    # Load movies
    movies = None
    if query:
        with st.spinner("Searching movies..."):
            try:
                response = requests.get(f"http://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}")
                response.raise_for_status()
                data = response.json()
                if data.get("Response") == "True":
                    movies = data["Search"]
                else:
                    show_error(f"No movies found for '{query}'")
            except Exception as e:
                show_error(f"Error fetching movies: {e}")
    else:
        with st.spinner("Loading trending movies..."):
            movies = fetch_trending_movies()
            if not movies:
                movies = fetch_default_movies()
                if not movies:
                    show_error("Failed to load movies.")

    # Display movies
    if movies:
        reviews = load_reviews()
        for movie in movies:
            movie_id = movie["imdbID"]
            if movie_id not in reviews:
                reviews[movie_id] = {"comments": []}
            col1, col2 = st.columns([1, 2], gap="small")
            with col1:
                st.image(movie.get("Poster", "https://via.placeholder.com/150"), width=200)
            with col2:
                st.subheader(f"{movie['Title']} ({movie['Year']})")
                if movie_id.startswith("tt"):
                    details = fetch_movie_details(movie_id)
                    st.write(details["Plot"])
                    st.write(f"IMDb: {details['imdbRating']}/10")
                review_text = st.text_area(f"Leave a review for {movie['Title']}", key=f"review_{movie_id}", placeholder="Your review...")
                if st.button("Add Review", key=f"submit_{movie_id}"):
                    if review_text.strip():
                        reviews[movie_id]["comments"].append(review_text)
                        save_reviews(reviews)
                        st.success("Review added!")
                    else:
                        st.warning("Please enter a review.")
                for comment in reviews[movie_id]["comments"]:
                    st.markdown(f"<div class='user-reviews'>{comment}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
