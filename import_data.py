import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load the secret connection string from your .env file
load_dotenv()

def bulk_import_csv():
    csv_file = 'raw_integrations.csv'
    
    print(f"Reading data from {csv_file}...")
    
    try:
        # 1. Load the CSV into a Pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # 2. Connect to the Neon Postgres database using SQLAlchemy
        db_url = os.environ.get("DATABASE_URL")
        # Ensure the URL starts with 'postgresql://' for SQLAlchemy compatibility
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(db_url)
        
        # 3. Get a list of slugs that already exist in the database
        existing_slugs_df = pd.read_sql('SELECT slug FROM integrations', engine)
        existing_slugs = existing_slugs_df['slug'].tolist()
        
        # 4. Filter the dataframe to ONLY include new rows
        new_data = df[~df['slug'].isin(existing_slugs)]
        
        # 5. Insert the new rows into the cloud!
        if new_data.empty:
            print("No new data to import. All rows in the CSV already exist in the database!")
        else:
            new_data.to_sql('integrations', engine, if_exists='append', index=False)
            print(f"Successfully imported {len(new_data)} NEW records into the Postgres cloud database!")
            
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}. Make sure you ran the scraper first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    bulk_import_csv()