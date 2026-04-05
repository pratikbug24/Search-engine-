from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from serpapi import GoogleSearch
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "supersecretkey"

# ================== 🔐 DATABASE ==================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ================== 🔐 GOOGLE LOGIN ==================
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ================== 🏠 HOME ==================
@app.route('/')
def home():
    user = session.get('user')
    if not user:
        return redirect('/login')
    return render_template('index.html', user=user)

# ================== 🔑 LOGIN ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = {
                "name": user[1],
                "email": "manual@login.com",
                "picture": "https://via.placeholder.com/40"
            }
            return redirect('/')
        else:
            return "Invalid username or password ❌"

    return render_template('login.html')

# ================== 📝 SIGNUP ==================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            conn.close()
            return "User already exists ❌"

    return render_template('signup.html')

# ================== 🔵 GOOGLE LOGIN ==================
@app.route('/login/google')
def login_google():
    return google.authorize_redirect(url_for('callback', _external=True))

# ================== 🔁 CALLBACK ==================
@app.route('/callback')
def callback():
    token = google.authorize_access_token()

    # ✅ FIX: use full URL
    resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
    user_info = resp.json()

    session['user'] = user_info
    return redirect('/')

# ================== 👤 PROFILE ==================
@app.route('/profile')
def profile():
    user = session.get('user')
    if not user:
        return redirect('/login')
    return render_template('profile.html', user=user)

# ================== 🚪 LOGOUT ==================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ================== 🔍 SEARCH API ==================
API_KEY = os.getenv("SERP_API_KEY")

@app.route('/api/search')
def search():
    query = request.args.get('q')
    search_type = request.args.get('type', 'all')

    params = {
        "q": query,
        "api_key": API_KEY
    }

    if search_type == "videos":
        params["engine"] = "google_videos"
    elif search_type == "images":
        params["engine"] = "google_images"
    else:
        params["engine"] = "google"

    search = GoogleSearch(params)
    results = search.get_dict()

    output = []

    if search_type == "images":
        for item in results.get("images_results", []):
            output.append({
                "image": item.get("original", ""),
                "title": item.get("title", ""),
                "url": item.get("link", "")
            })

    elif search_type == "videos":
        for item in results.get("video_results", []):
            output.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", ""),
                "thumbnail": item.get("thumbnail", "")
            })

    else:
        for item in results.get("organic_results", []):
            output.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "content": item.get("snippet", "")
            })

    return jsonify(output)

# ================== 💡 SUGGESTIONS ==================
@app.route('/api/suggest')
def suggest():
    query = request.args.get('q')

    suggestions = [
        query + " tutorial",
        query + " example",
        query + " latest",
        query + " interview questions",
        query + " project ideas"
    ]

    return jsonify(suggestions)

# ================== 🚀 RUN ==================
if __name__ == '__main__':
    app.run(debug=True)