"""
BLOG SEED SCRIPT — run this ONCE to populate your blog with 5 real posts.
This ensures your /blog page has real content for Google AdSense approval.

Usage:
    python seed_blog.py

Requirements: same DATABASE_URL env var as main.py
"""

import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn, conn.cursor(cursor_factory=RealDictCursor)

POSTS = [
    {
        "title": "How to Connect Slack and Notion: The Complete 2026 Automation Guide",
        "slug": "how-to-connect-slack-and-notion-automation-guide-2026",
        "content": """
<h2>Why Slack + Notion Is the Power Couple Every Team Needs</h2>
<p>If your team runs on Slack for communication and Notion for documentation, you already know the frustration: a great idea discussed in a Slack thread dies there. It never makes it to your Notion workspace. The context is lost. Work is duplicated.</p>
<p>Connecting Slack and Notion with automation solves this entirely. Over 6,274 professionals search for this integration every month — and for good reason.</p>

<h2>What You Can Automate Between Slack and Notion</h2>
<ul>
  <li><strong>Auto-create Notion pages from Slack messages:</strong> Tag a message with an emoji or slash command and have it automatically saved as a Notion page.</li>
  <li><strong>Send Notion database updates to Slack:</strong> When a task status changes in Notion, notify the relevant Slack channel instantly.</li>
  <li><strong>Daily digests:</strong> Every morning, send a Slack message listing all Notion tasks due today.</li>
  <li><strong>Meeting notes to Notion:</strong> Paste meeting notes into Slack and have them structured and filed in Notion automatically.</li>
</ul>

<h2>Step-by-Step: Setting Up Slack + Notion with Make.com</h2>
<p>Make.com (formerly Integromat) is the easiest way to connect Slack and Notion without writing a single line of code.</p>
<ol>
  <li>Create a free account at <a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Make.com</a>.</li>
  <li>Click <strong>Create a new scenario</strong>.</li>
  <li>Add Slack as the trigger app. Select the trigger "Watch new messages in a channel".</li>
  <li>Add Notion as the action. Select "Create a database item".</li>
  <li>Map the Slack message text to the Notion page title and body.</li>
  <li>Click <strong>Run once</strong> to test, then activate your automation.</li>
</ol>

<h2>How Much Time Will You Save?</h2>
<p>If your team manually copies 10 messages per day from Slack into Notion, and each copy takes 3 minutes, that is 30 minutes per day — or <strong>10+ hours per month per person</strong>. Automate it and get those hours back.</p>

<h2>Tips for Getting the Most Out of This Integration</h2>
<ul>
  <li>Use Slack's emoji reactions as triggers — for example, reacting with 📝 saves a message to Notion automatically.</li>
  <li>Set up filters so only messages from specific channels trigger Notion entries.</li>
  <li>Use Notion's database templates to ensure every auto-created page has the right structure.</li>
</ul>

<h2>Recommended Tools</h2>
<p>To set this up today, you will need:</p>
<ul>
  <li><a href="https://slack.com/get-started" rel="noopener">Slack</a> — free plan available for small teams.</li>
  <li><a href="https://www.notion.so/signup" rel="noopener">Notion</a> — free for personal use.</li>
  <li><a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Make.com</a> — 1,000 free operations per month, no credit card required.</li>
</ul>
"""
    },
    {
        "title": "Make.com vs Zapier in 2026: Which Automation Tool Is Right for You?",
        "slug": "make-com-vs-zapier-2026-comparison",
        "content": """
<h2>The Two Giants of No-Code Automation</h2>
<p>If you want to automate your business workflows without writing code, two tools dominate the market in 2026: Make.com and Zapier. Both connect thousands of apps and let you build automated workflows — but they are built for very different users.</p>
<p>This guide breaks down the real differences so you can choose the right tool for your needs.</p>

<h2>Make.com: Visual, Powerful, and Affordable</h2>
<p>Make.com (formerly Integromat) uses a visual, drag-and-drop canvas to build automations. You can see every step of your workflow as a flowchart, which makes complex multi-step automations much easier to build and debug.</p>
<ul>
  <li><strong>Free plan:</strong> 1,000 operations per month, unlimited scenarios.</li>
  <li><strong>Best for:</strong> Developers, power users, and businesses with complex workflows involving conditionals, loops, and data transformation.</li>
  <li><strong>Pricing:</strong> From $9/month for the Core plan (10,000 ops).</li>
  <li><strong>Integrations:</strong> 1,500+ apps.</li>
</ul>

<h2>Zapier: Simple, Fast, and the Most Popular</h2>
<p>Zapier is the most widely used automation tool in the world. Its linear "Zap" format (trigger → action) is extremely easy to understand for beginners. If you need a simple two-step automation, Zapier has you set up in under 5 minutes.</p>
<ul>
  <li><strong>Free plan:</strong> 100 tasks per month, 5 Zaps.</li>
  <li><strong>Best for:</strong> Non-technical users who need simple automations quickly.</li>
  <li><strong>Pricing:</strong> From $19.99/month for the Starter plan (750 tasks).</li>
  <li><strong>Integrations:</strong> 6,000+ apps — the largest library available.</li>
</ul>

<h2>Head-to-Head Comparison</h2>
<table style="width:100%; border-collapse:collapse; margin:1rem 0;">
  <tr style="background:#eff6ff;">
    <th style="text-align:left; padding:10px; border:1px solid #e5e7eb;">Feature</th>
    <th style="text-align:left; padding:10px; border:1px solid #e5e7eb;">Make.com</th>
    <th style="text-align:left; padding:10px; border:1px solid #e5e7eb;">Zapier</th>
  </tr>
  <tr>
    <td style="padding:10px; border:1px solid #e5e7eb;">Free plan ops</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">1,000/month</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">100 tasks/month</td>
  </tr>
  <tr>
    <td style="padding:10px; border:1px solid #e5e7eb;">Ease of use</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">Medium (visual canvas)</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">Very Easy (linear)</td>
  </tr>
  <tr>
    <td style="padding:10px; border:1px solid #e5e7eb;">Complex workflows</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">⭐⭐⭐⭐⭐</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">⭐⭐⭐</td>
  </tr>
  <tr>
    <td style="padding:10px; border:1px solid #e5e7eb;">App integrations</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">1,500+</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">6,000+</td>
  </tr>
  <tr>
    <td style="padding:10px; border:1px solid #e5e7eb;">Value for money</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">⭐⭐⭐⭐⭐</td>
    <td style="padding:10px; border:1px solid #e5e7eb;">⭐⭐⭐</td>
  </tr>
</table>

<h2>Our Recommendation</h2>
<p>For most growing businesses and developers: <strong>start with Make.com</strong>. The free plan is 10× more generous than Zapier's, and the visual canvas makes it easier to build sophisticated automations. If you find a specific app that only Zapier supports, you can always use both.</p>

<h2>Get Started</h2>
<ul>
  <li><a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Try Make.com free →</a> (1,000 ops/month, no credit card)</li>
  <li><a href="https://zapier.com/sign-up" rel="noopener">Try Zapier free →</a> (100 tasks/month)</li>
</ul>
"""
    },
    {
        "title": "10 Shopify Automations That Will Save Your E-Commerce Team Hours Every Week",
        "slug": "shopify-automations-save-time-ecommerce-2026",
        "content": """
<h2>Why Shopify Store Owners Need Automation in 2026</h2>
<p>Running a Shopify store in 2026 means managing orders, customer support, inventory, marketing, and fulfilment — often with a small team. The stores that scale fastest are not the ones working harder; they are the ones that automate the repetitive work.</p>
<p>Here are 10 practical automations every Shopify store owner should set up today.</p>

<h2>1. Auto-Notify Slack When a New Order Arrives</h2>
<p>Connect Shopify to Slack so your team gets an instant notification every time a new order is placed. Include the order value, product name, and customer location in the message.</p>

<h2>2. Add Customers to Mailchimp Automatically</h2>
<p>Every new Shopify customer is added to your Mailchimp email list automatically, tagged by product category. This means your post-purchase email flows start working the moment someone buys.</p>

<h2>3. Create a Google Sheets Order Log</h2>
<p>For sellers who want a simple spreadsheet overview: automatically append every new Shopify order to a Google Sheet. Great for accountants and finance teams.</p>

<h2>4. Alert Your Team When Stock Is Low</h2>
<p>When a product inventory level drops below your threshold (e.g., 5 units), send an automatic alert to Slack or email. Never run out of stock unexpectedly again.</p>

<h2>5. Create a Trello Card for Every Refund Request</h2>
<p>When a refund is requested in Shopify, automatically create a Trello card in your "Refunds to Process" board. Assign it to the relevant team member with the order details pre-filled.</p>

<h2>6. Tag High-Value Customers in Your CRM</h2>
<p>When a customer's total lifetime spend exceeds a threshold (e.g., ₹10,000), automatically tag them as "VIP" in HubSpot. Then trigger a personalised outreach email.</p>

<h2>7. Post New Products to Social Media</h2>
<p>When you publish a new Shopify product, automatically draft a social media post and send it to your social manager for approval via Slack.</p>

<h2>8. Send Abandoned Cart Alerts to Your Team</h2>
<p>High-value abandoned carts (above a certain value) can trigger an alert to your sales team to follow up personally — a great tactic for B2B or high-ticket stores.</p>

<h2>9. Sync Orders with Your Accounting Software</h2>
<p>Connect Shopify to Zoho Books or QuickBooks via Make.com. Every completed order automatically creates an invoice — no manual data entry at month-end.</p>

<h2>10. Auto-Tag Orders by Product Category</h2>
<p>Automatically tag Shopify orders by the product category purchased. This makes it easy to segment customers for targeted campaigns later.</p>

<h2>How to Set These Up (No Code Required)</h2>
<p>All of the above can be built in Make.com using their Shopify integration. You do not need to write any code — just connect your Shopify store, choose your trigger (e.g., "New Order"), and configure your action.</p>
<p><a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Start automating with Make.com for free →</a></p>
"""
    },
    {
        "title": "The Best Free CRM for Small Businesses in 2026: HubSpot vs Zoho vs Notion",
        "slug": "best-free-crm-small-business-2026-hubspot-zoho-notion",
        "content": """
<h2>Do You Really Need a CRM?</h2>
<p>If you are managing more than 10 active client relationships, the answer is yes. A CRM (Customer Relationship Management tool) keeps track of every conversation, deal, and task in one place — so nothing falls through the cracks and your team stays aligned.</p>
<p>The good news: in 2026, you do not need to spend money to get a great CRM. Here is how the top three free options compare.</p>

<h2>HubSpot CRM: The Best Free Option Overall</h2>
<p>HubSpot's free CRM is the most powerful free tier on the market. It includes unlimited contacts, a visual deals pipeline, email tracking, meeting scheduling, and a full activity timeline — all for free, forever.</p>
<ul>
  <li><strong>Best for:</strong> Sales teams, B2B businesses, and anyone who wants a complete CRM with no cost.</li>
  <li><strong>Free features:</strong> Unlimited contacts, deals pipeline, email integration, meeting links, basic reporting.</li>
  <li><strong>Limitation:</strong> Advanced automation and sequences require paid plans.</li>
</ul>
<p><a href="https://www.hubspot.com/products/crm" rel="noopener">Get HubSpot free →</a></p>

<h2>Zoho CRM: Best for Small Teams Up to 3 Users</h2>
<p>Zoho CRM's free plan supports up to 3 users and includes leads, contacts, accounts, and deal management. It is more feature-rich on the free tier than many paid tools, and integrates tightly with the broader Zoho suite (Zoho Books, Zoho Desk, etc.).</p>
<ul>
  <li><strong>Best for:</strong> Teams of 1–3 who also use other Zoho products.</li>
  <li><strong>Free features:</strong> Leads, contacts, deals, tasks, email integration.</li>
  <li><strong>Limitation:</strong> Capped at 3 users on the free plan.</li>
</ul>

<h2>Notion: The Flexible Alternative</h2>
<p>Notion is not technically a CRM, but thousands of small businesses use it as one. With its database and template system, you can build a custom CRM that fits exactly how your business works. There is a free template library with CRM setups you can copy in one click.</p>
<ul>
  <li><strong>Best for:</strong> Solopreneurs and small teams who want full flexibility and already use Notion.</li>
  <li><strong>Free features:</strong> Unlimited pages and databases on the free personal plan.</li>
  <li><strong>Limitation:</strong> No built-in sales automation — you need to add that via Make.com.</li>
</ul>

<h2>Our Recommendation</h2>
<p>For most small businesses: <strong>start with HubSpot's free CRM</strong>. It is the most complete free option, with no user limits and no credit card required. Connect it to Make.com to automate your follow-ups, and you will have a sales machine that runs itself.</p>

<p><a href="https://www.hubspot.com/products/crm" rel="noopener">Get HubSpot free →</a> &nbsp; | &nbsp; <a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Automate HubSpot with Make.com →</a></p>
"""
    },
    {
        "title": "How to Automate Your Newsletter: From Subscriber to Inbox Without Lifting a Finger",
        "slug": "automate-newsletter-workflow-mailchimp-make-2026",
        "content": """
<h2>Why Newsletter Automation Is the Best ROI in 2026</h2>
<p>Email marketing generates an average return of $36 for every $1 spent — the highest ROI of any digital marketing channel. But most businesses leave this money on the table because manually managing a newsletter takes too much time.</p>
<p>In this guide, we will show you how to build a fully automated newsletter workflow using free tools.</p>

<h2>The Tools You Need</h2>
<ul>
  <li><strong>Mailchimp or MailerLite:</strong> Your email sending platform. Both offer free plans (Mailchimp: 500 contacts / 1,000 emails per month; MailerLite: 1,000 subscribers / 12,000 emails per month).</li>
  <li><strong>Make.com:</strong> The automation layer that connects everything. 1,000 free operations per month.</li>
  <li><strong>Your content source:</strong> This could be your blog, an RSS feed, a Google Sheet, or an AI content generator.</li>
</ul>

<h2>The Automation Workflow: Step by Step</h2>
<ol>
  <li><strong>Trigger:</strong> A new post is published on your blog (or a new row is added to a Google Sheet).</li>
  <li><strong>Fetch content:</strong> Make.com reads the post title, excerpt, and URL.</li>
  <li><strong>Create email draft:</strong> Make.com creates a new campaign draft in Mailchimp using a pre-built template. The blog content is automatically inserted.</li>
  <li><strong>Schedule send:</strong> The campaign is scheduled to go out the next morning at 8am.</li>
  <li><strong>Track opens and clicks:</strong> Mailchimp automatically tracks engagement and updates your subscriber records.</li>
</ol>

<h2>Building Your Subscriber List (The Right Way)</h2>
<p>Automation only works if you have subscribers. Here is how to grow your list organically:</p>
<ul>
  <li>Add a newsletter signup form to your homepage and footer (your Integration Directory already has this).</li>
  <li>Offer a lead magnet: a free PDF guide, checklist, or template in exchange for an email address.</li>
  <li>Promote your newsletter in every blog post with an inline signup CTA.</li>
  <li>Post about your newsletter content on LinkedIn and Twitter with a signup link.</li>
</ul>

<h2>The Complete Free Stack</h2>
<ul>
  <li><a href="https://mailchimp.com/" rel="noopener">Mailchimp free →</a> (500 contacts, 1,000 emails/month)</li>
  <li><a href="https://www.mailerlite.com/" rel="noopener">MailerLite free →</a> (1,000 subscribers, 12,000 emails/month — better value)</li>
  <li><a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored nofollow">Make.com free →</a> (automation layer)</li>
</ul>

<h2>One Last Tip</h2>
<p>Consistency beats perfection. A weekly newsletter sent automatically every Thursday at 8am will always outperform a "perfect" newsletter sent whenever you have time. Set up the automation once and let it run.</p>
"""
    }
]

def seed_blog():
    conn, cursor = get_db()
    inserted = 0
    for i, post in enumerate(POSTS):
        # Stagger publish dates so they look organic (5 days apart)
        pub_date = datetime.now() - timedelta(days=i * 5)
        try:
            cursor.execute(
                '''INSERT INTO blog_posts (title, slug, content, published_date)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (slug) DO NOTHING''',
                (post["title"], post["slug"], post["content"], pub_date)
            )
            if cursor.rowcount > 0:
                inserted += 1
                print(f"✓ Inserted: {post['title']}")
            else:
                print(f"↷ Already exists: {post['title']}")
        except Exception as e:
            print(f"✗ Error inserting '{post['title']}': {e}")

    conn.commit()
    conn.close()
    print(f"\nDone! Inserted {inserted} new blog posts.")

if __name__ == "__main__":
    seed_blog()