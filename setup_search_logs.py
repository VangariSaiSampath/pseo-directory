import os
import psycopg2
from dotenv import load_dotenv

# Load your Neon database URL
load_dotenv()

def create_table():
    try:
        # Connect to your Neon Postgres database
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # The SQL command to create the search_logs table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS search_logs (
            id SERIAL PRIMARY KEY,
            query VARCHAR(255) NOT NULL,
            search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Execute the command and save the changes
        cursor.execute(create_table_query)
        conn.commit()
        
        print("Success! The search_logs table has been created in your Neon Cloud Database.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_table()