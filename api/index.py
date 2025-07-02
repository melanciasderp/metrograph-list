from flask import Flask, jsonify
import requests, os, re
from bs4 import BeautifulSoup

app = Flask(__name__)

TMDB_API_KEY =  os.getenv("TMDB_API_KEY") # Replace with your actual TMDb API key
pattern=r"\b\d{4}\b" # match release date from website

def get_tmdb_id(title, date=""):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    if date != "":
        search_url+=f"&year={date}"
    response = requests.get(search_url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
             if results[0]['title'] == title:
                 return results[0]
    return {}

@app.route('/')
def get_movie_details():
    # Scrape movie titles from Metrograph
    url = "https://metrograph.com/film/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    movie_banners = soup.find_all("div",{"class":"col-sm-12"})

    movies = []

    for movie_details in movie_banners:
        try:
            movie_name = movie_details.select("h3")[0].text.strip()
            details = [a.text.strip() for a in movie_details.select("h5")]
            date=""

            for text in details:
                date_match = re.search(pattern,text)
                if date_match:
                    date = date_match.group(0)

            tmdb = get_tmdb_id(movie_name,date)
            tmdb_id = tmdb.get('id',None)
            movie = {
                'title': movie_name,
                'TmdbId': tmdb_id,
                'id': tmdb_id,
            }
            movies.append(movie) if tmdb_id else None
        except IndexError:
            pass

    return jsonify(movies)

if __name__ == '__main__':
    app.run(debug=True)
