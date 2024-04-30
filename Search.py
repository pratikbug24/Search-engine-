import requests
from bs4 import BeautifulSoup
import sqlite3

# Level 1: Introduction to HTML and CSS
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Search Engine Explorer</title>
    <style>
        /* CSS styles */
        body {
            font-family: Arial, sans-serif;
        }
        #search-container {
            text-align: center;
            margin-top: 50px;
        }
        input[type="text"] {
            padding: 10px;
            width: 300px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 16px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            border-radius: 5px;
            background-color: #007bff;
            color: #fff;
            border: none;
            cursor: pointer;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div id="search-container">
        <h1>Welcome to Search Engine Explorer</h1>
        <form action="search_results.html" method="get">
            <input type="text" name="query" placeholder="Enter your search query">
            <input type="submit" value="Search">
        </form>
    </div>
</body>
</html>
"""

# Level 2: Understanding Web Crawling
url = 'https://example.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a')
for link in links:
    print(link.get('href'))

# Level 3: Basic Database Management
conn = sqlite3.connect('search_engine.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS web_data
             (url TEXT, title TEXT, content TEXT)''')
c.execute("INSERT INTO web_data VALUES ('https://example.com', 'Example', 'This is an example website')")
conn.commit()
conn.close()

# Level 4: Implementing Search Algorithms
def search(query, data):
    results = []
    for item in data:
        if query.lower() in item['content'].lower():
            results.append(item)
    return results

# Example usage
data = [{'url': 'https://example.com', 'title': 'Example', 'content': 'This is an example website'}]
query = 'example'
print(search(query, data))
