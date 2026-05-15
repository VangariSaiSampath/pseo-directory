from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.templating import Jinja2Templates
import sqlite3
import math


app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    conn = sqlite3.connect('pseo_data.db')
    conn.row_factory = sqlite3.Row
    return conn

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
