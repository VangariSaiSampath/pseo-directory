import os

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.templating import Jinja2Templates
import sqlite3
import math
from fastapi import Form
from fastapi.responses import JSONResponse
from google import genai
import os
from dotenv import load_dotenv
import random
import re
from datetime import datetime


app = FastAPI()
templates = Jinja2Templates(directory="templates")


# --- 1. The Public Blog Route ---
@app.get("/blog")
async def blog_index(request: Request):
    conn = get_db_connection()
    # Get the latest 20 blog posts
    posts = conn.execute('SELECT * FROM blog_posts ORDER BY published_date DESC LIMIT 20').fetchall()
    conn.close()
    return templates.TemplateResponse("blog.html", {"request": request, "posts": posts})

@app.get("/blog/{slug}")
async def read_blog(request: Request, slug: str):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM blog_posts WHERE slug = ?', (slug,)).fetchone()
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

    conn = get_db_connection()
    
    # 1. Pick a random integration from your database to write about
    integrations = conn.execute('SELECT tool_a, tool_b FROM integrations').fetchall()
    if not integrations:
        return {"error": "No integrations found to write about."}
    random_pair = random.choice(integrations)
    tool_a, tool_b = random_pair['tool_a'], random_pair['tool_b']

    # 2. Prompt Gemini to act as a Tech Journalist (Ensures zero plagiarism)
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
        # Generate the blog using Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        html_content = response.text

        # 3. Extract the Title to create a URL Slug
        title_match = re.search(r'<h1>(.*?)</h1>', html_content)
        title = title_match.group(1) if title_match else f"{tool_a} and {tool_b} Automation Guide"
        
        # Create a URL-friendly slug (e.g., "slack-and-notion-automation-guide")
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        # 4. Save to Database
        conn.execute('INSERT OR IGNORE INTO blog_posts (title, slug, content) VALUES (?, ?, ?)', 
                    (title, slug, html_content))
        conn.commit()
        conn.close()

        return {"status": "Success", "posted": title}

    except Exception as e:
        print(f"Agent Error: {e}")
        return {"status": "Failed", "error": str(e)}

def get_db_connection():
    conn = sqlite3.connect('pseo_data.db')
    conn.row_factory = sqlite3.Row
    return conn
load_dotenv()
# Configure Gemini API (You will add this key in Render later)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
model = "gemini-1.5-flash"

# --- NEW FEATURE 1: Lead Capture Route ---
@app.post("/request-integration")
async def request_integration(email: str = Form(...), tools: str = Form(...)):
    conn = get_db_connection()
    conn.execute('INSERT INTO leads (email, requested_tools) VALUES (?, ?)', (email, tools))
    conn.commit()
    conn.close()
    # Redirect back to home with a success message (simplified for this example)
    return {"message": "Success! We will notify you when this integration is live."}

# --- NEW FEATURE 2: AI Workflow Generator ---
@app.post("/api/generate-workflow")
async def generate_workflow(industry: str = Form(...), tool_a: str = Form(...), tool_b: str = Form(...)):
    try:
        prompt = f"Act as an automation expert. Give me a 3-step specific, highly practical workflow integrating {tool_a} and {tool_b} for a business in the {industry} industry. Keep it brief and formatted in HTML list tags (<ul><li>)."
        
        # NEW: Generating content with the updated genai syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return JSONResponse(content={"workflow": response.text})
    except Exception as e:
        print(f"AI Error: {e}") # This will log the error in your terminal if it fails
        return JSONResponse(content={"workflow": "<p>Error generating workflow. Please try again.</p>"})
    
@app.get("/")
async def home(request: Request, q: str = "", page: int = 1):
    conn = get_db_connection()
    if q:
        # Save what the user searched for into our new table
        conn.execute('INSERT INTO search_logs (query) VALUES (?)', (q.strip(),))
        conn.commit() # We must commit because we are writing data

    items_per_page = 15
    offset = (page - 1) * items_per_page

    if q:
        query = f"%{q}%"
        # Get total count for math
        total_items = conn.execute('SELECT COUNT(*) FROM integrations WHERE tool_a LIKE ? OR tool_b LIKE ? OR description LIKE ?', (query, query, query)).fetchone()[0]
        # Get the actual items for this page
        integrations = conn.execute('SELECT * FROM integrations WHERE tool_a LIKE ? OR tool_b LIKE ? OR description LIKE ? LIMIT ? OFFSET ?', (query, query, query, items_per_page, offset)).fetchall()
    else:
        total_items = conn.execute('SELECT COUNT(*) FROM integrations').fetchone()[0]
        integrations = conn.execute('SELECT * FROM integrations LIMIT ? OFFSET ?', (items_per_page, offset)).fetchall()
    
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
    conn = get_db_connection()
    terms = conn.execute('SELECT * FROM glossary').fetchall()
    conn.close()
    return templates.TemplateResponse("glossary.html", {"request": request, "terms": terms})

@app.get("/compare/{tool_a}-vs-{tool_b}")
async def compare(request: Request, tool_a: str, tool_b: str):
    # This generates a programmatic comparison page
    return templates.TemplateResponse("compare.html", {
        "request": request, 
        "tool_a": tool_a.capitalize(), 
        "tool_b": tool_b.capitalize()
    })

@app.get("/best-integrations-for/{tool}")
async def curated_list(request: Request, tool: str):
    conn = get_db_connection()
    query = f"%{tool}%"
    integrations = conn.execute('SELECT * FROM integrations WHERE tool_a LIKE ? OR tool_b LIKE ? LIMIT 10', (query, query)).fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "integrations": integrations, 
        "q": tool,
        "title": f"Top 10 Best Integrations for {tool.capitalize()}"
    })

@app.get("/integrate/{slug}")
async def integration_page(request: Request, slug: str):
    conn = get_db_connection()
    integration = conn.execute('SELECT * FROM integrations WHERE slug = ?', (slug,)).fetchone()
    conn.close()

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    return templates.TemplateResponse("integration.html", {"request": request, "data": integration})

# --- NEW: SEO Sitemap Generation ---
@app.get("/sitemap.xml")
async def sitemap():
    conn = get_db_connection()
    integrations = conn.execute('SELECT slug FROM integrations').fetchall()
    conn.close()

    # Change this to your actual domain before deployment
    base_url = "https://integration-directory.onrender.com" 
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Homepage priority
    xml += f'  <url>\n    <loc>{base_url}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    
    # Dynamic Pages
    for item in integrations:
        xml += f'  <url>\n    <loc>{base_url}/integrate/{item["slug"]}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
        
    xml += '</urlset>'
    
    return Response(content=xml, media_type="application/xml")
