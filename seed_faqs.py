import os
import time
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from google import genai

# Load environment variables (.env must contain DATABASE_URL and GEMINI_API_KEY)
load_dotenv()

# Initialize Gemini Client using your existing setup
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_db_connection():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

def pre_generate_faqs():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch only the rows that DO NOT have FAQs yet
    cursor.execute('''
        SELECT id, tool_a, tool_b 
        FROM integrations 
        WHERE faq_1 IS NULL OR faq_1 = ''
    ''')
    pending_integrations = cursor.fetchall()
    
    total = len(pending_integrations)
    print(f"Found {total} integrations missing FAQs. Starting batch generation...")

    if total == 0:
        print("All FAQs are already generated!")
        return

    # 2. Loop through each one and generate the content
    for index, row in enumerate(pending_integrations, 1):
        integration_id = row['id']
        tool_a = row['tool_a']
        tool_b = row['tool_b']
        
        print(f"[{index}/{total}] Generating FAQs for {tool_a} + {tool_b}...")
        
        try:
            prompt = (
                f"You are an expert SaaS integration analyst in 2026.\n"
                f"Provide direct, helpful answers to the following 6 questions about integrating {tool_a} and {tool_b} via Make.com.\n"
                f"Separate each answer strictly with the delimiter '|||'. Do not include any formatting, headers, or bullet points.\n\n"
                f"Question 1: How do I connect {tool_a} and {tool_b}?\n"
                f"Question 2: Is this integration free?\n"
                f"Question 3: Do I need coding skills?\n"
                f"Question 4: What can I automate between {tool_a} and {tool_b}?\n"
                f"Question 5: What is {tool_a} used for?\n"
                f"Question 6: What is {tool_b} used for?\n"
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            answers = [ans.strip() for ans in response.text.split("|||")]
            
            # Padding in case of formatting errors
            while len(answers) < 6:
                answers.append("Refer to the official technical documentation for detailed usage.")

            # 3. Save directly to your Neon database
            cursor.execute('''
                UPDATE integrations 
                SET faq_1=%s, faq_2=%s, faq_3=%s, faq_4=%s, faq_5=%s, faq_6=%s 
                WHERE id=%s
            ''', (answers[0], answers[1], answers[2], answers[3], answers[4], answers[5], integration_id))
            
            conn.commit()
            print(f"  -> Successfully saved to database.")
            
            # 4. RATE LIMIT PROTECTION
            # Gemini Free Tier allows 15 requests per minute. 
            # 60 seconds / 15 requests = 4 seconds. We wait 5 seconds to be completely safe.
            time.sleep(5)

        except Exception as e:
            print(f"  -> Error on {tool_a} + {tool_b}: {e}")
            print("  -> Waiting 30 seconds before resuming due to potential rate limit hit...")
            time.sleep(30)

    cursor.close()
    conn.close()
    print("Batch FAQ generation complete! Your database is now fully populated.")

if __name__ == "__main__":
    pre_generate_faqs()