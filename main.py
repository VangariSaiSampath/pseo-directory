import os
import math
import random
import re
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from google import genai
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

# Initialize FastAPI and Templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configure Gemini API
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- DATABASE CONNECTION ---
def get_db_connection():
    # Connect to Neon Postgres Cloud
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    # RealDictCursor returns rows as dictionaries
    return conn, conn.cursor(cursor_factory=RealDictCursor)


# --- 1. The Public Blog Route ---
@app.get("/blog")
async def blog_index(request: Request):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM blog_posts ORDER BY published_date DESC LIMIT 20')
    posts = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("blog.html", {"request": request, "posts": posts})

@app.get("/blog/{slug}")
async def read_blog(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM blog_posts WHERE slug = %s', (slug,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return {"error": "Post not found"}
    return templates.TemplateResponse("blog_post.html", {"request": request, "post": post})


# --- 2. THE AI AGENT ENDPOINT (The Automated Writer) ---
@app.get("/api/agent/daily-blog")
async def run_ai_agent(secret: str):
    # Security check: Only YOU can trigger this
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    conn, cursor = get_db_connection()
    
    # Pick a random integration
    cursor.execute('SELECT tool_a, tool_b FROM integrations')
    integrations = cursor.fetchall()
    
    if not integrations:
        conn.close()
        return {"error": "No integrations found to write about."}
        
    random_pair = random.choice(integrations)
    tool_a, tool_b = random_pair['tool_a'], random_pair['tool_b']

    prompt = f"""
    Act as a senior tech journalist. Write an engaging, highly SEO-optimized blog post about integrating {tool_a} and {tool_b}. 
    Discuss modern business trends, why this specific automation saves hours of manual data entry, and potential creative use cases for 2026.
    
    CRITICAL INSTRUCTIONS:
    - Write 100% original content. Do not copy from other sources.
    - Format the output strictly in HTML (using <h2>, <p>, <ul>, <li>, <strong>).
    - Do not include standard greetings, just the HTML content.
    - Start with an extremely catchy title wrapped in an <h1> tag.
    """
    
    try:
        # Generate the blog using the latest Gemini 2.0 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        html_content = response.text

        title_match = re.search(r'<h1>(.*?)</h1>', html_content)
        title = title_match.group(1) if title_match else f"{tool_a} and {tool_b} Automation Guide"
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        # Save to Postgres
        cursor.execute('''
            INSERT INTO blog_posts (title, slug, content) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (slug) DO NOTHING
        ''', (title, slug, html_content))
        
        conn.commit()
        conn.close()

        return {"status": "Success", "posted": title}

    except Exception as e:
        print(f"Agent Error: {e}")
        return {"status": "Failed", "error": str(e)}


# --- 3. Lead Capture Route ---
@app.post("/request-integration")
async def request_integration(email: str = Form(...), tools: str = Form(...)):
    conn, cursor = get_db_connection()
    cursor.execute('INSERT INTO leads (email, requested_tools) VALUES (%s, %s)', (email, tools))
    conn.commit()
    conn.close()
    return {"message": "Success! We will notify you when this integration is live."}


# --- 4. AI Workflow Generator ---
@app.post("/api/generate-workflow")
async def generate_workflow(industry: str = Form(...), tool_a: str = Form(...), tool_b: str = Form(...)):
    try:
        prompt = f"Act as an automation expert. Give me a 3-step specific, highly practical workflow integrating {tool_a} and {tool_b} for a business in the {industry} industry. Keep it brief and formatted in HTML list tags (<ul><li>)."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return JSONResponse(content={"workflow": response.text})
    except Exception as e:
        print(f"AI Error: {e}") 
        return JSONResponse(content={"workflow": "<p>Error generating workflow. Please try again.</p>"})
    

# --- 5. Main Directory Routes ---
@app.get("/")
async def home(request: Request, q: str = "", page: int = 1):
    conn, cursor = get_db_connection()
    
    if q:
        cursor.execute('INSERT INTO search_logs (query) VALUES (%s)', (q.strip(),))
        conn.commit()

    items_per_page = 15
    offset = (page - 1) * items_per_page

    if q:
        query = f"%{q}%"
        cursor.execute('SELECT COUNT(*) as count FROM integrations WHERE tool_a ILIKE %s OR tool_b ILIKE %s OR description ILIKE %s', (query, query, query))
        total_items = cursor.fetchone()['count']
        
        cursor.execute('SELECT * FROM integrations WHERE tool_a ILIKE %s OR tool_b ILIKE %s OR description ILIKE %s LIMIT %s OFFSET %s', (query, query, query, items_per_page, offset))
        integrations = cursor.fetchall()
    else:
        cursor.execute('SELECT COUNT(*) as count FROM integrations')
        total_items = cursor.fetchone()['count']
        
        cursor.execute('SELECT * FROM integrations LIMIT %s OFFSET %s', (items_per_page, offset))
        integrations = cursor.fetchall()
    
    conn.close()
    
    total_pages = math.ceil(total_items / items_per_page)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "integrations": integrations, 
        "q": q,
        "page": page,
        "total_pages": total_pages
    })

@app.get("/glossary")
async def glossary(request: Request):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM glossary')
    terms = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("glossary.html", {"request": request, "terms": terms})

@app.get("/compare/{tool_a}-vs-{tool_b}")
async def compare(request: Request, tool_a: str, tool_b: str):
    return templates.TemplateResponse("compare.html", {
        "request": request, 
        "tool_a": tool_a.capitalize(), 
        "tool_b": tool_b.capitalize()
    })

@app.get("/best-integrations-for/{tool}")
async def curated_list(request: Request, tool: str):
    conn, cursor = get_db_connection()
    query = f"%{tool}%"
    cursor.execute('SELECT * FROM integrations WHERE tool_a ILIKE %s OR tool_b ILIKE %s LIMIT 10', (query, query))
    integrations = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "integrations": integrations, 
        "q": tool,
        "title": f"Top 10 Best Integrations for {tool.capitalize()}"
    })

@app.get("/integrate/{slug}")
async def integration_page(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM integrations WHERE slug = %s', (slug,))
    integration = cursor.fetchone()
    conn.close()

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    return templates.TemplateResponse("integration.html", {"request": request, "data": integration})

# --- 6. SEO Sitemap Generation ---
@app.get("/sitemap.xml")
async def sitemap():
    conn, cursor = get_db_connection()
    cursor.execute('SELECT slug FROM integrations')
    integrations = cursor.fetchall()
    conn.close()

    base_url = "https://integration-directory.com" 
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    xml += f'  <url>\n    <loc>{base_url}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    
    for item in integrations:
        xml += f'  <url>\n    <loc>{base_url}/integrate/{item["slug"]}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
        
    xml += '</urlset>'
    
    return Response(content=xml, media_type="application/xml")

# --- 7. NEW: Autonomous Tech News Engine ---
@app.get("/news")
async def news_index(request: Request):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM news_posts ORDER BY published_date DESC LIMIT 20')
    posts = cursor.fetchall()
    conn.close()
    # Reusing existing blog layout!
    return templates.TemplateResponse("blog.html", {
        "request": request, 
        "posts": posts, 
        "page_title": "Latest AI & Tech News",
        "page_subtitle": "Breaking news on Artificial Intelligence, LLMs, and the future of work.",
        "post_type": "news"

    })

@app.get("/news/{slug}")
async def read_news(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM news_posts WHERE slug = %s', (slug,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return {"error": "News article not found"}
    return templates.TemplateResponse("blog_post.html", {"request": request, "post": post})

@app.get("/api/agent/daily-news")
async def run_news_agent(secret: str):
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    conn, cursor = get_db_connection()
    
    prompt = """
    Act as a senior tech journalist. Write a highly engaging, SEO-optimized news article about a very recent breakthrough in Artificial Intelligence, Large Language Models, or SaaS automation for 2026. 
    Focus on how these technologies are transforming business workflows and the future of work.
    
    CRITICAL INSTRUCTIONS:
    - Write 100% original content. 
    - Format the output strictly in HTML (using <h2>, <p>, <ul>, <li>, <strong>).
    - Start with an extremely catchy title wrapped in an <h1> tag.
    - Do not include standard greetings.
    """
    
    try:
        # Using gemini-2.5-flash as established for your account
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        html_content = response.text
        
        html_content = html_content.replace("```html", "").replace("```", "").strip()
        
        title_match = re.search(r'<h1>(.*?)</h1>', html_content)

        title_match = re.search(r'<h1>(.*?)</h1>', html_content)
        title = title_match.group(1) if title_match else "Latest AI and Automation News"
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        cursor.execute('''
            INSERT INTO news_posts (title, slug, content) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (slug) DO NOTHING
        ''', (title, slug, html_content))
        
        conn.commit()
        conn.close()

        return {"status": "Success", "posted": title}

    except Exception as e:
        print(f"News Agent Error: {e}")
        return {"status": "Failed", "error": str(e)}
    
    # --- 8. Legal Pages (AdSense Compliance) ---
@app.get("/privacy")
async def privacy_page(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms")
async def terms_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

# --- 9. NEW: AI Social Media Manager ---

@app.get("/api/agent/draft-socials")
async def draft_socials(secret: str):
    """Cron Job Endpoint: Reads the latest news post and drafts social media copy."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    conn, cursor = get_db_connection()
    
    try:
        # Get the most recently published news article
        cursor.execute('SELECT title, slug, content FROM news_posts ORDER BY published_date DESC LIMIT 1')
        latest_post = cursor.fetchone()
        
        if not latest_post:
            return {"status": "Failed", "error": "No news articles found to draft socials for."}

        title = latest_post['title']
        link = f"https://integration-directory.com/news/{latest_post['slug']}"
        snippet = latest_post['content'][:800] # Give the AI the first 800 characters to read

        prompt = f"""
        Act as an expert B2B Social Media Manager. I just published a new article on my tech blog titled: "{title}".
        Here is a snippet of the article: {snippet}
        
        Task 1: Write a highly engaging, professional LinkedIn post summarizing the value of this article. Use bullet points and professional hashtags.
        Task 2: Write a punchy, viral Twitter (X) post under 280 characters.
        
        CRITICAL: 
        - You MUST include this exact link at the end of both posts: {link}
        - Format your response exactly like this:
        [LINKEDIN]
        (The linkedin post here)
        [TWITTER]
        (The twitter post here)
        """
        
        # Call Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_response = response.text
        
        # Parse the AI response into LinkedIn and Twitter variables
        linkedin_part = ai_response.split('[TWITTER]')[0].replace('[LINKEDIN]', '').strip()
        twitter_part = ai_response.split('[TWITTER]')[1].strip() if '[TWITTER]' in ai_response else "Twitter draft failed."

        # Save the drafts to the database
        cursor.execute('''
            INSERT INTO social_drafts (article_title, linkedin_post, twitter_post) 
            VALUES (%s, %s, %s)
        ''', (title, linkedin_part, twitter_part))
        
        conn.commit()
        return {"status": "Success", "message": f"Social drafts created for: {title}"}

    except Exception as e:
        print(f"Social Agent Error: {e}")
        return {"status": "Failed", "error": str(e)}
    finally:
        conn.close()

@app.get("/social-dashboard")
async def view_social_drafts(request: Request, secret: str = None):
    """A private page for you to copy your AI-generated social posts."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized. Please provide your secret in the URL."}

    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM social_drafts ORDER BY created_at DESC LIMIT 10')
    drafts = cursor.fetchall()
    conn.close()
    
    # We will build a simple HTML string right here so you don't even need a new template file!
    html_content = """
    <html><body style="font-family: sans-serif; padding: 40px; background: #f4f4f5;">
    <h1 style="color: #18181b;">🤖 Your AI Social Media Dashboard</h1>
    <p>Copy and paste these drafts to your social accounts to drive traffic.</p>
    """
    for draft in drafts:
        html_content += f"""
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="margin-top:0; color: #2563eb;">Article: {draft['article_title']}</h2>
            <h3 style="color: #0077b5;">LinkedIn Draft</h3>
            <textarea style="width: 100%; height: 150px; padding: 10px;">{draft['linkedin_post']}</textarea>
            <h3 style="color: #0f1419;">Twitter Draft</h3>
            <textarea style="width: 100%; height: 80px; padding: 10px;">{draft['twitter_post']}</textarea>
        </div>
        """
    html_content += "</body></html>"
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)