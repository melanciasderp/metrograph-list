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


import vercel_blob
from datetime import datetime, timedelta, timezone
import json

# ... (keep existing functions scrape_metrograph_films and get_tmdb_data) ...

CACHE_FILE = 'metrograph_cache.json'

def update_cache(api_key):
    # Scrape and update cache
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
    
    # Upload to cache
    error = None
    try:
        # vercel_blob.put takes bytes
        vercel_blob.put(CACHE_FILE, json.dumps(results).encode('utf-8'), {'addRandomSuffix': 'false', 'allowOverwrite': 'true'})
    except Exception as e:
        print(f"Cache upload failed: {e}", file=sys.stderr)
        error = str(e)
        
    return results, error

@app.route('/')
def index():
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        return jsonify({"error": "TMDB_API_KEY not set"}), 500
    
    # Check cache
    try:
        blobs = vercel_blob.list({'limit': '1000'}) # List blobs to find cache
        cache_blob = next((b for b in blobs.get('blobs', []) if b['pathname'] == CACHE_FILE), None)
        
        if cache_blob:
            # Check TTL (1 Day)
            uploaded_at_str = cache_blob['uploadedAt']
            if uploaded_at_str.endswith('Z'):
                uploaded_at_str = uploaded_at_str[:-1] + '+00:00'
            
            uploaded_at = datetime.fromisoformat(uploaded_at_str)
            if datetime.now(timezone.utc) - uploaded_at < timedelta(days=1):
                # Cache is valid, download and serve
                cache_resp = requests.get(cache_blob['url'])
                cache_resp.raise_for_status()
                return jsonify(cache_resp.json())
    except Exception as e:
        print(f"Cache check failed: {e}", file=sys.stderr)
        
    # Cache missing or expired, update it
    results, error = update_cache(api_key)
    # We return results even if cache upload failed, but log it (already logged in update_cache)
    return jsonify(results)

@app.route('/cron')
def cron():
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        return jsonify({"error": "TMDB_API_KEY not set"}), 500
        
    results, error = update_cache(api_key)
    if error:
        return jsonify({"error": f"Cache update failed: {error}"}), 500
        
    return jsonify({"status": "success", "message": "Cache updated"})


if __name__ == "__main__":
    app.run(debug=True)
