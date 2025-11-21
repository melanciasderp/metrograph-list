# Metrograph List

This project scrapes the [Metrograph](https://metrograph.com/film/) "Now Playing" films and exposes them as a JSON API.

## Use with Radarr

This API is designed to be used as a **Radarr List**. 

1.  Deploy this application (e.g., on Vercel or a local server).
2.  In Radarr, go to **Settings > Lists**.
3.  Add a new **Custom List**.
4.  Set the **List URL** to your deployed URL (e.g., `http://localhost:5000/` or your Vercel URL).
5.  Radarr will now automatically sync movies playing at Metrograph.

## Development

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    export TMDB_API_KEY=<YOUR_API_KEY>
    python api/index.py
    ```
