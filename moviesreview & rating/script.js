const omdbApiKey = '3bb17324'; // Valid OMDB API key
const tmdbApiKey = '22a439d36d29b1236785b8dee07dd5dc'; // Valid TMDB API key
const movieGrid = document.getElementById('movies');
const searchInput = document.getElementById('searchInput');
const suggestions = document.getElementById('suggestions');
const toast = document.getElementById('toast');
const loading = document.getElementById('loading');

// Load reviews from localStorage
function loadReviews(movieId) {
    return JSON.parse(localStorage.getItem(`reviews_${movieId}`)) || { ratings: [], comments: [] };
}

// Save reviews to localStorage
function saveReviews(movieId, reviews) {
    localStorage.setItem(`reviews_${movieId}`, JSON.stringify(reviews));
}

// Show toast notification
function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// Show/hide loading indicator
function toggleLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

// Fallback to OMDB default movies
async function fetchDefaultMovies() {
    toggleLoading(true);
    try {
        const response = await fetch(`http://www.omdbapi.com/?s=movie&apikey=${omdbApiKey}`);
        const data = await response.json();
        if (data.Response === 'True') {
            displayMovies(data.Search, true);
        } else {
            movieGrid.innerHTML = `<p>Error: ${data.Error || 'Unable to fetch default movies.'}</p>`;
            showToast('Failed to load default movies.');
        }
    } catch (error) {
        console.error('Error fetching default movies:', error);
        movieGrid.innerHTML = '<p>Error fetching default movies. Please try again.</p>';
        showToast('Network error while fetching default movies.');
    } finally {
        toggleLoading(false);
    }
}

// Fetch trending movies from TMDB with fallback to OMDB
async function fetchTrendingMovies() {
    toggleLoading(true);
    try {
        const response = await fetch(`https://api.themoviedb.org/3/trending/movie/week?api_key=${tmdbApiKey}`);
        const data = await response.json();
        if (response.ok && data.results) {
            const movies = data.results.map(movie => ({
                Title: movie.title,
                Year: movie.release_date ? movie.release_date.split('-')[0] : 'N/A',
                Poster: movie.poster_path ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` : 'https://via.placeholder.com/150',
                imdbID: `tmdb_${movie.id}` // Prefix TMDB ID to avoid conflicts with OMDB
            }));
            displayMovies(movies, false);
        } else {
            console.warn('TMDB API error:', data.status_message);
            movieGrid.innerHTML = `<p>Error: ${data.status_message || 'Unable to fetch trending movies.'}</p>`;
            showToast('Failed to load trending movies. Using default movies.');
            fetchDefaultMovies();
        }
    } catch (error) {
        console.error('Error fetching trending movies:', error);
        movieGrid.innerHTML = '<p>Error fetching trending movies. Using default movies.</p>';
        showToast('Network error while fetching trending movies.');
        fetchDefaultMovies();
    } finally {
        toggleLoading(false);
    }
}

// Search movies with OMDB API
let debounceTimeout;
async function searchMovies() {
    const query = searchInput.value.trim();
    if (!query) {
        fetchTrendingMovies();
        suggestions.style.display = 'none';
        return;
    }
    toggleLoading(true);
    try {
        const response = await fetch(`http://www.omdbapi.com/?s=${encodeURIComponent(query)}&apikey=${omdbApiKey}`);
        const data = await response.json();
        if (data.Response === 'True') {
            displayMovies(data.Search, true);
            suggestions.style.display = 'none';
        } else {
            movieGrid.innerHTML = `<p>Error: ${data.Error || 'No movies found.'}</p>`;
            suggestions.style.display = 'none';
            showToast('No movies found for your search.');
        }
    } catch (error) {
        console.error('Error fetching movies:', error);
        movieGrid.innerHTML = '<p>Error fetching movies. Please try again.</p>';
        showToast('Network error while searching movies.');
    } finally {
        toggleLoading(false);
    }
}

// Autocomplete suggestions with OMDB API
async function fetchSuggestions(query) {
    if (!query) {
        suggestions.style.display = 'none';
        return;
    }
    try {
        const response = await fetch(`http://www.omdbapi.com/?s=${encodeURIComponent(query)}&apikey=${omdbApiKey}`);
        const data = await response.json();
        if (data.Response === 'True') {
            suggestions.innerHTML = data.Search.slice(0, 5).map(movie => `
                <div onclick="searchInput.value='${movie.Title}'; searchMovies()">${movie.Title} (${movie.Year})</div>
            `).join('');
            suggestions.style.display = 'block';
        } else {
            suggestions.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        suggestions.style.display = 'none';
        showToast('Error loading search suggestions.');
    }
}

// Debounced input for suggestions
searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => fetchSuggestions(searchInput.value.trim()), 300);
});

// Display movies in grid
function displayMovies(movies, isOmdb = false) {
    movieGrid.innerHTML = '';
    movies.forEach(async movie => {
        const reviews = loadReviews(movie.imdbID);
        let movieDetails = '';
        if (isOmdb && movie.imdbID) {
            try {
                const response = await fetch(`http://www.omdbapi.com/?i=${movie.imdbID}&apikey=${omdbApiKey}`);
                const data = await response.json();
                if (data.Response === 'True') {
                    movie.Plot = data.Plot || 'N/A';
                    movie.imdbRating = data.imdbRating || 'N/A';
                }
            } catch (error) {
                console.error('Error fetching movie details:', error);
                movie.Plot = 'N/A';
                movie.imdbRating = 'N/A';
            }
            movieDetails = `
                <p>${movie.Plot}</p>
                <p class="rating">IMDb: ${movie.imdbRating}/10</p>
            `;
        }
        const movieCard = document.createElement('div');
        movieCard.className = 'movie-card';
        movieCard.innerHTML = `
            <img src="${movie.Poster !== 'N/A' ? movie.Poster : 'https://via.placeholder.com/150'}" alt="${movie.Title}">
            <h3>${movie.Title} (${movie.Year})</h3>
            ${movieDetails}
            <div class="review-box">
                <textarea placeholder="Leave a review..." aria-label="Review for ${movie.Title}"></textarea>
                <button onclick="addReview('${movie.imdbID}', this.previousElementSibling.value)">Add Review</button>
            </div>
            <div class="user-reviews">
                ${reviews.comments.map(comment => `<p>${comment}</p>`).join('')}
            </div>
        `;
        movieGrid.appendChild(movieCard);
    });
}

// Add a review
function addReview(movieId, comment) {
    if (!comment.trim()) {
        showToast('Please enter a review.');
        return;
    }
    const reviews = loadReviews(movieId);
    reviews.comments.push(comment);
    saveReviews(movieId, reviews);
    showToast('Review added!');
    searchMovies();
}

// Handle Enter key for search
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchMovies();
        suggestions.style.display = 'none';
    }
});

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !suggestions.contains(e.target)) {
        suggestions.style.display = 'none';
    }
});

// Load trending movies on page load
document.addEventListener('DOMContentLoaded', fetchTrendingMovies);