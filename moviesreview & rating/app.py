import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Initialize reviews file
REVIEWS_FILE = "reviews.json"
if not os.path.exists(REVIEWS_FILE):
    with open(REVIEWS_FILE, "w") as f:
        json.dump({}, f)

# Load reviews
def load_reviews():
    try:
        with open(REVIEWS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading reviews: {str(e)}")
        return {}

# Save reviews
def save_reviews(reviews):
    try:
        with open(REVIEWS_FILE, "w") as f:
            json.dump(reviews, f, indent=2)
    except Exception as e:
        st.error(f"Error saving reviews: {str(e)}")

# Fetch trending movies from TMDB with retry
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(5), wait=wait_fixed(5), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_trending_movies():
    try:
        response = requests.get(f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            return [{
                "Title": movie["title"],
                "Year": movie["release_date"].split("-")[0] if movie["release_date"] else "N/A",
                "Poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else "https://via.placeholder.com/150",
                "imdbID": f"tmdb_{movie['id']}"
            } for movie in data["results"]]
        st.error("No trending movies found.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            st.error("TMDB API key is invalid or unauthorized. Please regenerate your API key at themoviedb.org.")
        else:
            st.error(f"Error fetching trending movies: {str(e)}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Network error fetching trending movies. Check your internet connection or try a different network: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching trending movies: {str(e)}")
        return None

# Fetch default OMDB movies with retry
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(5), wait=wait_fixed(5), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_default_movies():
    try:
        response = requests.get(f"http://www.omdbapi.com/?s=movie&apikey={OMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data["Search"]
        st.error("No default movies found.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            st.error("OMDB API key is invalid or unauthorized. Please regenerate your API key at omdbapi.com.")
        else:
            st.error(f"Error fetching default movies: {str(e)}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Network error fetching default movies. Check your internet connection or try a different network: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching default movies: {str(e)}")
        return None

# Search movies with OMDB with retry
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(5), wait=wait_fixed(5), retry=retry_if_exception_type(requests.exceptions.RequestException))
def search_movies(query):
    try:
        response = requests.get(f"http://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data["Search"]
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            st.error("OMDB API key is invalid or unauthorized. Please regenerate your API key at omdbapi.com.")
        else:
            st.error(f"Error searching movies: {str(e)}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Network error searching movies. Check your internet connection or try a different network: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error searching movies: {str(e)}")
        return None

# Fetch movie details from OMDB with retry
@st.cache_data(show_spinner=False)
@retry(stop=stop_after_attempt(5), wait=wait_fixed(5), retry=retry_if_exception_type(requests.exceptions.RequestException))
def fetch_movie_details(imdb_id):
    try:
        response = requests.get(f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}")
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return {"Plot": data.get("Plot", "N/A"), "imdbRating": data.get("imdbRating", "N/A")}
        return {"Plot": "N/A", "imdbRating": "N/A"}
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            st.error("OMDB API key is invalid or unauthorized. Please regenerate your API key at omdbapi.com.")
        else:
            st.error(f"Error fetching movie details: {str(e)}")
        return {"Plot": "N/A", "imdbRating": "N/A"}
    except requests.exceptions.ConnectionError as e:
        st.error(f"Network error fetching movie details. Check your internet connection or try a different network: {str(e)}")
        return {"Plot": "N/A", "imdbRating": "N/A"}
    except Exception as e:
        st.error(f"Error fetching movie details: {str(e)}")
        return {"Plot": "N/A", "imdbRating": "N/A"}

# Main app
def main():
    # Load custom CSS
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {str(e)}")

    # Header
    st.markdown("<h1>🎬 Trending Movies & Public Reviews</h1>", unsafe_allow_html=True)

    # Search box with suggestions
    st.markdown("<div class='search-box'>", unsafe_allow_html=True)
    query = st.text_input("Search for a movie...", key="search_input", placeholder="Enter movie title...")
    if query:
        suggestions = search_movies(query)
        if suggestions:
            suggestion_html = "".join([f"<div class='suggestion' onclick=\"document.getElementById('st_search_input').value='{movie['Title'].replace("'", "\\'")}'; document.forms[0].submit();\">{movie['Title']} ({movie['Year']})</div>" for movie in suggestions[:5]])
            st.markdown(f"<div class='suggestions'>{suggestion_html}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Initialize session state for toast
    if "toast" not in st.session_state:
        st.session_state.toast = None

    # Display toast
    if st.session_state.toast:
        st.markdown(f'<div class="toast">{st.session_state.toast}</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <script>
            setTimeout(() => {
                const toast = document.querySelector('.toast');
                if (toast) {
                    toast.classList.add('show');
                    setTimeout(() => toast.classList.remove('show'), 3000);
                }
            }, 100);
            </script>
            """,
            unsafe_allow_html=True
        )

    # Load movies
    movies = None
    if query:
        with st.spinner("Loading..."):
            movies = search_movies(query)
            if not movies:
                st.error("No movies found.")
                st.session_state.toast = "No movies found for your search."
    else:
        with st.spinner("Loading..."):
            movies = fetch_trending_movies()
            if not movies:
                movies = fetch_default_movies()
                if not movies:
                    st.error("Failed to load movies.")
                    st.session_state.toast = "Failed to load movies. Please try again."

    # Display movies
    if movies:
        st.markdown('<div id="movies">', unsafe_allow_html=True)
        reviews = load_reviews()
        for movie in movies:
            movie_id = movie["imdbID"]
            if movie_id not in reviews:
                reviews[movie_id] = {"comments": []}
            with st.container():
                col1, col2 = st.columns([1, 2], gap="small")
                with col1:
                    st.image(movie["Poster"], width=200)
                with col2:
                    st.markdown(f"<h3>{movie['Title']} ({movie['Year']})</h3>", unsafe_allow_html=True)
                    if movie_id.startswith("tt"):  # OMDB movie
                        details = fetch_movie_details(movie_id)
                        st.markdown(f"<p>{details['Plot']}</p>", unsafe_allow_html=True)
                        st.markdown(f'<p class="rating">IMDb: {details["imdbRating"]}/10</p>', unsafe_allow_html=True)
                    review = st.text_area(f"Leave a review for {movie['Title']}", key=f"review_{movie_id}", placeholder="Your review...")
                    if st.button("Add Review", key=f"submit_{movie_id}"):
                        if review.strip():
                            reviews[movie_id]["comments"].append(review)
                            save_reviews(reviews)
                            st.session_state.toast = "Review added!"
                            st.rerun()
                        else:
                            st.session_state.toast = "Please enter a review."
                    for comment in reviews[movie_id]["comments"]:
                        st.markdown(f'<div class="user-reviews"><p>{comment}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()