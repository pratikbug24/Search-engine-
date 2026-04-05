from flask import Flask, request, jsonify, render_template
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# 🔒 Secure API Key
API_KEY = os.getenv("SERP_API_KEY")
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/search')
def search():
    query = request.args.get('q')
    search_type = request.args.get('type', 'all')

    params = {
        "q": query,
        "api_key": API_KEY
    }

    # 🔥 Correct engines
    if search_type == "videos":
        params["engine"] = "google_videos"   # ✅ FIXED
    elif search_type == "images":
        params["engine"] = "google_images"
    else:
        params["engine"] = "google"

    search = GoogleSearch(params)
    results = search.get_dict()

    output = []

    # 🖼️ Images
    if search_type == "images":
        for item in results.get("images_results", []):
            output.append({
                "image": item.get("original", ""),
                "title": item.get("title", ""),
                "url": item.get("link", "")
            })

    # 🎥 Videos (FIXED)
    elif search_type == "videos":
        for item in results.get("video_results", []):
            output.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", ""),
                "thumbnail": item.get("thumbnail", "")
            })

    # 🔍 Normal search
    else:
        for item in results.get("organic_results", []):
            output.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", "")
            })

    return jsonify(output)


@app.route('/api/suggest')
def suggest():
    query = request.args.get('q')
    
    # simple suggestions (can upgrade later)
    suggestions = [
        query + " tutorial",
        query + " example",
        query + " latest",
        query + " interview questions",
        query + " project ideas"
    ]

    return jsonify(suggestions)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)