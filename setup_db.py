import sqlite3

def setup_database():
    conn = sqlite3.connect('pseo_data.db')
    cursor = conn.cursor()

    # 1. THE MAIN INTEGRATIONS TABLE (With all columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            tool_a TEXT,
            tool_b TEXT,
            description TEXT,
            search_volume INTEGER,
            affiliate_link TEXT,
            recipe TEXT
        )
    ''')

    # 2. THE SEARCH LOGS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. THE GLOSSARY TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            definition TEXT
        )
    ''')

    # 4. INSERT GLOSSARY DUMMY DATA
    terms = [
        ("API", "Application Programming Interface - the 'bridge' that allows two apps to talk."),
        ("Webhook", "A way for an app to send real-time info to another app as soon as an event happens."),
        ("Trigger", "The event that starts an automation (e.g., 'New Email Received')."),
        ("Action", "The task that happens automatically (e.g., 'Save to Spreadsheet').")
    ]
    cursor.executemany('INSERT OR IGNORE INTO glossary (term, definition) VALUES (?, ?)', terms)
    # 5. THE LEADS TABLE (For user integration requests)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            requested_tools TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Master Database Setup Complete! All tables and columns are ready.")

if __name__ == "__main__":
    setup_database()