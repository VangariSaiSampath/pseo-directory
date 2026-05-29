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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks

from fastapi.responses import RedirectResponse

import feedparser
import httpx


# Load environment variables
load_dotenv()

MAKE_AFFILIATE = "https://www.make.com/en/register?pc=sampath9"
 
TOOL_LINKS = {
    # Automation tools - use your affiliate for Make.com, direct links for others
    "make.com":      {"url": MAKE_AFFILIATE,                              "label": "Try Make.com free →",    "badge": "Your Affiliate"},
    "make":          {"url": MAKE_AFFILIATE,                              "label": "Try Make.com free →",    "badge": "Your Affiliate"},
    "zapier":        {"url": "https://zapier.com/sign-up",                "label": "Try Zapier free →",      "badge": "Free plan"},
    "n8n":           {"url": "https://n8n.io/",                           "label": "Try n8n free →",         "badge": "Open source"},
    "activepieces":  {"url": "https://www.activepieces.com/",             "label": "Try Activepieces →",     "badge": "Free"},
    # CRM / Sales
    "hubspot":       {"url": "https://www.hubspot.com/products/crm",      "label": "Try HubSpot free CRM →", "badge": "Free forever"},
    "salesforce":    {"url": "https://www.salesforce.com/form/signup/",   "label": "Try Salesforce →",       "badge": "30-day trial"},
    "pipedrive":     {"url": "https://www.pipedrive.com/",                "label": "Try Pipedrive →",        "badge": "14-day trial"},
    "zoho":          {"url": "https://www.zoho.com/crm/",                 "label": "Try Zoho CRM →",         "badge": "Free plan"},
    # Project management
    "notion":        {"url": "https://www.notion.so/signup",              "label": "Try Notion free →",      "badge": "Free plan"},
    "trello":        {"url": "https://trello.com/signup",                 "label": "Try Trello free →",      "badge": "Free forever"},
    "asana":         {"url": "https://asana.com/create-account",          "label": "Try Asana free →",       "badge": "Free plan"},
    "monday.com":    {"url": "https://monday.com/lang/en/",               "label": "Try Monday.com →",       "badge": "Free trial"},
    "airtable":      {"url": "https://airtable.com/signup",               "label": "Try Airtable free →",    "badge": "Free plan"},
    "clickup":       {"url": "https://clickup.com/",                      "label": "Try ClickUp free →",     "badge": "Free forever"},
    "jira":          {"url": "https://www.atlassian.com/software/jira",   "label": "Try Jira free →",        "badge": "Free for 10 users"},
    # Communication
    "slack":         {"url": "https://slack.com/get-started",             "label": "Try Slack free →",       "badge": "Free plan"},
    "zoom":          {"url": "https://zoom.us/freesignup/",               "label": "Try Zoom free →",        "badge": "Free plan"},
    "teams":         {"url": "https://www.microsoft.com/en/microsoft-teams/", "label": "Try Teams free →",   "badge": "Free plan"},
    "discord":       {"url": "https://discord.com/register",              "label": "Join Discord →",         "badge": "Free"},
    # Marketing
    "mailchimp":     {"url": "https://mailchimp.com/",                    "label": "Try Mailchimp free →",   "badge": "Free plan"},
    "mailerlite":    {"url": "https://www.mailerlite.com/",               "label": "Try MailerLite free →",  "badge": "Free plan"},
    "activecampaign":{"url": "https://www.activecampaign.com/",           "label": "Try ActiveCampaign →",   "badge": "14-day trial"},
    # E-commerce
    "shopify":       {"url": "https://www.shopify.com/",                  "label": "Try Shopify →",          "badge": "3-day free trial"},
    "woocommerce":   {"url": "https://woocommerce.com/",                  "label": "Try WooCommerce →",      "badge": "Free plugin"},
    "stripe":        {"url": "https://dashboard.stripe.com/register",     "label": "Try Stripe →",           "badge": "No monthly fee"},
    # Support
    "zendesk":       {"url": "https://www.zendesk.com/register/",         "label": "Try Zendesk →",          "badge": "Free trial"},
    "intercom":      {"url": "https://www.intercom.com/",                 "label": "Try Intercom →",         "badge": "14-day trial"},
    "freshdesk":     {"url": "https://freshdesk.com/",                    "label": "Try Freshdesk free →",   "badge": "Free plan"},
    # Storage / Productivity
    "google sheets": {"url": "https://workspace.google.com/",             "label": "Try Google Workspace →", "badge": "Free personal"},
    "google drive":  {"url": "https://workspace.google.com/",             "label": "Try Google Workspace →", "badge": "Free"},
    "dropbox":       {"url": "https://www.dropbox.com/register",          "label": "Try Dropbox free →",     "badge": "Free 2GB"},
    "onedrive":      {"url": "https://www.microsoft.com/en-us/microsoft-365/", "label": "Try Microsoft 365 →", "badge": "Free trial"},
    # Dev tools
    "github":        {"url": "https://github.com/signup",                 "label": "Try GitHub free →",      "badge": "Free forever"},
    "gitlab":        {"url": "https://gitlab.com/users/sign_up",          "label": "Try GitLab free →",      "badge": "Free plan"},
    "linear":        {"url": "https://linear.app/",                       "label": "Try Linear free →",      "badge": "Free plan"},
    # Analytics
    "google analytics":{"url": "https://analytics.google.com/",           "label": "Try Google Analytics →", "badge": "Free"},
    "mixpanel":      {"url": "https://mixpanel.com/register/",            "label": "Try Mixpanel free →",    "badge": "Free plan"},
}
 
def get_tool_link(tool_name: str) -> dict:
    """Helper: returns link info for a tool, falls back to Make.com for unknown tools."""
    key = tool_name.lower().strip()
    return TOOL_LINKS.get(key, {
        "url": MAKE_AFFILIATE,
        "label": f"Automate {tool_name} with Make.com →",
        "badge": "Free trial"
    })
 

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

# --- EMAIL AUTOMATION ENGINE ---
def send_newsletter(subject: str, content: str):
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    
    if not sender_email or not sender_password:
        print("SMTP credentials missing. Emails will not be sent.")
        return

    conn, cursor = get_db_connection()
    cursor.execute("SELECT email FROM newsletter_subscribers")
    subscribers = cursor.fetchall()
    conn.close()

    if not subscribers:
        return

    try:
        # Connect to Gmail's secure server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        for sub in subscribers:
            msg = MIMEMultipart()
            msg['From'] = f"Integration Directory <{sender_email}>"
            msg['To'] = sub['email']
            msg['Subject'] = f"New: {subject}"
            
            # Wrap the AI's HTML in a nice email layout
            email_body = f"""
            <html><body style="font-family: sans-serif; color: #333; line-height: 1.6;">
            <div style="max-w: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Hey Techie,</h2>
                <p>We just published a new breakdown on the Integration Directory. Here is your exclusive look:</p>
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                {content}
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                <p><a href="https://integration-directory.com" style="color: #2563eb; font-weight: bold;">View more on the website &rarr;</a></p>
            </div>
            </body></html>
            """
            msg.attach(MIMEText(email_body, 'html'))
            server.send_message(msg)
        
        server.quit()
        print(f"Success! Emailed {len(subscribers)} subscribers.")
    except Exception as e:
        print(f"Email failed: {e}")


# --- 1. The Public Blog Route ---
@app.get("/blog")
async def blog_index(request: Request, page: int = 1):
    conn, cursor = get_db_connection()
    per_page = 15
    offset = (page - 1) * per_page
    
    # Count total posts for pagination
    cursor.execute('SELECT COUNT(*) as count FROM blog_posts')
    total_items = cursor.fetchone()['count']
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    
    # Fetch just the 15 posts for the current page
    cursor.execute('SELECT * FROM blog_posts ORDER BY published_date DESC LIMIT %s OFFSET %s', (per_page, offset))
    posts = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("blog.html", {
        "request": request, 
        "posts": posts,
        "page_title": "The Techie Blog",
        "page_subtitle": "Daily insights on the latest software integrations and automation strategies.",
        "post_type": "blog",
        "page": page,
        "total_pages": total_pages
    })

@app.get("/blog/{slug}")
async def read_blog(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM blog_posts WHERE slug = %s', (slug,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return {"error": "Post not found"}
    
    # Pass dynamic back routing to the HTML template
    return templates.TemplateResponse("blog_post.html", {
        "request": request, 
        "post": post,
        "back_url": "/blog",
        "back_text": "Techie Blog"
    })

# --- 2. THE AI AGENT ENDPOINT (The Automated Writer) ---

@app.get("/api/agent/daily-blog")
async def run_ai_agent(secret: str, background_tasks: BackgroundTasks):
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    conn, cursor = get_db_connection()

    # ── RATE LIMIT: only one blog post per day ─────────────────────────────
    cursor.execute(
        "SELECT COUNT(*) as count FROM blog_posts WHERE published_date >= NOW() - INTERVAL '24 hours'"
    )
    posts_today = cursor.fetchone()["count"]
    if posts_today >= 1:
        conn.close()
        return {"status": "Skipped", "reason": "Already posted a blog today. Cron will run again tomorrow."}
    # ───────────────────────────────────────────────────────────────────────

    # Pick a random integration pair
    cursor.execute("SELECT tool_a, tool_b FROM integrations")
    integrations = cursor.fetchall()
    if not integrations:
        conn.close()
        return {"error": "No integrations found in database."}

    random_pair = random.choice(integrations)
    tool_a, tool_b = random_pair["tool_a"], random_pair["tool_b"]

    # ── IMPROVED PROMPT: SEO-optimised, no clickbait ───────────────────────
    prompt = f"""
You are a B2B tech writer for integration-directory.com, a software integration directory.
Write an 900-word SEO blog post about connecting {tool_a} and {tool_b} using Make.com automation.

TITLE FORMAT (mandatory):
"How to Connect {tool_a} and {tool_b}: Step-by-Step Guide (2026)"
Wrap it in an <h1> tag.

STRUCTURE (use these exact H2 headings):
<h2>Why connect {tool_a} and {tool_b}?</h2>
<h2>What you need before you start</h2>
<h2>Step-by-step: How to integrate {tool_a} and {tool_b} using Make.com</h2>
  → Write 3 numbered steps inside this section as <ol><li> tags
<h2>Popular use cases</h2>
  → 3 bullet points, realistic business scenarios
<h2>How much time will this save?</h2>
  → 1 short paragraph with realistic time savings estimate

COM CTA (insert after the step-by-step section, exact HTML):
<div style="background:#eff6ff;border-left:4px solid #2563eb;padding:16px;border-radius:6px;margin:24px 0;">
<strong>Ready to set this up?</strong> Build this automation for free on Make.com — no coding needed.<br>
<a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored" style="color:#2563eb;font-weight:bold;">Start free on Make.com →</a>
</div>

FAQ SECTION (at the end, mandatory for Google rich snippets):
<h2>Frequently asked questions</h2>
Write exactly 3 questions and answers about this integration using <h3> for questions and <p> for answers.

STRICT RULES:
- DO NOT use words: unleash, nexus, supercharge, revolutionize, game-changer, hyper-productivity
- DO NOT invent product features
- Use plain business language, not marketing hype
- Format entire output in HTML only (<h1> <h2> <h3> <p> <ul> <ol> <li> <strong> <div>)
- Do not include greetings or sign-offs
"""
    # ───────────────────────────────────────────────────────────────────────

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        html_content = response.text
        html_content = html_content.replace("```html", "").replace("```", "").strip()

        title_match = re.search(r"<h1>(.*?)</h1>", html_content)
        title = title_match.group(1) if title_match else f"{tool_a} and {tool_b} Automation Guide"
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        cursor.execute(
            """
            INSERT INTO blog_posts (title, slug, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
            """,
            (title, slug, html_content),
        )
        conn.commit()
        conn.close()

        background_tasks.add_task(send_newsletter, title, html_content)
        return {"status": "Success", "posted": title}

    except Exception as e:
        print(f"Agent Error: {e}")
        conn.close()
        return {"status": "Failed", "error": str(e)}

# --- 3. Lead Capture Route ---
@app.post("/request-integration")
async def request_integration(email: str = Form(...), tools: str = Form(...)):
    conn, cursor = get_db_connection()
    cursor.execute('INSERT INTO leads (email, requested_tools) VALUES (%s, %s)', (email, tools))
    conn.commit()
    conn.close()
    return {"message": "Success! We will notify you when this integration is live."}

# --- NEW: Newsletter Subscription Route ---
@app.post("/subscribe")
async def subscribe_newsletter(email: str = Form(...)):
    conn, cursor = get_db_connection()
    try:
        # ON CONFLICT DO NOTHING prevents server crashes if they subscribe twice
        cursor.execute(
            'INSERT INTO newsletter_subscribers (email) VALUES (%s) ON CONFLICT (email) DO NOTHING', 
            (email.strip().lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"Subscription Error: {e}")
    finally:
        conn.close()
        
    return {"message": f"Success! {email} has been added to the Techie Newsletter."}

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
    
    # --- NEW: Fetch LIVE Trending Searches for the Sidebar Widget ---
    cursor.execute('''
        SELECT query, COUNT(*) as search_count 
        FROM search_logs 
        GROUP BY query 
        ORDER BY search_count DESC 
        LIMIT 5
    ''')
    trending_raw = cursor.fetchall()
    trending_searches = [{"term": row['query'], "count": row['search_count']} for row in trending_raw]
    # ----------------------------------------------------------------
    
    # --- NEW: Fetch E-Commerce Deals ---
    cursor.execute("SELECT * FROM ecommerce_deals ORDER BY id DESC LIMIT 5")
    daily_deals = [
        {
            "platform": "MAKE.COM",
            "product_name": "Top Integration Tools",
            "affiliate_link": "https://www.make.com/en/register?pc=sampath9",
        },
        {
            "platform": "NOTION",
            "product_name": "Free Workspace for Teams",
            "affiliate_link": "https://www.notion.so/signup",
        },
        {
            "platform": "HUBSPOT",
            "product_name": "Free CRM — Forever Free",
            "affiliate_link": "https://www.hubspot.com/products/crm",
        },
        {
            "platform": "ZAPIER",
            "product_name": "Automate 6,000+ Apps",
            "affiliate_link": "https://zapier.com/sign-up",
        },
        {
            "platform": "CLICKUP",
            "product_name": "Free Project Management",
            "affiliate_link": "https://clickup.com/",
        },
    ]
    # ---------------------------------------------------------------



    if q:
        # Save search to database to keep trending searches updated
        cursor.execute('INSERT INTO search_logs (query) VALUES (%s)', (q.strip().lower(),))
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
    
    # Safe fallback if database is empty
    total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "integrations": integrations, 
        "q": q,
        "page": page,
        "total_pages": total_pages,
        "trending_searches": trending_searches,
        "daily_deals": daily_deals,
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
    
    # 1. Fetch the relevant integrations
    query = f"%{tool}%"
    cursor.execute('SELECT * FROM integrations WHERE tool_a ILIKE %s OR tool_b ILIKE %s LIMIT 10', (query, query))
    integrations = cursor.fetchall()
    
    # 2. Fetch LIVE Trending Searches for the Sidebar
    cursor.execute('''
        SELECT query, COUNT(*) as search_count 
        FROM search_logs 
        GROUP BY query 
        ORDER BY search_count DESC 
        LIMIT 5
    ''')
    trending_raw = cursor.fetchall()
    trending_searches = [{"term": row['query'], "count": row['search_count']} for row in trending_raw]
    
    # 3. Fetch E-Commerce Deals for the Sidebar
    cursor.execute('SELECT * FROM ecommerce_deals ORDER BY RANDOM() LIMIT 4')
    daily_deals = cursor.fetchall()
    
    conn.close()
    
    # Pass ALL the data to the template!
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "integrations": integrations, 
        "q": tool,
        "title": f"Top 10 Best Integrations for {tool.capitalize()}",
        "trending_searches": trending_searches,  # <-- Now passing trending searches
        "daily_deals": daily_deals               # <-- Now passing daily deals
    })


@app.get("/integrate/{slug}")
async def integration_page(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM integrations WHERE slug = %s", (slug,))
    integration = cursor.fetchone()
    conn.close()
 
    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")
 
    # Get direct links for both tools
    tool_a_info = get_tool_link(integration["tool_a"])
    tool_b_info = get_tool_link(integration["tool_b"])
 
    return templates.TemplateResponse("integration.html", {
        "request": request,
        "data": integration,
        "make_affiliate": MAKE_AFFILIATE,
        "tool_a_info": tool_a_info,
        "tool_b_info": tool_b_info,
    })



# --- Dedicated Affiliate Landing Page (Generalized) ---

@app.get("/gear")
async def gear_page(request: Request):
    """B2B SaaS Tools landing page — optimised for AdSense + Make.com affiliate."""
    conn, cursor = get_db_connection()
    cursor.execute(
        "SELECT query, COUNT(*) as search_count FROM search_logs GROUP BY query ORDER BY search_count DESC LIMIT 5"
    )
    trending_raw = cursor.fetchall()
    trending_searches = [{"term": row["query"], "count": row["search_count"]} for row in trending_raw]
    conn.close()
 
    # B2B SaaS tool cards — direct links, no affiliate approval needed
    # Replace URL with your affiliate link once approved for each program
    saas_deals = [
        # ── Automation ─────────────────────────────────────────────────────
        {
            "category": "Automation",
            "platform": "Make.com",
            "product_name": "Automate any workflow — 1,000 ops/month free",
            "affiliate_link": "https://www.make.com/en/register?pc=sampath9",
            "badge": "★ Our Top Pick",
            "badge_color": "blue",
            "description": "Connect 1,500+ apps. Build visual automation workflows without code.",
            "is_affiliate": True,  # Your active affiliate
        },
        {
            "category": "Automation",
            "platform": "Zapier",
            "product_name": "Connect 6,000+ apps — free plan available",
            "affiliate_link": "https://zapier.com/sign-up",
            "badge": "Free plan",
            "badge_color": "orange",
            "description": "The most popular automation tool. 100 tasks/month free.",
            "is_affiliate": False,
        },
        {
            "category": "Automation",
            "platform": "n8n",
            "product_name": "Open-source automation — self-host for free",
            "affiliate_link": "https://n8n.io/",
            "badge": "Open Source",
            "badge_color": "green",
            "description": "Free forever if self-hosted. 200+ integrations included.",
            "is_affiliate": False,
        },
        # ── CRM ───────────────────────────────────────────────────────────
        {
            "category": "CRM & Sales",
            "platform": "HubSpot",
            "product_name": "Free CRM — unlimited contacts, forever free",
            "affiliate_link": "https://www.hubspot.com/products/crm",
            "badge": "Free forever",
            "badge_color": "orange",
            "description": "Manage contacts, deals and pipelines. No credit card needed.",
            "is_affiliate": False,
        },
        {
            "category": "CRM & Sales",
            "platform": "Zoho CRM",
            "product_name": "Free CRM for up to 3 users",
            "affiliate_link": "https://www.zoho.com/crm/",
            "badge": "Free plan",
            "badge_color": "red",
            "description": "Full-featured CRM. Connect with Make.com for automation.",
            "is_affiliate": False,
        },
        # ── Project Management ────────────────────────────────────────────
        {
            "category": "Project Management",
            "platform": "Notion",
            "product_name": "All-in-one workspace — free for personal use",
            "affiliate_link": "https://www.notion.so/signup",
            "badge": "Free plan",
            "badge_color": "gray",
            "description": "Notes, databases, wikis and project tracking in one tool.",
            "is_affiliate": False,
        },
        {
            "category": "Project Management",
            "platform": "Trello",
            "product_name": "Visual project boards — free forever",
            "affiliate_link": "https://trello.com/signup",
            "badge": "Free forever",
            "badge_color": "blue",
            "description": "Kanban boards for any team. Integrates with 200+ tools.",
            "is_affiliate": False,
        },
        {
            "category": "Project Management",
            "platform": "ClickUp",
            "product_name": "Replace all your tools — free forever plan",
            "affiliate_link": "https://clickup.com/",
            "badge": "Free forever",
            "badge_color": "purple",
            "description": "Tasks, docs, goals, and chat. 100MB storage free.",
            "is_affiliate": False,
        },
        # ── Communication ────────────────────────────────────────────────
        {
            "category": "Communication",
            "platform": "Slack",
            "product_name": "Team messaging — free plan for small teams",
            "affiliate_link": "https://slack.com/get-started",
            "badge": "Free plan",
            "badge_color": "green",
            "description": "90-day message history free. Integrates with Make.com.",
            "is_affiliate": False,
        },
        {
            "category": "Communication",
            "platform": "Zoom",
            "product_name": "Video meetings — 40 min free",
            "affiliate_link": "https://zoom.us/freesignup/",
            "badge": "Free plan",
            "badge_color": "blue",
            "description": "100 participants, unlimited meetings. No credit card needed.",
            "is_affiliate": False,
        },
        # ── Marketing ────────────────────────────────────────────────────
        {
            "category": "Email Marketing",
            "platform": "Mailchimp",
            "product_name": "Email marketing — 500 contacts free",
            "affiliate_link": "https://mailchimp.com/",
            "badge": "Free plan",
            "badge_color": "yellow",
            "description": "1,000 emails/month free. Automate with Make.com.",
            "is_affiliate": False,
        },
        {
            "category": "Email Marketing",
            "platform": "MailerLite",
            "product_name": "Email newsletters — 1,000 subscribers free",
            "affiliate_link": "https://www.mailerlite.com/",
            "badge": "Free plan",
            "badge_color": "green",
            "description": "12,000 emails/month free. Great for newsletters.",
            "is_affiliate": False,
        },
        # ── Support ──────────────────────────────────────────────────────
        {
            "category": "Customer Support",
            "platform": "Freshdesk",
            "product_name": "Help desk software — free for 10 agents",
            "affiliate_link": "https://freshdesk.com/",
            "badge": "Free plan",
            "badge_color": "teal",
            "description": "Tickets, live chat, and knowledge base. 100% free tier.",
            "is_affiliate": False,
        },
        {
            "category": "Customer Support",
            "platform": "Zendesk",
            "product_name": "Enterprise customer support platform",
            "affiliate_link": "https://www.zendesk.com/register/",
            "badge": "Free trial",
            "badge_color": "green",
            "description": "14-day free trial. Integrates with 1,000+ tools.",
            "is_affiliate": False,
        },
        # ── E-commerce ──────────────────────────────────────────────────
        {
            "category": "E-commerce",
            "platform": "Shopify",
            "product_name": "Start your online store — 3-day free trial",
            "affiliate_link": "https://www.shopify.com/",
            "badge": "Free trial",
            "badge_color": "green",
            "description": "Build, run and grow your e-commerce business.",
            "is_affiliate": False,
        },
        {
            "category": "E-commerce",
            "platform": "Stripe",
            "product_name": "Accept payments online — no monthly fees",
            "affiliate_link": "https://dashboard.stripe.com/register",
            "badge": "No monthly fee",
            "badge_color": "purple",
            "description": "Pay only per transaction. Works with Make.com automation.",
            "is_affiliate": False,
        },
    ]
 
    return templates.TemplateResponse("gear.html", {
        "request": request,
        "deals": saas_deals,
        "trending_searches": trending_searches,
        "make_affiliate": MAKE_AFFILIATE,
        "page_title": "Best Free SaaS Tools for 2026",
        "page_subtitle": "Hand-picked free and freemium tools to run your business. All connect with Make.com automation.",
    })


@app.get("/india-deals")
async def india_deals_page(request: Request):
    """Indian consumer deals — EarnKaro affiliate links live here."""
    conn, cursor = get_db_connection()
    # Fetch consumer deals from ecommerce_deals table (your EarnKaro links)
    cursor.execute("SELECT * FROM ecommerce_deals ORDER BY id DESC")
    all_deals = cursor.fetchall()
    cursor.execute(
        "SELECT query, COUNT(*) as search_count FROM search_logs GROUP BY query ORDER BY search_count DESC LIMIT 5"
    )
    trending_raw = cursor.fetchall()
    trending_searches = [{"term": row["query"], "count": row["search_count"]} for row in trending_raw]
    conn.close()
 
    return templates.TemplateResponse("india_deals.html", {
        "request": request,
        "deals": all_deals,
        "trending_searches": trending_searches,
        "page_title": "Top India Online Deals 2026",
        "page_subtitle": "Exclusive deals on fashion, electronics, beauty and more from top Indian platforms.",
        "make_affiliate": MAKE_AFFILIATE,
    })


# --- 6. SEO Sitemap Generation ---

@app.get("/sitemap.xml")
async def sitemap():
    conn, cursor = get_db_connection()

    cursor.execute("SELECT slug FROM integrations")
    integrations = cursor.fetchall()

    cursor.execute("SELECT slug FROM blog_posts ORDER BY published_date DESC")
    blog_posts = cursor.fetchall()

    cursor.execute("SELECT slug FROM news_posts ORDER BY published_date DESC")
    news_posts = cursor.fetchall()

    conn.close()

    base_url = "https://integration-directory.com"
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Static pages
    static_pages = [
        ("", "1.0", "daily"),
        ("/blog", "0.9", "daily"),
        ("/news", "0.9", "daily"),
        ("/gear", "0.7", "weekly"),
        ("/india-deals", "0.6", "weekly"),
        ("/contact", "0.5", "yearly"),
    ]
    for path, priority, freq in static_pages:
        xml += f"  <url>\n    <loc>{base_url}{path}</loc>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n"

    # Integration pages
    for item in integrations:
        xml += f"  <url>\n    <loc>{base_url}/integrate/{item['slug']}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"

    # Blog posts
    for post in blog_posts:
        xml += f"  <url>\n    <loc>{base_url}/blog/{post['slug']}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n"

    # News posts
    for post in news_posts:
        xml += f"  <url>\n    <loc>{base_url}/news/{post['slug']}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"

    xml += "</urlset>"
    return Response(content=xml, media_type="application/xml")

# --- 7. NEW: Autonomous Tech News Engine ---
@app.get("/news")
async def news_index(request: Request, page: int = 1):
    conn, cursor = get_db_connection()
    per_page = 15
    offset = (page - 1) * per_page
    
    cursor.execute('SELECT COUNT(*) as count FROM news_posts')
    total_items = cursor.fetchone()['count']
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    
    cursor.execute('SELECT * FROM news_posts ORDER BY published_date DESC LIMIT %s OFFSET %s', (per_page, offset))
    posts = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("blog.html", {
        "request": request, 
        "posts": posts, 
        "page_title": "Latest AI & Tech News",
        "page_subtitle": "Breaking news on Artificial Intelligence, LLMs, and the future of work.",
        "post_type": "news",
        "page": page,
        "total_pages": total_pages
    })

@app.get("/news/{slug}")
async def read_news(request: Request, slug: str):
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM news_posts WHERE slug = %s', (slug,))
    post = cursor.fetchone()
    conn.close()
    
    if not post:
        return {"error": "News article not found"}
        
    # Pass dynamic back routing to the HTML template
    return templates.TemplateResponse("blog_post.html", {
        "request": request, 
        "post": post,
        "back_url": "/news",
        "back_text": "AI News"
    })


import feedparser
import httpx

# Real RSS sources — AI and automation news only
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
]

@app.get("/api/agent/daily-news")
async def run_news_agent(secret: str, background_tasks: BackgroundTasks):
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    conn, cursor = get_db_connection()

    # ── RATE LIMIT: only one post per day ──────────────────────────────────
    cursor.execute(
        "SELECT COUNT(*) as count FROM news_posts WHERE published_date >= NOW() - INTERVAL '24 hours'"
    )
    posts_today = cursor.fetchone()["count"]
    if posts_today >= 1:
        conn.close()
        return {"status": "Skipped", "reason": "Already posted news today. Cron will run again tomorrow."}
    # ───────────────────────────────────────────────────────────────────────

    # ── FETCH REAL NEWS FROM RSS ────────────────────────────────────────────
    real_articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # top 5 from each feed
                real_articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:600],
                    "link": entry.get("link", ""),
                    "source": feed.feed.get("title", "Tech News")
                })
        except Exception as e:
            print(f"RSS fetch failed for {feed_url}: {e}")
            continue

    if not real_articles:
        conn.close()
        return {"status": "Failed", "error": "Could not fetch any RSS articles. Check feed URLs."}

    # Pick one random real article to base the post on
    source_article = random.choice(real_articles)
    # ───────────────────────────────────────────────────────────────────────

    # ── GEMINI: Write an original analysis based on the REAL article ────────
    prompt = f"""
You are a senior tech journalist writing for integration-directory.com, a site about software automation and AI tools.

A real news article was just published:
- Source: {source_article['source']}
- Headline: {source_article['title']}
- Summary: {source_article['summary']}

Write a 700-word original analysis article inspired by this REAL news. Do not invent company names or fake products.
Focus on: what this means for software integrations, workflow automation, and SaaS teams.

STRICT INSTRUCTIONS:
- Title must follow this format: "[Real Topic]: What It Means for Your Automation Workflows"
- Start the title in an <h1> tag.
- Use <h2>, <p>, <ul>, <li>, <strong> HTML only.
- Do NOT use hype words like "unleash", "nexus", "revolutionizing", "cognitive engine".
- Add a "How to automate this with Make.com" section near the end with this exact CTA:
  <div style="background:#f0f4ff;padding:16px;border-radius:8px;margin:20px 0;">
  <strong>Automate this workflow today →</strong> <a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored">Start free on Make.com</a> — no code required.
  </div>
- End with a 3-question FAQ section using <h3> for questions and <p> for answers.
- Do NOT invent statistics, company names, or product features that are not in the source article.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        html_content = response.text
        html_content = html_content.replace("```html", "").replace("```", "").strip()

        title_match = re.search(r"<h1>(.*?)</h1>", html_content)
        title = title_match.group(1) if title_match else source_article["title"]
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        cursor.execute(
            """
            INSERT INTO news_posts (title, slug, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (slug) DO NOTHING
            """,
            (title, slug, html_content),
        )
        conn.commit()
        conn.close()

        background_tasks.add_task(send_newsletter, title, html_content)
        return {"status": "Success", "posted": title, "based_on": source_article["title"]}

    except Exception as e:
        print(f"News Agent Error: {e}")
        conn.close()
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

from fastapi.responses import RedirectResponse

# ==========================================
# 11. SECRET AFFILIATE LINK MANAGER (CMS)
# ==========================================

@app.get("/admin/deals")
async def view_admin_deals(request: Request, secret: str = None):
    """A private dashboard to easily paste and manage affiliate links."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized. Please provide your secret."}

    conn, cursor = get_db_connection()
    # Fetch all active deals to show you what is currently in the sidebar
    cursor.execute('SELECT * FROM ecommerce_deals ORDER BY id DESC')
    deals = cursor.fetchall()
    conn.close()
    
    # Building a sleek, Tailwind-styled UI right here in Python
    html_content = f"""
    <html>
    <head>
        <title>Affiliate Link Manager</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 p-8 font-sans">
        <div class="max-w-3xl mx-auto">
            <h1 class="text-3xl font-bold text-gray-900 mb-6">💰 Affiliate Link Manager</h1>
            
            <div class="bg-white p-6 rounded-lg shadow-md mb-8 border border-gray-200">
                <h2 class="text-xl font-bold mb-4 text-blue-600">Add New Affiliate Link</h2>
                <form action="/admin/deals/add" method="POST" class="space-y-4">
                    <input type="hidden" name="secret" value="{secret}">
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Platform Name</label>
                            <input type="text" name="platform" placeholder="e.g., Amazon, Flipkart, Myntra" required class="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Brand Color Theme</label>
                            <select name="color_theme" class="w-full p-2 border rounded bg-white focus:ring-blue-500">
                                <option value="yellow-400">Amazon (Yellow)</option>
                                <option value="blue-500">Flipkart (Blue)</option>
                                <option value="pink-500">Myntra / Meesho (Pink)</option>
                                <option value="teal-500">Ajio / Croma (Teal)</option>
                                <option value="green-500">Generic (Green)</option>
                            </select>
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Product / Deal Name</label>
                        <input type="text" name="product_name" placeholder="e.g., Top Tech Deals Today" required class="w-full p-2 border rounded focus:ring-blue-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Your Affiliate Link URL</label>
                        <input type="url" name="affiliate_link" placeholder="Paste your EarnKaro or Amazon tracking link here..." required class="w-full p-2 border rounded focus:ring-blue-500">
                    </div>
                    
                    <button type="submit" class="w-full bg-blue-600 text-white font-bold py-3 rounded hover:bg-blue-700 transition">Add Link to Website</button>
                </form>
            </div>

            <h2 class="text-xl font-bold mb-4 text-gray-800">Active Links in Sidebar ({len(deals)})</h2>
            <div class="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Platform</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
    """
    
    # Loop through the database to show what is currently live
    for deal in deals:
        html_content += f"""
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-l-4 border-{deal['color_theme']}">{deal['platform']}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><a href="{deal['affiliate_link']}" target="_blank" rel="sponsored nofollow" class="text-blue-600 hover:underline">{deal['product_name']}</a></td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-bold">
                                <form action="/admin/deals/delete" method="POST" style="margin:0;">
                                    <input type="hidden" name="secret" value="{secret}">
                                    <input type="hidden" name="deal_id" value="{deal['id']}">
                                    <button type="submit" class="text-red-600 hover:underline">Remove</button>
                                </form>
                            </td>
                        </tr>
        """
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


@app.post("/admin/deals/add")
async def add_admin_deal(
    secret: str = Form(...),
    platform: str = Form(...),
    product_name: str = Form(...),
    affiliate_link: str = Form(...),
    color_theme: str = Form(...)
):
    """Processes the form and saves the new link to the database."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized."}

    conn, cursor = get_db_connection()
    try:
        cursor.execute('''
            INSERT INTO ecommerce_deals (platform, product_name, affiliate_link, color_theme) 
            VALUES (%s, %s, %s, %s)
        ''', (platform, product_name, affiliate_link, color_theme))
        conn.commit()
    finally:
        conn.close()
        
    # Instantly refreshes the admin page so you see the new link!
    return RedirectResponse(url=f"/admin/deals?secret={secret}", status_code=303)


@app.post("/admin/deals/delete")
async def delete_admin_deal(secret: str = Form(...), deal_id: int = Form(...)):
    """Removes a link from the sidebar."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized."}

    conn, cursor = get_db_connection()
    try:
        cursor.execute('DELETE FROM ecommerce_deals WHERE id = %s', (deal_id,))
        conn.commit()
    finally:
        conn.close()
        
    return RedirectResponse(url=f"/admin/deals?secret={secret}", status_code=303)



#CONTACT_ROUTE = '''
@app.get("/contact")
async def contact_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})
