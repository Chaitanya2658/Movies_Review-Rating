// require('dotenv').config({ path: './.env' });
// console.log('TMDB_API_KEY:', process.env.TMDB_API_KEY || 'Not loaded');

const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const port = 3000;

const API_KEY = '22a439d36d29b1236785b8dee07dd5dc'; // Hardcoded
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

app.use(cors());
app.use(express.static('../Public')); // Matches capitalized Public

app.get('/api/trending', async (req, res) => {
  try {
    if (!API_KEY) throw new Error('TMDB_API_KEY is not defined');
    console.log('Fetching trending movies...');
    const response = await axios.get(`${TMDB_BASE_URL}/trending/movie/week?api_key=${API_KEY}`);
    console.log('Trending movies fetched successfully');
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching trending movies:', error.message, error.response ? error.response.data : '');
    res.status(500).json({ error: 'Failed to fetch trending movies' });
  }
});

app.get('/api/search', async (req, res) => {
  const query = req.query.query;
  if (!query) {
    return res.status(400).json({ error: 'Query parameter is required' });
  }
  try {
    if (!API_KEY) throw new Error('TMDB_API_KEY is not defined');
    console.log('Searching movies:', query);
    const response = await axios.get(`${TMDB_BASE_URL}/search/movie?api_key=${API_KEY}&query=${encodeURIComponent(query)}`);
    console.log('Movies searched successfully');
    res.json(response.data);
  } catch (error) {
    console.error('Error searching movies:', error.message, error.response ? error.response.data : '');
    res.status(500).json({ error: 'Failed to search movies' });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});