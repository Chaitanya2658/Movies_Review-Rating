const IMG_BASE = "https://image.tmdb.org/t/p/w500";

document.addEventListener("DOMContentLoaded", getTrendingMovies);

function getTrendingMovies() {
  document.getElementById("loading").style.display = "block";
  fetch('http://localhost:3000/api/trending')
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    })
    .then(data => {
      document.getElementById("loading").style.display = "none";
      displayMovies(data.results);
    })
    .catch(err => {
      document.getElementById("loading").style.display = "none";
      console.error('Error fetching trending movies:', err);
    });
}

function searchMovies() {
  const query = document.getElementById("searchInput").value;
  document.getElementById("loading").style.display = "block";
  if (!query) {
    getTrendingMovies();
    return;
  }
  fetch(`http://localhost:3000/api/search?query=${encodeURIComponent(query)}`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
      return res.json();
    })
    .then(data => {
      document.getElementById("loading").style.display = "none";
      displayMovies(data.results);
    })
    .catch(err => {
      document.getElementById("loading").style.display = "none";
      console.error('Error searching movies:', err);
    });
}

function displayMovies(movies) {
  const container = document.getElementById("movies");
  container.innerHTML = "";

  if (!movies || movies.length === 0) {
    container.innerHTML = "<p>No movies found.</p>";
    return;
  }

  movies.forEach(movie => {
    const movieCard = document.createElement("div");
    movieCard.className = "movie-card";

    const poster = movie.poster_path
      ? `${IMG_BASE}${movie.poster_path}`
      : "https://via.placeholder.com/200x300?text=No+Image";

    movieCard.innerHTML = `
      <img src="${poster}" alt="${movie.title}">
      <h3>${movie.title}</h3>
      <p>Release: ${movie.release_date || "N/A"}</p>
      <p class="rating">⭐ ${movie.vote_average.toFixed(1)} / 10</p>
      
      <div class="review-box">
        <textarea id="review-${movie.id}" placeholder="Write a review..."></textarea>
        <button onclick="addReview(${movie.id})">Submit</button>
        <div class="user-reviews" id="reviews-${movie.id}"></div>
      </div>
    `;

    container.appendChild(movieCard);
    loadReviews(movie.id);
  });
}

function addReview(movieId) {
  const textarea = document.getElementById(`review-${movieId}`);
  const review = textarea.value.trim();

  if (!review) return;

  let reviews = JSON.parse(localStorage.getItem(`reviews-${movieId}`)) || [];
  reviews.push(review);
  localStorage.setItem(`reviews-${movieId}`, JSON.stringify(reviews));

  textarea.value = "";
  loadReviews(movieId);
}

function loadReviews(movieId) {
  const container = document.getElementById(`reviews-${movieId}`);
  let reviews = JSON.parse(localStorage.getItem(`reviews-${movieId}`)) || [];

  container.innerHTML = reviews.map(r => `<p>• ${r}</p>`).join("");
}