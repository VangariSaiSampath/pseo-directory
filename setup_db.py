import sqlite3

def setup_database():
    conn = sqlite3.connect('pseo_data.db')
    cursor = conn.cursor()

    # ... [Keep your existing integrations, search_logs, glossary, and leads tables] ...
    
    # NEW: THE BLOG POSTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            slug TEXT UNIQUE,
            content TEXT,
            published_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database upgraded with Blog table!")

if __name__ == "__main__":
    setup_database()