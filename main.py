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