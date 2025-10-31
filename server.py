from flask import Flask, request, jsonify, send_from_directory, Response
from waitress import serve
import os
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from queue import Queue
import threading
import json

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

# Server-Sent Events (SSE) clients storage
sse_clients = []
sse_lock = threading.Lock()

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

# Server-Sent Events endpoint for streaming events to remote.html
@app.route('/events', methods=['GET'])
def events_stream():
    """SSE endpoint that streams events to connected clients"""
    def generate():
        client_queue = Queue()
        
        # Add this client to the list
        with sse_lock:
            sse_clients.append(client_queue)
        
        try:
            # Keep the connection alive and send any queued events
            while True:
                try:
                    event_data = client_queue.get(timeout=30)  # 30-second timeout
                    yield f"data: {event_data}\n\n"
                except Exception:
                    # Send a comment to keep connection alive
                    yield ": keep-alive\n\n"
        finally:
            # Remove this client when connection closes
            with sse_lock:
                if client_queue in sse_clients:
                    sse_clients.remove(client_queue)
    
    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })

# Broadcast event to all connected SSE clients
def broadcast_event(event_type, command):
    """Send an event to all connected clients"""
    event_data = json.dumps({"type": event_type, "command": command})
    
    with sse_lock:
        for client_queue in sse_clients:
            try:
                client_queue.put(event_data, block=False)
            except Exception:
                # Client queue is full, skip this client
                pass

# Play endpoint
@app.route('/play', methods=['POST'])
@limiter.limit("60 per minute")
def play():
    """Send play command via SSE"""
    broadcast_event('control', 'play')
    return jsonify({'status': 'success', 'message': 'Play command sent'}), 200

# Pause endpoint
@app.route('/pause', methods=['POST'])
@limiter.limit("60 per minute")
def pause():
    """Send pause command via SSE"""
    broadcast_event('control', 'pause')
    return jsonify({'status': 'success', 'message': 'Pause command sent'}), 200

# Toggle endpoint (play/pause)
@app.route('/toggle', methods=['POST'])
@limiter.limit("60 per minute")
def toggle():
    """Send toggle (play/pause) command via SSE"""
    broadcast_event('control', 'toggle')
    return jsonify({'status': 'success', 'message': 'Toggle command sent'}), 200

# Serve static files (e.g., remote.html)
@app.route('/', defaults={'path': 'remote.html'})
@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"Server running on http://localhost:{port}")
    serve(app, host='0.0.0.0', port=port)
