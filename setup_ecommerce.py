import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_deals():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        
        # 1. Create the table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecommerce_deals (
            id SERIAL PRIMARY KEY,
            platform VARCHAR(50),
            product_name VARCHAR(255),
            affiliate_link TEXT,
            color_theme VARCHAR(50)
        );
        """)
        
        # 2. Clear old test data (if you run this multiple times)
        cursor.execute("TRUNCATE TABLE ecommerce_deals;")
        
        # 3. Insert your first 3 real products! (Replace the URLs with your actual affiliate links)
        deals = [
            ("Amazon", "Logitech MX Master 3S", "https://amazon.com/your-link", "yellow-400"),
            ("Flipkart", "Dell 27-inch 4K Monitor", "https://flipkart.com/your-link", "blue-500"),
            ("Meesho", "Ergonomic Laptop Stand", "https://meesho.com/your-link", "pink-500")
        ]
        
        for deal in deals:
            cursor.execute("INSERT INTO ecommerce_deals (platform, product_name, affiliate_link, color_theme) VALUES (%s, %s, %s, %s)", deal)
            
        conn.commit()
        print("Success! E-commerce table created and seeded with deals.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_deals()