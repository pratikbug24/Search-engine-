from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from serpapi import GoogleSearch
import sqlite3
import requests
import os
from dotenv import load_dotenv
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    raise ValueError("❌ HF_API_KEY not found in .env")


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

# ================== ✏️ EDIT PROFILE ==================
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    user = session.get('user')
    if not user:
        return redirect('/login')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        # Update user session
        user['name'] = name
        user['email'] = email
        session['user'] = user
        
        # Update in database if it's a manual login
        if 'manual@login.com' in user.get('email', ''):
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("UPDATE users SET username=? WHERE username=?", (name, user.get('original_name', name)))
            conn.commit()
            conn.close()
        
        return redirect('/profile')
    
    user['original_name'] = user.get('name')
    return render_template('edit_profile.html', user=user)

# ================== ⚙️ SETTINGS ==================
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user = session.get('user')
    if not user:
        return redirect('/login')
    
    if request.method == 'POST':
        # Save settings to session/localStorage
        session['settings'] = {
            'theme': request.form.get('theme', 'light'),
            'search_suggestions': request.form.get('search_suggestions', 'on'),
            'search_history': request.form.get('search_history', 'on'),
            'auto_correct': request.form.get('auto_correct', 'on'),
            'safe_search': request.form.get('safe_search', 'on'),
            'language': request.form.get('language', 'en'),
        }
        return redirect('/settings')
    
    user_settings = session.get('settings', {
        'theme': 'light',
        'search_suggestions': 'on',
        'search_history': 'on',
        'auto_correct': 'on',
        'safe_search': 'on',
        'language': 'en'
    })
    return render_template('settings.html', user=user, settings=user_settings)

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


@app.route('/api/ai-summary')
def ai_summary():
    query = request.args.get('q')

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-large",
            headers={
                "Authorization": f"Bearer {HF_API_KEY}"
            },
            json={
                "inputs": f"Answer this clearly in 2 lines: {query}",
                "options": {"wait_for_model": True}
            }
        )

        data = response.json()   # ✅ IMPORTANT

        # ✅ Success case
        if isinstance(data, list):
            return jsonify({"answer": data[0].get("generated_text", "")})

        # ✅ Error case
        if isinstance(data, dict) and "error" in data:
            return jsonify({"answer": "⚠️ AI not available right now"})

        return jsonify({"answer": "No response from AI"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"answer": "AI service error"})
    
    # ================== ⭐ FAVORITES ==================

def init_favorites_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_favorites_db()


# ➕ Add to favorites
@app.route('/api/favorite', methods=['POST'])
def add_favorite():
    user = session.get('user')
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    title = data.get("title")
    url = data.get("url")

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO favorites (username, title, url) VALUES (?, ?, ?)",
        (user['name'], title, url)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Added to favorites"})


# 📄 Get favorites
@app.route('/api/favorites')
def get_favorites():
    user = session.get('user')
    if not user:
        return jsonify([])

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, title, url FROM favorites WHERE username=?", (user['name'],))
    data = c.fetchall()
    conn.close()

    favorites = [
        {"id": row[0], "title": row[1], "url": row[2]}
        for row in data
    ]

    return jsonify(favorites)


# ❌ Delete favorite
@app.route('/api/favorite/<int:id>', methods=['DELETE'])
def delete_favorite(id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted"})

@app.route('/api/favorites/count')
def favorites_count():
    user = session.get('user')
    if not user:
        return jsonify({"count": 0})

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM favorites WHERE username=?", (user['name'],))
    count = c.fetchone()[0]

    conn.close()


    return jsonify({"count": count})

@app.route('/api/search/count')
def search_count():
    user = session.get('user')
    if not user:
        return jsonify({"count": 0})

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM searches WHERE username=?", (user['name'],))
    count = c.fetchone()[0]

    conn.close()

    return jsonify({"count": count})
# ================== 🚀 RUN ==================
if __name__ == '__main__':
    app.run(debug=True)