import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    # Connect to the new Cloud Database
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cursor = conn.cursor()

    # 1. Integrations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS integrations (
            id SERIAL PRIMARY KEY,
            slug TEXT UNIQUE,
            tool_a TEXT,
            tool_b TEXT,
            description TEXT,
            search_volume INTEGER,
            affiliate_link TEXT,
            recipe TEXT
        )
    ''')

    # 2. Leads Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            email TEXT,
            requested_tools TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Blog Posts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id SERIAL PRIMARY KEY,
            title TEXT,
            slug TEXT UNIQUE,
            content TEXT,
            published_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Glossary Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS glossary (
            id SERIAL PRIMARY KEY,
            term TEXT UNIQUE,
            definition TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Successfully connected and built tables in Neon Cloud Postgres!")

if __name__ == "__main__":
    setup_database()