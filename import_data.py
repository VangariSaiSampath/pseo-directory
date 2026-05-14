import pandas as pd
import sqlite3

def bulk_import_csv():
    csv_file = 'raw_integrations.csv'
    db_file = 'pseo_data.db'
    
    print(f"Reading data from {csv_file}...")
    
    try:
        # 1. Load the CSV into a Pandas DataFrame
        df = pd.read_csv(csv_file)
        
        # 2. Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        
        # 3. Get a list of slugs that already exist in the database
        existing_slugs_df = pd.read_sql('SELECT slug FROM integrations', conn)
        existing_slugs = existing_slugs_df['slug'].tolist()
        
        # 4. Filter the dataframe to ONLY include new rows
        new_data = df[~df['slug'].isin(existing_slugs)]
        
        # 5. Insert the new rows
        if new_data.empty:
            print("No new data to import. All rows in the CSV already exist in the database!")
        else:
            new_data.to_sql('integrations', conn, if_exists='append', index=False)
            print(f"Successfully imported {len(new_data)} NEW records into the database!")
            
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}. Make sure you ran the scraper first.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    bulk_import_csv()