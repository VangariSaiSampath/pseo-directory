import sqlite3

def setup_database():
    conn = sqlite3.connect('pseo_data.db')
    cursor = conn.cursor()

    # Your existing integrations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            tool_a TEXT,
            tool_b TEXT,
            description TEXT,
            search_volume INTEGER,
            affiliate_link TEXT
        )
    ''')

    # --- NEW: SEARCH LOGS TABLE ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database and search logs table ready!")

if __name__ == "__main__":
    setup_database()