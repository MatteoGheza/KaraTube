from flask import Flask, request, jsonify, send_from_directory
from waitress import serve
import os
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Load environment variables from .env file
load_dotenv()
apiKey = os.getenv("YOUTUBE_API_KEY")

# Initialize Flask app
app = Flask(__name__, static_folder='.')

# Configure caching with a 1-week timeout
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 604800})  # 604800 seconds = 1 week

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"],  # Default rate limit: 10 requests per minute
    storage_uri="memory://"
)

# Proxy endpoint for YouTube API with caching and rate limiting
@app.route('/search_video', methods=['GET'])
@limiter.limit("30 per minute")  # Limit this endpoint to 30 requests per minute
def proxy_youtube_api():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    # Check if the result is already cached
    cached_response = cache.get(query)
    if cached_response:
        return jsonify(cached_response), 200

    # If not cached, make the request to the YouTube API
    youtube_api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={apiKey}"
    response = requests.get(youtube_api_url)

    if response.status_code == 200:
        # Cache the response
        cache.set(query, response.json())

    return jsonify(response.json()), response.status_code

# Serve static files (e.g., remote.html)
@app.route('/', defaults={'path': 'remote.html'})
@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"Server running on http://localhost:{port}")
    serve(app, host='0.0.0.0', port=port)
