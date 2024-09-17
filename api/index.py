from flask import Flask, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)

TMDB_API_KEY =  os.getenv("TMDB_API_KEY") # Replace with your actual TMDb API key

def get_tmdb_id(title):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(search_url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]['id']
    return None

@app.route('/')
def get_movies():
    # Scrape movie titles from Metrograph
    url = "https://metrograph.com/film/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    movie_titles = [title.text.strip() for title in soup.select('h3')]

    # Create a list of dictionaries with movie titles and TMDb IDs
    movies = []
    for title in movie_titles:
        tmdb_id = get_tmdb_id(title)
        movie = {
            'title': title,
            'id': tmdb_id,
            'tmdbId': tmdb_id
        }
        movies.append(movie) if tmdb_id else None

    return jsonify(movies)

if __name__ == '__main__':
    app.run(debug=True)
