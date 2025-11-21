import requests
from flask import Flask, jsonify
from bs4 import BeautifulSoup
import os
import sys


import re

def scrape_metrograph_films():
    url = "https://metrograph.com/film/"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Based on inspection: h3.movie_title > a
    # Year is in a following h5, e.g. <h5>1985 / 71min / 4K DCP</h5>
    films = []
    for h3 in soup.select('h3.movie_title'):
        a_tag = h3.find('a')
        if a_tag:
            title = a_tag.get_text(strip=True)
            if title:
                # Find year in siblings
                year = None
                # The h3 is inside a col-sm-6. We need to look at siblings of h3.
                # Structure: h3, div.showtimes, h5 (Director), h5 (Year/...)
                for sibling in h3.find_next_siblings('h5'):
                    text = sibling.get_text(strip=True)
                    # Match 4 digits at start
                    match = re.match(r'^(\d{4})', text)
                    if match:
                        year = match.group(1)
                        break
                
                films.append((title, year))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_films = []
    for title, year in films:
        # Use title as unique key, or title+year? Let's use title for now to match previous logic
        if title not in seen:
            unique_films.append((title, year))
            seen.add(title)
            
    return unique_films

def get_tmdb_data(title, api_key, year=None):
    search_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": title,
        "include_adult": "false"
    }
    if year:
        params['primary_release_year'] = year
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            # Return the first result's ID and Title
            result = data['results'][0]
            return result['id'], result['title']
        else:
            return None, None
    except requests.RequestException as e:
        print(f"Error searching TMDB for '{title}': {e}", file=sys.stderr)
        return None, None


app = Flask(__name__)

# ... (keep existing functions scrape_metrograph_films and get_tmdb_data) ...


@app.route('/')
def index():
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        return jsonify({"error": "TMDB_API_KEY not set"}), 500
        
    films = scrape_metrograph_films()
    results = []
    for title, year in films:
        tmdb_id, tmdb_title = get_tmdb_data(title, api_key, year)
        if tmdb_id:
            results.append({
                "title": tmdb_title,
                "TmdbId": tmdb_id,
                "id": tmdb_id
            })
            
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
