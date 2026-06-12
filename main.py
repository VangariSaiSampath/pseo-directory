import os
import math
import random
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

app = FastAPI()

from google import genai
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from the Python package directory itself.
load_dotenv(Path(__file__).resolve().parent / ".env")

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks

from fastapi.responses import RedirectResponse

import feedparser
import httpx

from fastapi.responses import PlainTextResponse

from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import HTMLResponse

@app.get("/ads.txt", response_class=PlainTextResponse)
async def ads_txt():
    # Replace with your actual AdSense publisher ID once approved
    # Format: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
    return "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0"

# ================================================================
# TOOL DESCRIPTIONS DATA
# Paste this dictionary into main.py (at the top, after imports)
# Then update your integration route to pass these to the template
# ================================================================

TOOL_DATA = {
    "slack": {
        "name": "Slack",
        "emoji": "💬",
        "category": "Team Communication",
        "plan": "Free plan available",
        "url": "https://slack.com/get-started",
        "description": (
            "Slack is the world's most popular team messaging platform, used by over "
            "10 million people daily. It organises conversations into channels, threads, "
            "and direct messages, making it easy for teams of any size to collaborate "
            "in real time — whether in the same office or across the globe."
        ),
        "features": [
            "Organised channels for every project and team",
            "Instant direct messaging and group chats",
            "File sharing, search, and message history",
            "1,000+ app integrations including Make.com",
            "Audio and video huddles built-in",
        ],
        "short": "Team messaging platform used by 10M+ people daily.",
    },
    "notion": {
        "name": "Notion",
        "emoji": "📝",
        "category": "Productivity & Docs",
        "plan": "Free for personal use",
        "url": "https://www.notion.so/signup",
        "description": (
            "Notion is an all-in-one workspace that replaces your notes, docs, wikis, "
            "and project management tools. Teams use it to write, plan, collaborate, and "
            "organise everything in one place. Its flexible database system lets you build "
            "custom workflows, CRMs, and content trackers without writing any code."
        ),
        "features": [
            "Notes, wikis, and rich-text documents",
            "Flexible databases and table views",
            "Kanban boards and Gantt-style timelines",
            "Team collaboration with real-time editing",
            "AI assistant built in (Notion AI)",
        ],
        "short": "All-in-one workspace for notes, docs, and project management.",
    },
    "hubspot": {
        "name": "HubSpot",
        "emoji": "🧲",
        "category": "CRM & Marketing",
        "plan": "Free forever",
        "url": "https://www.hubspot.com/products/crm",
        "description": (
            "HubSpot is the most widely used free CRM in the world, trusted by over "
            "200,000 companies. It combines contact management, deal tracking, email "
            "marketing, and customer support into a single platform. The free tier is "
            "genuinely powerful — unlimited contacts, a full deals pipeline, and email "
            "tracking are all included at no cost."
        ),
        "features": [
            "Unlimited contacts and companies — free forever",
            "Visual deals pipeline and sales tracking",
            "Email tracking and meeting scheduler",
            "Marketing emails and landing pages",
            "Live chat and ticketing support tools",
        ],
        "short": "The world's most popular free CRM with unlimited contacts.",
    },
    "salesforce": {
        "name": "Salesforce",
        "emoji": "☁️",
        "category": "Enterprise CRM",
        "plan": "30-day free trial",
        "url": "https://www.salesforce.com/form/signup/freetrial-sales/",
        "description": (
            "Salesforce is the world's #1 enterprise CRM platform, used by over 150,000 "
            "companies globally. It provides advanced tools for sales forecasting, "
            "pipeline management, customer service, and marketing automation. Salesforce "
            "is highly customisable and integrates with virtually every major business "
            "application via its AppExchange marketplace."
        ),
        "features": [
            "Advanced sales pipeline and opportunity tracking",
            "AI-powered forecasting with Salesforce Einstein",
            "AppExchange with 3,000+ integrations",
            "Custom reports and real-time dashboards",
            "Enterprise-grade security and compliance",
        ],
        "short": "The world's #1 enterprise CRM used by 150,000+ companies.",
    },
    "trello": {
        "name": "Trello",
        "emoji": "📋",
        "category": "Project Management",
        "plan": "Free forever",
        "url": "https://trello.com/signup",
        "description": (
            "Trello is a visual project management tool built around the Kanban board "
            "methodology. Teams use it to organise tasks into lists and drag them through "
            "stages — To Do, In Progress, Done. It is simple enough for personal use but "
            "powerful enough for teams of 100+, with automation via Butler and over 200 "
            "Power-Up integrations."
        ),
        "features": [
            "Drag-and-drop Kanban boards",
            "Cards with checklists, due dates, and attachments",
            "Butler automation for recurring tasks",
            "200+ Power-Up integrations",
            "Timeline and calendar views on paid plans",
        ],
        "short": "Visual Kanban boards for organising any project or team.",
    },
    "asana": {
        "name": "Asana",
        "emoji": "✅",
        "category": "Project Management",
        "plan": "Free for up to 10 users",
        "url": "https://asana.com/create-account",
        "description": (
            "Asana is a leading work management platform that helps teams organise, "
            "track, and manage their projects in one place. It offers tasks, subtasks, "
            "projects, portfolios, and workload management. Over 131,000 paying "
            "organisations use Asana to coordinate work across departments and reduce "
            "the need for status update meetings."
        ),
        "features": [
            "Tasks, subtasks, and project templates",
            "Multiple views: list, board, timeline, calendar",
            "Portfolio and workload management",
            "Goal tracking and OKR management",
            "300+ integrations including Slack, Zoom, and Make.com",
        ],
        "short": "Work management for teams to coordinate projects at scale.",
    },
    "jira": {
        "name": "Jira",
        "emoji": "🔵",
        "category": "Dev Project Management",
        "plan": "Free for up to 10 users",
        "url": "https://www.atlassian.com/software/jira",
        "description": (
            "Jira is the industry-standard project management tool for software development "
            "teams. Built by Atlassian, it supports agile methodologies including Scrum "
            "and Kanban. Engineering teams use Jira to plan sprints, track bugs, manage "
            "releases, and report on velocity. It integrates tightly with GitHub, "
            "Bitbucket, Confluence, and 3,000+ other tools."
        ),
        "features": [
            "Scrum and Kanban boards for agile teams",
            "Bug tracking and issue management",
            "Sprint planning and velocity reporting",
            "Roadmaps and release management",
            "3,000+ integrations via the Atlassian Marketplace",
        ],
        "short": "The industry-standard project tracker for software dev teams.",
    },
    "zoom": {
        "name": "Zoom",
        "emoji": "📹",
        "category": "Video Conferencing",
        "plan": "Free plan available",
        "url": "https://zoom.us/freesignup/",
        "description": (
            "Zoom is the world's most widely used video conferencing platform, with over "
            "350 million daily meeting participants. It powers remote meetings, webinars, "
            "online events, and team collaboration. The free plan allows unlimited 1:1 "
            "meetings and group calls up to 40 minutes, making it the go-to solution "
            "for distributed teams."
        ),
        "features": [
            "HD video and audio meetings",
            "Screen sharing and whiteboard",
            "Breakout rooms and webinar hosting",
            "Meeting recordings to cloud or local",
            "1,000+ app integrations via Zoom App Marketplace",
        ],
        "short": "World's leading video conferencing with 350M+ daily users.",
    },
    "mailchimp": {
        "name": "Mailchimp",
        "emoji": "📧",
        "category": "Email Marketing",
        "plan": "Free up to 500 contacts",
        "url": "https://mailchimp.com/",
        "description": (
            "Mailchimp is the world's most popular email marketing platform, trusted by "
            "over 11 million businesses. It lets you design professional emails, build "
            "automated campaigns, and analyse performance — all from a drag-and-drop "
            "editor. The free plan includes 500 contacts and 1,000 emails per month, "
            "making it perfect for growing businesses."
        ),
        "features": [
            "Drag-and-drop email designer",
            "Automated email sequences and drip campaigns",
            "Audience segmentation and personalisation",
            "A/B testing and campaign analytics",
            "Landing pages and signup forms",
        ],
        "short": "Email marketing platform trusted by 11 million businesses.",
    },
    "stripe": {
        "name": "Stripe",
        "emoji": "💳",
        "category": "Payments",
        "plan": "No monthly fee",
        "url": "https://dashboard.stripe.com/register",
        "description": (
            "Stripe is the world's most developer-friendly payment processing platform, "
            "powering payments for millions of businesses from startups to Fortune 500 "
            "companies. It handles online payments, subscriptions, invoicing, and fraud "
            "prevention. With no monthly fees — just a small per-transaction fee — it "
            "is ideal for businesses of any size."
        ),
        "features": [
            "Accept cards, UPI, wallets, and bank transfers",
            "Subscription billing and recurring payments",
            "Invoicing and automated payment collection",
            "Advanced fraud detection (Radar)",
            "Real-time payment analytics dashboard",
        ],
        "short": "The world's most developer-friendly payment processing platform.",
    },
    "shopify": {
        "name": "Shopify",
        "emoji": "🛍️",
        "category": "E-Commerce",
        "plan": "3-day free trial",
        "url": "https://www.shopify.com/",
        "description": (
            "Shopify is the leading e-commerce platform powering over 1.7 million "
            "businesses in 175 countries. It lets you build a professional online store "
            "in minutes, manage inventory, process payments, and fulfil orders — all "
            "from one dashboard. With thousands of apps and Make.com integrations, "
            "Shopify stores can be fully automated."
        ),
        "features": [
            "Professional online store builder",
            "Inventory management and order fulfilment",
            "Built-in payment processing (Shopify Payments)",
            "Shopify App Store with 8,000+ apps",
            "Analytics, reports, and customer insights",
        ],
        "short": "The leading e-commerce platform powering 1.7M+ businesses.",
    },
    "zapier": {
        "name": "Zapier",
        "emoji": "⚡",
        "category": "Automation",
        "plan": "Free up to 100 tasks/month",
        "url": "https://zapier.com/sign-up",
        "description": (
            "Zapier is the world's most popular no-code automation tool, connecting "
            "6,000+ apps without writing a single line of code. Each automation (called "
            "a 'Zap') follows a simple trigger-action format. It is the easiest automation "
            "tool for beginners, and its massive app library means you can connect almost "
            "any two tools you already use."
        ),
        "features": [
            "6,000+ app integrations — the largest library",
            "Simple trigger-action automation format",
            "Multi-step Zaps with filters and conditions",
            "Pre-built Zap templates for popular workflows",
            "No coding required — beginner friendly",
        ],
        "short": "No-code automation connecting 6,000+ apps. Largest app library.",
    },
    "google-sheets": {
        "name": "Google Sheets",
        "emoji": "📊",
        "category": "Spreadsheets",
        "plan": "Free with Google account",
        "url": "https://sheets.google.com",
        "description": (
            "Google Sheets is Google's free, cloud-based spreadsheet application used "
            "by over 1 billion people. It combines the power of Excel with real-time "
            "collaboration, making it ideal for teams managing data, tracking KPIs, or "
            "running automated reporting. As a Make.com integration target, Sheets is "
            "one of the most versatile data destinations available."
        ),
        "features": [
            "Real-time collaborative editing",
            "Powerful formulas and pivot tables",
            "Google Apps Script for custom automation",
            "Charts, dashboards, and conditional formatting",
            "Connects to Make.com as a trigger or action",
        ],
        "short": "Google's free cloud spreadsheet used by 1 billion people.",
    },
    "google-drive": {
        "name": "Google Drive",
        "emoji": "📁",
        "category": "Cloud Storage",
        "plan": "15 GB free",
        "url": "https://drive.google.com",
        "description": (
            "Google Drive is Google's cloud storage and file management service, offering "
            "15 GB free for every Google account. Teams use it to store, share, and "
            "collaborate on documents, spreadsheets, and presentations in real time. "
            "With Make.com, you can automate file creation, organisation, sharing, and "
            "notifications based on Drive activity."
        ),
        "features": [
            "15 GB free cloud storage",
            "Real-time collaboration on Docs, Sheets, Slides",
            "File sharing with granular permission controls",
            "Search across all file types including PDFs",
            "Integrates with Make.com for file automation",
        ],
        "short": "Google's cloud storage with 15 GB free and real-time collaboration.",
    },
    "airtable": {
        "name": "Airtable",
        "emoji": "🗂️",
        "category": "Database & Spreadsheet",
        "plan": "Free plan available",
        "url": "https://airtable.com/signup",
        "description": (
            "Airtable is a flexible database-spreadsheet hybrid that teams use to manage "
            "almost anything — from content calendars and CRMs to project trackers and "
            "product roadmaps. Its visual interface combines the familiarity of a "
            "spreadsheet with the power of a relational database, making it ideal for "
            "non-technical teams who need structured data management."
        ),
        "features": [
            "Spreadsheet-style rows with database power",
            "Multiple views: grid, gallery, kanban, calendar",
            "Linked records across tables (relational data)",
            "Automations and scripting built in",
            "Rich field types: attachments, ratings, formulas",
        ],
        "short": "Flexible database-spreadsheet hybrid for any business data.",
    },
    "clickup": {
        "name": "ClickUp",
        "emoji": "🎯",
        "category": "Project Management",
        "plan": "Free forever",
        "url": "https://clickup.com/",
        "description": (
            "ClickUp is an all-in-one productivity platform designed to replace multiple "
            "separate tools with a single workspace. It combines tasks, docs, goals, chat, "
            "whiteboards, and time tracking in one place. With a generous free forever "
            "plan and 1,000+ integrations, ClickUp is one of the fastest-growing "
            "productivity tools among startups and agencies."
        ),
        "features": [
            "Tasks, subtasks, and checklists",
            "Docs, wikis, and collaborative notes",
            "Goals, OKRs, and time tracking",
            "15+ view types including timeline and mind map",
            "1,000+ integrations including Make.com",
        ],
        "short": "All-in-one productivity replacing tasks, docs, goals, and chat.",
    },
    "make": {
        "name": "Make.com",
        "emoji": "⚙️",
        "category": "Automation Platform",
        "plan": "1,000 ops/month free",
        "url": "https://www.make.com/en/register?pc=sampath9",
        "description": (
            "Make.com (formerly Integromat) is the most powerful visual automation "
            "platform available. Unlike linear tools, Make uses a canvas where you can "
            "build complex multi-step scenarios with branches, loops, filters, and data "
            "transformations. With 1,500+ app integrations and a free plan that includes "
            "1,000 operations per month, it is the best value automation tool in 2026."
        ),
        "features": [
            "1,500+ app integrations",
            "Visual drag-and-drop scenario builder",
            "Advanced: loops, branches, error handling",
            "1,000 free operations per month",
            "Real-time monitoring and execution history",
        ],
        "short": "The most powerful visual automation platform with 1,500+ integrations.",
    },
    "freshdesk": {
        "name": "Freshdesk",
        "emoji": "🎧",
        "category": "Customer Support",
        "plan": "Free for up to 10 agents",
        "url": "https://freshdesk.com/",
        "description": (
            "Freshdesk is a cloud-based customer support platform used by over 50,000 "
            "businesses. It centralises customer queries from email, chat, phone, and "
            "social media into a single ticketing system. The free Sprout plan supports "
            "up to 10 agents with unlimited tickets, making it one of the most generous "
            "free support tools available."
        ),
        "features": [
            "Unified ticket inbox from all channels",
            "Automated ticket routing and SLAs",
            "Knowledge base and self-service portal",
            "Canned responses and collision detection",
            "Reports and customer satisfaction surveys",
        ],
        "short": "Cloud helpdesk unifying support tickets from all channels.",
    },
    "zendesk": {
        "name": "Zendesk",
        "emoji": "💬",
        "category": "Customer Support",
        "plan": "14-day free trial",
        "url": "https://www.zendesk.com/register/",
        "description": (
            "Zendesk is the enterprise-grade customer support platform used by some of "
            "the world's largest companies including Airbnb, Uber, and Shopify. It offers "
            "ticketing, live chat, a knowledge base, and an AI-powered bot — all in one "
            "platform. Zendesk's integration with Make.com allows you to automate ticket "
            "workflows, escalations, and customer notifications."
        ),
        "features": [
            "Multi-channel ticketing (email, chat, social)",
            "AI-powered chatbot (Zendesk Bot)",
            "Self-service knowledge base",
            "SLA management and escalation rules",
            "1,000+ marketplace integrations",
        ],
        "short": "Enterprise support platform used by Airbnb, Uber, and Shopify.",
    },
    "mailerlite": {
        "name": "MailerLite",
        "emoji": "📨",
        "category": "Email Marketing",
        "plan": "Free up to 1,000 subscribers",
        "url": "https://www.mailerlite.com/",
        "description": (
            "MailerLite is a clean, modern email marketing platform known for its ease "
            "of use and generous free plan. With 1,000 free subscribers and 12,000 "
            "emails per month, it offers better value than most competitors. Teams use "
            "it for newsletters, automated sequences, landing pages, and pop-up forms."
        ),
        "features": [
            "1,000 free subscribers, 12,000 emails/month",
            "Drag-and-drop email editor",
            "Automation workflows and drip sequences",
            "Landing pages and pop-up forms",
            "Detailed analytics and A/B testing",
        ],
        "short": "Email marketing with the most generous free plan — 1,000 subscribers.",
    },
    # ── NEW TOOLS ADDED ─────────────────────────────────────────
 
    "jasper": {
        "name": "Jasper",
        "emoji": "✍️",
        "category": "AI Writing",
        "plan": "7-day free trial",
        "url": "https://www.jasper.ai/",
        "description": (
            "Jasper is the world's leading AI writing assistant, used by over 100,000 "
            "marketing teams and content creators. It generates high-quality blog posts, "
            "ad copy, social media content, and email sequences in seconds. Jasper is "
            "trained on best-practice copywriting frameworks and integrates with popular "
            "marketing and project management tools to streamline content workflows."
        ),
        "features": [
            "AI-generated blog posts, ads, and social copy",
            "50+ content templates for every use case",
            "Brand voice training for consistent output",
            "Chrome extension for writing anywhere",
            "Integrates with Surfer SEO for optimised content",
        ],
        "short": "AI writing assistant used by 100,000+ marketing teams.",
    },
 
    "monday.com": {
        "name": "Monday.com",
        "emoji": "📅",
        "category": "Project Management",
        "plan": "Free for up to 2 seats",
        "url": "https://monday.com/",
        "description": (
            "Monday.com is a visual work operating system used by over 186,000 "
            "companies to manage projects, processes, and everyday work. Its colourful, "
            "flexible boards let teams build custom workflows without code. From simple "
            "task lists to complex project timelines, Monday.com adapts to how your team "
            "works — and connects to 200+ tools via Make.com automation."
        ),
        "features": [
            "Visual boards, timelines, and Gantt charts",
            "Custom automations and status notifications",
            "200+ integrations including Slack and HubSpot",
            "Dashboards with real-time reporting",
            "Templates for every industry and team size",
        ],
        "short": "Visual work OS used by 186,000+ companies to manage everything.",
    },
 
    "clickup": {
        "name": "ClickUp",
        "emoji": "🎯",
        "category": "Project Management",
        "plan": "Free forever",
        "url": "https://clickup.com/",
        "description": (
            "ClickUp is an all-in-one productivity platform designed to replace multiple "
            "separate tools with a single workspace. It combines tasks, docs, goals, chat, "
            "whiteboards, and time tracking in one place. With a generous free forever "
            "plan and 1,000+ integrations, ClickUp is one of the fastest-growing "
            "productivity tools among startups and agencies."
        ),
        "features": [
            "Tasks, subtasks, and checklists",
            "Docs, wikis, and collaborative notes",
            "Goals, OKRs, and time tracking",
            "15+ view types including timeline and mind map",
            "1,000+ integrations including Make.com",
        ],
        "short": "All-in-one productivity replacing tasks, docs, goals, and chat.",
    },
 
    "linear": {
        "name": "Linear",
        "emoji": "📐",
        "category": "Dev Project Management",
        "plan": "Free for up to 250 issues",
        "url": "https://linear.app/",
        "description": (
            "Linear is the project management tool built specifically for software "
            "engineering teams who demand speed and elegance. Unlike Jira, Linear is "
            "designed to be fast — keyboard-first, minimal, and opinionated. It is used "
            "by leading tech companies including Vercel, Raycast, and Retool for sprint "
            "planning, bug tracking, and roadmap management."
        ),
        "features": [
            "Blazing-fast keyboard-first interface",
            "Cycles (sprints) and roadmap planning",
            "GitHub and GitLab native integration",
            "Automatic issue creation from git commits",
            "SLAs, priorities, and triage workflows",
        ],
        "short": "The fast, elegant project tracker loved by top engineering teams.",
    },
 
    "typeform": {
        "name": "Typeform",
        "emoji": "📋",
        "category": "Forms & Surveys",
        "plan": "Free up to 10 responses/month",
        "url": "https://www.typeform.com/",
        "description": (
            "Typeform is the most beautiful online form and survey builder, used by "
            "over 150,000 businesses. Its conversational one-question-at-a-time format "
            "achieves completion rates up to 3× higher than traditional forms. It is "
            "the go-to choice for lead generation forms, NPS surveys, quizzes, and "
            "job applications — and connects to HubSpot, Mailchimp, and Make.com natively."
        ),
        "features": [
            "Conversational, one-question-at-a-time forms",
            "Logic jumps and conditional branching",
            "Native integrations with HubSpot, Mailchimp, Slack",
            "Custom branding and embed anywhere",
            "Analytics on completion rates and drop-offs",
        ],
        "short": "Beautiful forms with 3× higher completion rates than traditional forms.",
    },
 
    "calendly": {
        "name": "Calendly",
        "emoji": "📆",
        "category": "Scheduling",
        "plan": "Free plan available",
        "url": "https://calendly.com/",
        "description": (
            "Calendly is the world's most widely used online scheduling tool, with over "
            "20 million users. It eliminates back-and-forth emails by letting contacts "
            "book available time slots directly in your calendar. Sales teams use it "
            "for demos, recruiters for interviews, and consultants for client calls — "
            "all with automatic Zoom link generation and reminder emails."
        ),
        "features": [
            "Shareable booking links with availability rules",
            "Automatic Zoom and Google Meet link generation",
            "Round-robin and collective meeting types",
            "Automatic reminder and follow-up emails",
            "Connects to Salesforce, HubSpot, and Make.com",
        ],
        "short": "Online scheduling used by 20M+ users to eliminate booking back-and-forth.",
    },
 
    "chatgpt": {
        "name": "ChatGPT",
        "emoji": "🤖",
        "category": "AI Assistant",
        "plan": "Free plan available",
        "url": "https://chat.openai.com/",
        "description": (
            "ChatGPT by OpenAI is the world's most widely used AI assistant, with over "
            "100 million weekly active users. It can write, code, analyse, summarise, "
            "and reason across virtually any task. Via the OpenAI API, it connects to "
            "Make.com and other automation tools to power AI-driven workflows — from "
            "auto-generating Slack responses to summarising emails to enriching CRM records."
        ),
        "features": [
            "Conversational AI for any task",
            "GPT-4o with vision, code, and analysis",
            "OpenAI API for integration into any workflow",
            "Custom GPTs for specific business use cases",
            "Connects to Make.com via OpenAI API module",
        ],
        "short": "The world's most used AI assistant with 100M+ weekly users.",
    },
 
    "github": {
        "name": "GitHub",
        "emoji": "🐙",
        "category": "Dev & Code",
        "plan": "Free for public repos",
        "url": "https://github.com/signup",
        "description": (
            "GitHub is the world's largest developer platform, used by over 100 million "
            "developers to host, review, and collaborate on code. It is the centre of "
            "the open-source ecosystem and integrates tightly with Jira, Linear, Slack, "
            "and Asana to create fully automated software development pipelines — from "
            "commit to deployment to notification."
        ),
        "features": [
            "Code hosting with unlimited public repositories",
            "Pull requests, code reviews, and branch protection",
            "GitHub Actions for CI/CD automation",
            "Issues and project boards built in",
            "Connects to Jira, Slack, Linear, and Make.com",
        ],
        "short": "The world's largest developer platform used by 100M+ developers.",
    },
 
    "google-drive": {
        "name": "Google Drive",
        "emoji": "📁",
        "category": "Cloud Storage",
        "plan": "15 GB free",
        "url": "https://drive.google.com",
        "description": (
            "Google Drive is Google's cloud storage and file management service, offering "
            "15 GB free for every Google account. Teams use it to store, share, and "
            "collaborate on documents, spreadsheets, and presentations in real time. "
            "With Make.com, you can automate file creation, organisation, sharing, and "
            "notifications based on Drive activity."
        ),
        "features": [
            "15 GB free cloud storage",
            "Real-time collaboration on Docs, Sheets, Slides",
            "File sharing with granular permission controls",
            "Search across all file types including PDFs",
            "Integrates with Make.com for file automation",
        ],
        "short": "Google's cloud storage with 15 GB free and real-time collaboration.",
    },
 
    "activecampaign": {
        "name": "ActiveCampaign",
        "emoji": "📣",
        "category": "Email Marketing & CRM",
        "plan": "14-day free trial",
        "url": "https://www.activecampaign.com/",
        "description": (
            "ActiveCampaign is the leading customer experience automation platform, "
            "combining email marketing, marketing automation, and CRM in one tool. "
            "Used by 180,000+ businesses, it is especially powerful for e-commerce "
            "and B2B teams who want to build sophisticated automated customer journeys "
            "triggered by behaviour, tags, and lifecycle stage."
        ),
        "features": [
            "Email marketing with behaviour-based triggers",
            "Built-in CRM with deal pipeline",
            "Advanced automation with 500+ recipes",
            "Site tracking and event-based automation",
            "Integrates with Shopify, Stripe, and Make.com",
        ],
        "short": "Email automation + CRM used by 180,000+ businesses.",
    },
 
    "webflow": {
        "name": "Webflow",
        "emoji": "🌐",
        "category": "No-Code Web Builder",
        "plan": "Free starter plan",
        "url": "https://webflow.com/",
        "description": (
            "Webflow is the most powerful no-code website builder for designers and "
            "marketing teams. Unlike Wix or Squarespace, Webflow generates clean, "
            "production-ready code and supports full CMS capabilities. With Make.com "
            "integration, you can automate form submissions to your CRM, send Slack "
            "alerts for new leads, or trigger email campaigns from Webflow events."
        ),
        "features": [
            "Visual drag-and-drop design with clean HTML/CSS output",
            "Built-in CMS for blogs, portfolios, and directories",
            "Form builder with custom logic",
            "Hosting with global CDN included",
            "Connects to HubSpot, Mailchimp, and Make.com",
        ],
        "short": "No-code web builder that generates production-ready code.",
    },
 
    "notion-ai": {
        "name": "Notion AI",
        "emoji": "🧠",
        "category": "AI Productivity",
        "plan": "Add-on to Notion free plan",
        "url": "https://www.notion.so/product/ai",
        "description": (
            "Notion AI is the built-in AI assistant inside Notion, allowing teams to "
            "generate content, summarise documents, translate text, and extract action "
            "items — all without leaving their workspace. Unlike standalone AI tools, "
            "Notion AI has full context of your team's notes, projects, and databases, "
            "making it uniquely powerful for internal knowledge work."
        ),
        "features": [
            "AI writing and editing inside Notion pages",
            "Summarise meeting notes and documents instantly",
            "Auto-fill database properties with AI",
            "Translate content into 15+ languages",
            "Ask AI questions about your workspace content",
        ],
        "short": "AI assistant built into Notion with full workspace context.",
    },
    "claude": {
        "name": "Claude",
        "emoji": "🤖",
        "category": "AI Assistant",
        "plan": "Free plan available",
        "url": "https://claude.ai/",
        "description": (
            "Claude is Anthropic's flagship AI assistant, known for its exceptional "
            "reasoning, writing quality, and safety. Available via API, it powers "
            "automation workflows across thousands of businesses — from summarising "
            "emails to writing code to analysing documents. Claude connects to Slack, "
            "Notion, GitHub, and 38+ tools natively, and integrates with Make.com "
            "and n8n for custom workflow automation."
        ),
        "features": [
            "Exceptional writing, reasoning, and code generation",
            "Native integrations with Slack, Notion, GitHub via MCP",
            "API available for custom workflow integration",
            "Connects to Make.com and n8n for automation",
            "Claude Code for agentic software development",
        ],
        "short": "Anthropic's AI assistant with superior reasoning and writing quality.",
    },

    "gemini": {
        "name": "Gemini",
        "emoji": "✨",
        "category": "AI Assistant",
        "plan": "Free plan available",
        "url": "https://gemini.google.com/",
        "description": (
            "Gemini is Google's most capable AI model family, available in Ultra, Pro, "
            "and Flash variants. It is deeply integrated with Google Workspace, making "
            "it uniquely powerful for teams already using Google Sheets, Docs, Drive, "
            "and Gmail. Via the Gemini API, it powers automation workflows in Make.com "
            "and n8n, enabling AI-driven document processing, content generation, "
            "and intelligent data analysis at scale."
        ),
        "features": [
            "Deeply integrated with Google Workspace (Sheets, Docs, Drive)",
            "Gemini API for custom integrations and automation",
            "Multimodal: understands text, images, audio, and video",
            "Connects to Make.com, n8n, and Zapier",
            "Gemini CLI for developer terminal workflows",
        ],
        "short": "Google's AI model, deeply integrated with Google Workspace.",
    },

    "ollama": {
        "name": "Ollama",
        "emoji": "🦙",
        "category": "Local AI Runner",
        "plan": "100% free & open source",
        "url": "https://ollama.com/",
        "description": (
            "Ollama lets you run powerful large language models — including Llama 3, "
            "Mistral, Gemma, and DeepSeek — entirely on your own hardware, with zero "
            "API costs and complete data privacy. It exposes an OpenAI-compatible API "
            "so existing tools like n8n, Make.com, and LangChain connect to it "
            "instantly. In 2026, Ollama is the go-to choice for teams who need AI "
            "automation without cloud costs or data privacy concerns."
        ),
        "features": [
            "Run Llama 3, Mistral, DeepSeek, Gemma locally",
            "Zero API costs — runs on your own hardware",
            "OpenAI-compatible API endpoint",
            "Native n8n and LangChain integration",
            "Full data privacy — nothing leaves your network",
        ],
        "short": "Run AI models locally — zero cost, zero cloud, full privacy.",
    },

    "n8n": {
        "name": "n8n",
        "emoji": "🔄",
        "category": "Self-Hosted Automation",
        "plan": "Free self-hosted (open source)",
        "url": "https://n8n.io/",
        "description": (
            "n8n is the most powerful open-source workflow automation platform, "
            "combining 400+ app integrations with native AI agent support. Unlike "
            "Zapier or Make.com, n8n is self-hostable, giving you full control over "
            "your data. Its LangChain-based AI nodes let you build multi-step AI "
            "agent workflows that use local models (Ollama) or cloud APIs (Claude, "
            "Gemini, OpenAI) — making it the top choice for technical teams in 2026."
        ),
        "features": [
            "400+ integrations including all major SaaS tools",
            "Native AI agent nodes with LangChain support",
            "Connect to Ollama, Claude, Gemini, and OpenAI",
            "Self-hosted for full data privacy and control",
            "Visual workflow builder with custom JavaScript/Python",
        ],
        "short": "Open-source automation with native AI agents — self-hosted or cloud.",
    },

    "perplexity": {
        "name": "Perplexity",
        "emoji": "🔍",
        "category": "AI Search Engine",
        "plan": "Free plan available",
        "url": "https://www.perplexity.ai/",
        "description": (
            "Perplexity is the AI-native search engine that answers questions with "
            "real-time web citations, used by over 15 million people monthly. Unlike "
            "ChatGPT, Perplexity specialises in research and fact-checked answers. "
            "Via its API, teams automate competitive research, news monitoring, and "
            "knowledge base enrichment — piping real-time information into Notion, "
            "Slack, and Google Sheets automatically."
        ),
        "features": [
            "Real-time web search with cited answers",
            "Perplexity API for automated research workflows",
            "Deep Research for comprehensive reports",
            "Connects to Zapier, Make.com, and n8n via API",
            "Multi-model: Claude, GPT-4, and Sonar models",
        ],
        "short": "AI search engine with real-time web citations used by 15M+ monthly.",
    },

    "deepseek": {
        "name": "DeepSeek",
        "emoji": "🐳",
        "category": "AI Model",
        "plan": "Free API (very low cost)",
        "url": "https://www.deepseek.com/",
        "description": (
            "DeepSeek is the Chinese open-source AI model that shocked the industry "
            "in 2025 by matching GPT-4 performance at a fraction of the cost. Its API "
            "is dramatically cheaper than OpenAI or Anthropic, making it the preferred "
            "choice for high-volume automation workflows. DeepSeek R2 and V3 models "
            "run via Ollama locally or through the DeepSeek API, and integrate with "
            "n8n, Make.com, and LangChain for AI-powered pipelines."
        ),
        "features": [
            "GPT-4 level performance at significantly lower cost",
            "Run locally via Ollama for zero API costs",
            "DeepSeek API for cloud inference",
            "Integrates with n8n, Make.com, and LangChain",
            "Strong coding and reasoning capabilities",
        ],
        "short": "Open-source AI matching GPT-4 quality at a fraction of the cost.",
    },

    "midjourney": {
        "name": "Midjourney",
        "emoji": "🎨",
        "category": "AI Image Generation",
        "plan": "From $10/month",
        "url": "https://www.midjourney.com/",
        "description": (
            "Midjourney is the world's most popular AI image generation platform, "
            "used by over 16 million designers, marketers, and creators. It produces "
            "stunning, photorealistic and artistic images from text prompts. Via "
            "automation workflows, teams pipe Midjourney-generated images into Shopify "
            "product listings, social media schedulers, Notion design systems, and "
            "content management tools — eliminating hours of manual design work."
        ),
        "features": [
            "Industry-leading image quality and artistic styles",
            "Web interface and Discord bot integration",
            "API available for workflow automation",
            "Connect to Shopify, Notion, and Google Drive via Make.com",
            "Upscaling, variation, and inpainting capabilities",
        ],
        "short": "World's most popular AI image generator used by 16M+ creators.",
    },

    "stable-diffusion": {
        "name": "Stable Diffusion",
        "emoji": "🖼️",
        "category": "AI Image Generation",
        "plan": "Free & open source",
        "url": "https://stability.ai/",
        "description": (
            "Stable Diffusion is the leading open-source AI image generation model, "
            "allowing anyone to generate, edit, and remix images locally or via API "
            "with no usage limits. Run via Automatic1111 or ComfyUI on your own "
            "hardware, it integrates with n8n and Make.com for fully automated "
            "image generation pipelines — perfect for e-commerce product images, "
            "marketing assets, and content creation at scale."
        ),
        "features": [
            "100% free and open source",
            "Run locally with no usage costs",
            "Fine-tune on your own brand images",
            "ComfyUI and Automatic1111 interfaces",
            "Integrates with n8n and Make.com via HTTP API",
        ],
        "short": "Open-source AI image generation — run locally with zero usage costs.",
    },

    "grok": {
        "name": "Grok",
        "emoji": "🚀",
        "category": "AI Assistant",
        "plan": "Included with X Premium",
        "url": "https://grok.x.ai/",
        "description": (
            "Grok is xAI's (Elon Musk's AI company) flagship AI model, available via "
            "X (Twitter) and the Grok API. Grok 3 is competitive with GPT-4o and "
            "Claude Sonnet, with unique access to real-time X/Twitter data — making "
            "it especially powerful for social media monitoring, trend analysis, and "
            "brand intelligence automation workflows."
        ),
        "features": [
            "Real-time access to X/Twitter data",
            "Grok API for workflow integration",
            "Competitive reasoning and coding capabilities",
            "Integrates with Make.com, n8n, and Zapier via API",
            "DeepSearch for real-time web research",
        ],
        "short": "xAI's AI model with unique real-time X/Twitter data access.",
    },

    "mistral": {
        "name": "Mistral",
        "emoji": "💫",
        "category": "AI Model",
        "plan": "Free API tier available",
        "url": "https://mistral.ai/",
        "description": (
            "Mistral is the leading European AI company, producing high-performance "
            "open-weight models including Mistral 7B, Mixtral, and Mistral Large. "
            "Its models run via Ollama locally or through the Mistral API, and are "
            "especially popular for European businesses that need GDPR-compliant AI. "
            "Mistral integrates natively with n8n, LangChain, and Make.com for "
            "building private, cost-effective AI automation workflows."
        ),
        "features": [
            "Open-weight models — run locally via Ollama",
            "GDPR-compliant (European company, EU data centers)",
            "Mistral API for cloud inference",
            "Native LangChain and n8n support",
            "Le Chat: Mistral's consumer-facing chatbot",
        ],
        "short": "Europe's leading AI models — GDPR-compliant, open-weight, and fast.",
    },

    "langchain": {
        "name": "LangChain",
        "emoji": "🔗",
        "category": "AI Development Framework",
        "plan": "Open source (free)",
        "url": "https://www.langchain.com/",
        "description": (
            "LangChain is the world's most popular framework for building AI-powered "
            "applications, with over 100,000 GitHub stars. It provides the building "
            "blocks for connecting LLMs to databases, APIs, and tools — enabling RAG "
            "(Retrieval-Augmented Generation) pipelines, AI agents, and multi-step "
            "reasoning chains. LangChain integrates with every major LLM (Claude, "
            "Gemini, OpenAI, Ollama) and vector database (Pinecone, Supabase)."
        ),
        "features": [
            "Connect LLMs to any data source or API",
            "RAG pipelines for knowledge base Q&A",
            "AI agent frameworks with tool calling",
            "Supports Claude, Gemini, OpenAI, Ollama, and more",
            "LangSmith for tracing and monitoring AI apps",
        ],
        "short": "The most popular framework for building LLM-powered applications.",
    },

    "cursor": {
        "name": "Cursor",
        "emoji": "💻",
        "category": "AI Code Editor",
        "plan": "Free tier available",
        "url": "https://cursor.sh/",
        "description": (
            "Cursor is the AI-first code editor that has taken the developer world "
            "by storm in 2026, with over 3 million developers switching from VS Code. "
            "It combines a familiar coding environment with deeply integrated Claude "
            "and GPT-4 capabilities — allowing developers to write, debug, and "
            "refactor code in natural language. Cursor integrates with GitHub, Jira, "
            "Slack, and Linear to build complete AI-assisted development workflows."
        ),
        "features": [
            "AI pair programmer with codebase awareness",
            "Inline code generation and refactoring",
            "Natural language to code with full repo context",
            "Composer for multi-file AI changes",
            "Integrates with GitHub, Jira, Slack, and Linear",
        ],
        "short": "The AI code editor used by 3M+ developers, powered by Claude and GPT-4.",
    },

    "github-copilot": {
        "name": "GitHub Copilot",
        "emoji": "🤝",
        "category": "AI Code Assistant",
        "plan": "Free for students; $10/month",
        "url": "https://github.com/features/copilot",
        "description": (
            "GitHub Copilot is Microsoft's AI coding assistant, built directly into "
            "VS Code, JetBrains, and GitHub itself. With over 1.8 million paid "
            "subscribers and deep GitHub integration, it suggests entire functions, "
            "explains code, generates tests, and connects to Jira, Slack, and Linear "
            "to turn issue descriptions directly into working code."
        ),
        "features": [
            "AI code suggestions in VS Code, JetBrains, and GitHub",
            "Copilot Chat for explaining and debugging code",
            "Copilot Workspace for issue-to-code automation",
            "Integrates with Jira, Slack, and Linear",
            "Code review suggestions and security scanning",
        ],
        "short": "Microsoft's AI coding assistant with 1.8M+ subscribers.",
    },

    "flowise": {
        "name": "Flowise",
        "emoji": "🌊",
        "category": "Visual LLM App Builder",
        "plan": "Free & open source",
        "url": "https://flowiseai.com/",
        "description": (
            "Flowise is the open-source, drag-and-drop LLM app builder that lets "
            "non-developers build AI chatbots, RAG pipelines, and AI agents visually — "
            "no code required. Built on LangChain, it supports every major AI model "
            "and vector database. Teams use Flowise to build custom AI assistants "
            "connected to their Notion wikis, Airtable databases, and Slack channels, "
            "then deploy them as embeddable chat widgets or API endpoints."
        ),
        "features": [
            "Visual drag-and-drop LLM workflow builder",
            "Built on LangChain — supports all major LLMs",
            "RAG (Retrieval-Augmented Generation) pipelines",
            "Embed AI chat on any website",
            "Self-hosted or Flowise Cloud",
        ],
        "short": "Open-source drag-and-drop builder for AI chatbots and RAG pipelines.",
    },

    "telegram": {
        "name": "Telegram",
        "emoji": "✈️",
        "category": "Messaging",
        "plan": "Free (Telegram Premium optional)",
        "url": "https://telegram.org/",
        "description": (
            "Telegram is the fastest-growing messaging platform with over 900 million "
            "active users, especially popular in India, Russia, and Southeast Asia for "
            "both personal and business communication. Its Bot API is one of the most "
            "powerful in the messaging world, enabling teams to build automated bots "
            "that receive orders, send notifications, deliver AI responses, and sync "
            "data with CRMs and spreadsheets — all via Make.com or n8n."
        ),
        "features": [
            "900M+ active users — massive reach",
            "Powerful Bot API for automation",
            "Channels for broadcasting to unlimited subscribers",
            "Groups up to 200,000 members",
            "Connects to Make.com, n8n, and Zapier for automation",
        ],
        "short": "900M+ user messaging platform with a powerful Bot API for automation.",
    },

    "supabase": {
        "name": "Supabase",
        "emoji": "⚡",
        "category": "Backend & Database",
        "plan": "Free tier available",
        "url": "https://supabase.com/",
        "description": (
            "Supabase is the open-source Firebase alternative that combines a "
            "PostgreSQL database, authentication, real-time subscriptions, storage, "
            "and edge functions in one platform. It is the fastest-growing backend "
            "platform in 2026, especially among AI teams building RAG applications. "
            "Supabase's pgvector extension makes it the go-to vector store for "
            "LangChain, Claude, and Gemini-powered AI applications."
        ),
        "features": [
            "PostgreSQL database with pgvector for AI apps",
            "Built-in auth, storage, and real-time subscriptions",
            "Edge functions for serverless API logic",
            "Native LangChain and n8n integration",
            "Open-source — self-host or use Supabase Cloud",
        ],
        "short": "Open-source Firebase alternative — the go-to backend for AI applications.",
    },

    "pinecone": {
        "name": "Pinecone",
        "emoji": "🌲",
        "category": "Vector Database",
        "plan": "Free tier (100K vectors)",
        "url": "https://www.pinecone.io/",
        "description": (
            "Pinecone is the leading managed vector database, powering semantic search "
            "and Retrieval-Augmented Generation (RAG) applications for over 10,000 "
            "companies. It stores and retrieves AI-generated embeddings at scale, "
            "enabling LLM applications to search company knowledge bases, customer "
            "data, and documents with human-like understanding. Pinecone integrates "
            "natively with LangChain, Claude, Gemini, and n8n."
        ),
        "features": [
            "Managed vector database — no infrastructure to manage",
            "Sub-10ms similarity search at any scale",
            "Native LangChain, Claude, and OpenAI integration",
            "Serverless indexing with automatic scaling",
            "Free tier with 100,000 vectors",
        ],
        "short": "The leading vector database for AI search and RAG applications.",
    },

    "dify": {
        "name": "Dify",
        "emoji": "🔮",
        "category": "AI App Platform",
        "plan": "Free & open source",
        "url": "https://dify.ai/",
        "description": (
            "Dify is the fastest-growing open-source LLM application platform, "
            "combining prompt engineering, RAG pipelines, and AI agent workflows "
            "in a visual interface. With 40,000+ GitHub stars and support for every "
            "major LLM (Claude, Gemini, Ollama, DeepSeek), Dify lets teams build "
            "custom AI applications connected to their Slack, Notion, and database "
            "— deployable as APIs, web apps, or embeddable widgets."
        ),
        "features": [
            "Visual LLM app builder with prompt engineering tools",
            "RAG pipeline with document ingestion and retrieval",
            "AI agent workflows with tool calling",
            "Supports Claude, Gemini, Ollama, DeepSeek, and more",
            "40,000+ GitHub stars — fastest-growing AI platform",
        ],
        "short": "Open-source LLM app platform with 40,000+ stars — build AI apps visually.",
    },

    "luma-ai": {
        "name": "Luma AI",
        "emoji": "🎬",
        "category": "AI Video Generation",
        "plan": "Free tier available",
        "url": "https://lumalabs.ai/",
        "description": (
            "Luma AI (Dream Machine) is the leading AI video generation platform, "
            "creating photorealistic video clips from text prompts or images in seconds. "
            "Marketing teams use Luma AI to generate product demo videos, social media "
            "content, and animated graphics — then automate distribution to Google Drive, "
            "Notion, and social schedulers via Make.com and Zapier automation workflows."
        ),
        "features": [
            "Text-to-video and image-to-video generation",
            "Photorealistic video quality in seconds",
            "Luma API for workflow automation",
            "Connects to Google Drive, Notion, and Make.com",
            "Ray 2 model for cinematic quality output",
        ],
        "short": "Leading AI video generation platform — create videos from text in seconds.",
    },

    "whatsapp-business": {
        "name": "WhatsApp Business",
        "emoji": "💬",
        "category": "Business Messaging",
        "plan": "Free app; API pay-per-message",
        "url": "https://business.whatsapp.com/",
        "description": (
            "WhatsApp Business is the world's most popular business messaging platform, "
            "with over 200 million active business users globally. In India especially, "
            "WhatsApp is the primary channel for customer communication. The WhatsApp "
            "Business API integrates with HubSpot, Salesforce, and Shopify to automate "
            "order notifications, customer support, lead qualification, and marketing "
            "campaigns at scale via Make.com and Zapier."
        ),
        "features": [
            "200M+ active business users globally",
            "WhatsApp Business API for automation",
            "Message templates for marketing and notifications",
            "Integrates with HubSpot, Salesforce, and Shopify",
            "Connects to Make.com and Zapier for workflow automation",
        ],
        "short": "World's most used business messaging with 200M+ business accounts.",
    },

    "mysql": {
        "name": "MySQL",
        "emoji": "🗄️",
        "category": "Database",
        "plan": "Free & open source",
        "url": "https://www.mysql.com/",
        "description": (
            "MySQL is the world's most popular open-source relational database, "
            "powering over half of all websites including Facebook, Twitter, and "
            "YouTube. Integrating MySQL with automation tools like Make.com, n8n, "
            "and Zapier allows teams to automatically sync CRM data, update records "
            "from form submissions, export database reports to Google Sheets, "
            "and trigger Slack notifications based on database changes."
        ),
        "features": [
            "World's most popular open-source database",
            "Connects to Make.com, n8n, and Zapier natively",
            "Sync with Google Sheets, HubSpot, and Salesforce",
            "Trigger automations from database events",
            "Widely supported by all hosting providers",
        ],
        "short": "The world's most popular database — integrate with any SaaS tool.",
    },

    "postgresql": {
        "name": "PostgreSQL",
        "emoji": "🐘",
        "category": "Database",
        "plan": "Free & open source",
        "url": "https://www.postgresql.org/",
        "description": (
            "PostgreSQL is the world's most advanced open-source database, favoured "
            "by developers and AI teams for its powerful features including JSONB "
            "storage, full-text search, and the pgvector extension for AI embeddings. "
            "PostgreSQL integrates with n8n, Make.com, and LangChain to build "
            "automated data pipelines, AI-powered search, and real-time sync "
            "between databases and business applications."
        ),
        "features": [
            "Advanced SQL with JSONB and full-text search",
            "pgvector extension for AI embeddings and RAG",
            "Native n8n, Make.com, and LangChain support",
            "ACID compliant — production-grade reliability",
            "The database powering Supabase",
        ],
        "short": "The most advanced open-source database — powering modern AI applications.",
    },
    # ── Claude pairs ─────────────────────────────────────────────────
        "claude-slack": (
            "Bring Claude's AI directly into Slack to transform how your team works. "
            "Teams connect Claude to Slack to auto-summarise long threads, generate "
            "meeting agendas from channel discussions, draft professional replies, "
            "and build AI-powered support bots that answer questions using your "
            "company's knowledge base — all without leaving Slack."
        ),
        "claude-notion": (
            "Claude and Notion together create the ultimate AI-powered workspace. "
            "Auto-generate Notion pages from meeting transcripts, expand bullet notes "
            "into full documents with Claude, summarise long wiki pages on demand, "
            "and build a Notion-connected AI assistant that answers questions about "
            "your team's entire knowledge base using Claude's reasoning capabilities."
        ),
        "claude-github": (
            "Engineering teams using Claude and GitHub can automate the entire "
            "development workflow. Claude reviews pull requests and suggests improvements, "
            "generates code documentation from source files, creates GitHub issues from "
            "natural language descriptions, and summarises release notes from commit "
            "history — dramatically reducing the manual overhead of software development."
        ),
        "claude-google-sheets": (
            "Transform Google Sheets from a static spreadsheet into an intelligent "
            "data platform by connecting it to Claude. New rows trigger Claude to "
            "classify entries, generate summaries, translate content, extract key "
            "information, or enrich records with AI analysis — all written back to "
            "the sheet automatically. Turn any spreadsheet into a smart database."
        ),
        "claude-make.com": (
            "Make.com and Claude together unlock fully automated AI workflows without "
            "writing a single line of code. Build scenarios where Claude reads emails "
            "and routes them, generates personalised responses to form submissions, "
            "classifies support tickets by urgency, or writes product descriptions "
            "from SKU data — triggered automatically by events in any of Make.com's "
            "1,500+ connected apps."
        ),
        "claude-ollama": (
            "Running Claude alongside Ollama gives your team the best of both worlds: "
            "use Claude's industry-leading reasoning for complex, high-stakes tasks "
            "and route routine tasks (classification, summarisation, data extraction) "
            "through local Ollama models at zero cost. Build hybrid AI pipelines in "
            "n8n or LangChain that automatically select the right model for each task "
            "based on complexity, cost, and privacy requirements."
        ),

        # ── Gemini pairs ──────────────────────────────────────────────────
        "gemini-google-sheets": (
            "Gemini and Google Sheets are natively integrated via Google Workspace — "
            "the most powerful spreadsheet-AI combination available. Use Gemini to "
            "analyse trends in your data, generate charts from natural language, "
            "auto-populate cells with AI-generated content, and build custom Gemini "
            "functions that run AI analysis directly inside your spreadsheet formulas."
        ),
        "gemini-google-drive": (
            "Gemini's deepest integration is with Google Drive. Summarise any document "
            "in Drive with one click, extract key information from uploaded PDFs and "
            "presentations, and build automated pipelines that process new Drive files "
            "through Gemini for classification, translation, or content extraction — "
            "then store results back to Sheets or send summaries via Gmail."
        ),
        "gemini-slack": (
            "Bring Google's AI into your Slack workspace by connecting Gemini and Slack. "
            "Automatically summarise key Google Docs and Sheets updates to Slack "
            "channels, build a Gemini-powered Slack bot that searches your Drive and "
            "answers questions, or trigger Gemini analysis whenever new messages "
            "arrive in specific channels — keeping your team informed with AI insights."
        ),
        "gemini-ollama": (
            "Gemini and Ollama serve perfectly complementary roles in an AI automation "
            "stack. Route complex tasks requiring internet knowledge and reasoning to "
            "Gemini via API, while running high-volume routine tasks (text cleaning, "
            "classification, simple extraction) through Ollama's local models at zero "
            "cost. Build intelligent routing logic in n8n that makes this decision "
            "automatically based on task type and data sensitivity."
        ),

        # ── Ollama pairs ──────────────────────────────────────────────────
        "ollama-n8n": (
            "n8n and Ollama together create the most powerful free AI automation stack "
            "available in 2026. n8n's native Ollama nodes let you build multi-step AI "
            "agent workflows that run entirely on your own infrastructure — no cloud "
            "costs, no API limits, complete data privacy. Build email triage agents, "
            "document processing pipelines, and AI chatbots that scale to thousands "
            "of requests without a single dollar in API fees."
        ),
        "ollama-langchain": (
            "LangChain and Ollama are the foundation of every serious private AI "
            "application in 2026. LangChain provides the agent framework and RAG "
            "pipeline architecture; Ollama runs the local LLM. Together they enable "
            "teams to build sophisticated AI applications — semantic search over "
            "company documents, automated research pipelines, multi-step reasoning "
            "agents — all running on private infrastructure with zero API costs."
        ),
        "ollama-flowise": (
            "Flowise and Ollama are the go-to combo for teams who want to build AI "
            "chatbots and RAG pipelines without cloud costs or coding. Flowise provides "
            "the visual drag-and-drop interface; Ollama runs the LLM locally. Build a "
            "custom AI assistant connected to your company's documents in under an hour "
            "— then deploy it as a website chat widget or Slack bot."
        ),
        "deepseek-ollama": (
            "DeepSeek and Ollama together represent the most cost-effective AI "
            "automation stack available. Run DeepSeek R2 or V3 models locally via "
            "Ollama — getting near-frontier reasoning quality at literally zero per-"
            "token cost. Build automation workflows in n8n that use DeepSeek for "
            "complex analysis and route simpler tasks to faster, smaller models. "
            "Perfect for high-volume Indian businesses managing API cost carefully."
        ),

        # ── n8n pairs ─────────────────────────────────────────────────────
        "n8n-slack": (
            "n8n and Slack together replace an entire team of manual data handlers. "
            "Post automated Slack notifications from any database change, incoming "
            "webhook, or scheduled report. Build AI-powered Slack bots that use "
            "Ollama or Claude to answer team questions. Route customer messages from "
            "any source to the right Slack channel automatically. n8n's self-hosted "
            "nature means all your team data stays on your own infrastructure."
        ),
        "n8n-google-sheets": (
            "n8n and Google Sheets create a free, powerful data pipeline for teams "
            "of any size. Automatically append form submissions, CRM updates, and "
            "e-commerce orders to Google Sheets. Trigger n8n workflows from new "
            "Sheets rows. Build scheduled reports that pull data from multiple "
            "sources and write them to Sheets every morning. All without paying "
            "per-operation fees that add up in Zapier or Make.com."
        ),
        "n8n-telegram": (
            "n8n and Telegram together are the go-to combination for Indian and "
            "Southeast Asian businesses building customer communication automation. "
            "Build Telegram bots that receive orders, answer product questions using "
            "AI, notify teams about new leads, and send automated follow-up messages "
            "— all orchestrated by n8n workflows running on your own server at zero "
            "monthly cost beyond your VPS."
        ),

        # ── Telegram pairs ────────────────────────────────────────────────
        "telegram-whatsapp-business": (
            "Teams managing both Telegram and WhatsApp channels can unify their "
            "customer communication by connecting both to a single n8n or Make.com "
            "workflow. Route messages from both platforms to the right team in Slack, "
            "log all conversations to your CRM, and send automated replies using "
            "AI — giving customers a consistent experience regardless of which "
            "platform they use to reach you."
        ),
        "telegram-hubspot": (
            "Connect Telegram to HubSpot to turn every customer message into a CRM "
            "contact automatically. New Telegram bot interactions create HubSpot "
            "contacts with conversation history, deal stages update based on "
            "customer responses, and your sales team gets Slack notifications for "
            "high-value conversations — building a complete inbound pipeline "
            "from Telegram messages."
        ),
        "telegram-shopify": (
            "E-commerce stores using Telegram for customer communication can automate "
            "their entire support workflow. New Shopify orders trigger Telegram "
            "confirmation messages, shipping updates go out automatically, customer "
            "queries via Telegram bot create Shopify support tickets, and refund "
            "requests are processed and confirmed — all without manual intervention."
        ),
        "whatsapp-business-hubspot": (
            "The most powerful customer communication stack for Indian businesses: "
            "WhatsApp Business connected to HubSpot. Every WhatsApp message from a "
            "prospect automatically creates a HubSpot contact, conversation history "
            "is logged to the contact record, lead score updates based on engagement, "
            "and your sales team gets notified for hot leads — turning WhatsApp into "
            "a fully tracked revenue channel."
        ),
        "whatsapp-business-shopify": (
            "Connect WhatsApp Business to Shopify to deliver the customer experience "
            "Indian shoppers expect. Automatic order confirmations, shipping tracking "
            "updates, delivery notifications, and abandoned cart recovery messages — "
            "all sent directly to customers' WhatsApp. With 97%+ open rates vs 20% "
            "for email, WhatsApp automation dramatically increases customer satisfaction "
            "and repeat purchase rates."
        ),
        "whatsapp-business-make.com": (
            "Make.com is the most popular way to connect WhatsApp Business to your "
            "existing tools without coding. Build scenarios that send WhatsApp "
            "messages when a new HubSpot deal is created, when a Shopify order ships, "
            "when a Typeform is submitted, or on any schedule you define. Make.com's "
            "visual builder makes WhatsApp automation accessible to any business "
            "without a developer."
        ),

        # ── AI-to-AI pairs (Claude+Ollama style pairs users asked about) ──
        "claude-langchain": (
            "LangChain and Claude together are the gold standard for enterprise AI "
            "applications. LangChain's agent framework handles orchestration, tool "
            "calling, and RAG pipeline architecture, while Claude provides the best-"
            "in-class reasoning and writing quality. Build document Q&A systems, "
            "multi-step research agents, and customer support bots that combine "
            "LangChain's flexibility with Claude's intelligence."
        ),
        "gemini-langchain": (
            "Google's Gemini models integrate natively with LangChain via the "
            "langchain-google-genai package. Teams building RAG pipelines over Google "
            "Drive documents, Workspace data, or BigQuery datasets get the best "
            "results from combining Gemini's native Google data access with "
            "LangChain's retrieval and agent orchestration capabilities."
        ),
        "claude-pinecone": (
            "Claude and Pinecone together power the most intelligent knowledge base "
            "systems available in 2026. Pinecone stores vector embeddings of your "
            "documents, and Claude uses those embeddings to answer questions with "
            "precise citations — a system called RAG. Build internal wikis that "
            "actually answer questions, customer support bots that know your entire "
            "product, and research assistants that can query thousands of documents instantly."
        ),
        "langchain-pinecone": (
            "LangChain and Pinecone are the most popular RAG combination in the "
            "AI ecosystem. LangChain handles document ingestion, chunking, and "
            "embedding, while Pinecone stores and retrieves vectors with millisecond "
            "latency. Together they power production knowledge base applications used "
            "by thousands of companies — from customer support chatbots to internal "
            "document search systems at enterprise scale."
        ),
        "claude-supabase": (
            "Claude and Supabase together enable AI applications with persistent "
            "memory and real-time data access. Store conversation history and user "
            "preferences in Supabase PostgreSQL, use Supabase's pgvector for semantic "
            "search over your data, and build Claude-powered applications that remember "
            "context across sessions — creating AI assistants that genuinely learn "
            "your users' needs over time."
        ),
        "claude-cursor": (
            "Claude and Cursor create the most powerful AI-assisted development "
            "environment available. Cursor is already powered by Claude under the "
            "hood, but connecting them via the Claude API unlocks custom coding "
            "agents, automated code review workflows, and AI-powered documentation "
            "generation that understands your entire codebase — accelerating "
            "development velocity by 2-3× according to independent benchmarks."
        ),
        
}

# ================================================================
# HELPER FUNCTION — get tool data by slug name
# Add this function to main.py
# ================================================================

def get_tool_info(tool_name_raw: str) -> dict:
    """
    Given a raw tool name from the DB (e.g. 'Slack', 'HubSpot', 'Google Sheets'),
    return the tool description dict from TOOL_DATA.
    Falls back to a generic dict if tool not found.
    """
    key = tool_name_raw.lower().replace(" ", "-").replace(".", "")
    data = TOOL_DATA.get(key)
    if data:
        return data
    # Generic fallback for any tool not in the dict
    return {
        "name": tool_name_raw,
        "emoji": "🔧",
        "category": "SaaS Tool",
        "plan": "Free plan available",
        "url": f"https://www.google.com/search?q={tool_name_raw.replace(' ', '+')}+pricing",
        "description": (
            f"{tool_name_raw} is a popular SaaS tool used by thousands of teams "
            f"to improve productivity and automate workflows. Connect it with other tools "
            f"using Make.com to save time and reduce manual work."
        ),
        "features": [
            f"Core {tool_name_raw} features",
            "Integrates with Make.com for automation",
            "Cloud-based — access from anywhere",
            "Free plan or trial available",
        ],
        "short": f"Connect {tool_name_raw} with Make.com to automate your workflows.",
    }


def get_together_description(tool_a: str, tool_b: str) -> str:
    """
    Returns a 'better together' description for tool pair.
    Extend this dict with more pairs as needed.
    """
    pair_key = f"{tool_a.lower()}-{tool_b.lower()}"
    pairs = {
        "slack-notion": (
            "When Slack messages are automatically saved to Notion, your team's best "
            "ideas stop getting lost in threads. Connect them to auto-create Notion pages "
            "from Slack messages, send Notion task updates to Slack channels, and run "
            "daily standup summaries — all without switching tabs."
        ),
        "slack-hubspot": (
            "Sales teams using both Slack and HubSpot can close deals faster by "
            "automating their handoffs. Get instant Slack notifications when a HubSpot "
            "deal moves stage, auto-log Slack conversations to HubSpot contact records, "
            "or alert your sales channel whenever a new lead comes in."
        ),
        "slack-salesforce": (
            "Enterprise sales teams win more by connecting Slack's speed with "
            "Salesforce's depth. Auto-post Salesforce opportunity updates to Slack, "
            "alert your team on high-value leads, or log Slack discussions directly "
            "to Salesforce activity records — keeping everyone aligned without manual updates."
        ),
        "slack-jira": (
            "Engineering teams using Slack and Jira can eliminate status meetings "
            "by automating their updates. Get Slack notifications for new Jira bugs, "
            "post sprint progress to channels, or let developers update Jira tickets "
            "directly from Slack — no context switching needed."
        ),
        "slack-trello": (
            "Keep your whole team aligned by connecting Slack and Trello. Automatically "
            "post Trello card updates to Slack channels, create Trello cards from Slack "
            "messages, or get daily board summaries delivered to your team channel."
        ),
        "slack-asana": (
            "Stop asking 'what's the status?' Connect Slack and Asana to get automatic "
            "Slack notifications when Asana tasks are completed, create Asana tasks "
            "from Slack messages, and send daily work summaries to your team channel."
        ),
        "slack-zoom": (
            "Automate your meeting workflows by connecting Slack and Zoom. Start Zoom "
            "meetings from Slack with a slash command, post meeting summaries and "
            "recordings back to Slack channels, and send automatic reminders before "
            "upcoming calls."
        ),
        "slack-mailchimp": (
            "Marketing teams using Slack and Mailchimp can stay on top of campaign "
            "performance without logging into dashboards. Get Slack alerts when "
            "campaigns are sent, when open rates cross a threshold, or when new "
            "subscribers sign up — all automatically."
        ),
        "slack-shopify": (
            "E-commerce teams love connecting Slack and Shopify for real-time order "
            "visibility. Get instant Slack notifications for new orders, refund requests, "
            "and low-stock alerts — so your team can respond fast without constantly "
            "checking the Shopify dashboard."
        ),
        "slack-stripe": (
            "Get real-time payment visibility by connecting Slack and Stripe. Receive "
            "instant Slack notifications for new payments, failed charges, and new "
            "customer subscriptions — keeping your team informed without manually "
            "monitoring the Stripe dashboard."
        ),
        "notion-hubspot": (
            "Content and sales teams working across Notion and HubSpot can keep their "
            "data perfectly synced. Auto-create Notion pages from new HubSpot contacts, "
            "update your Notion CRM tracker when deal stages change, or log meeting "
            "notes from Notion directly into HubSpot contact records."
        ),
        "hubspot-salesforce": (
            "Connecting HubSpot and Salesforce ensures your marketing and sales data "
            "stays perfectly in sync. Automatically sync contacts, deals, and "
            "company data between both platforms — eliminating duplicate entries, "
            "reducing manual work, and giving every team a single source of truth."
        ),
        "shopify-mailchimp": (
            "Every new Shopify customer can automatically join your Mailchimp list, "
            "tagged by product category and purchase history. This means your "
            "post-purchase email flows, abandoned cart sequences, and VIP campaigns "
            "start working the moment someone buys — zero manual work required."
        ),
        "shopify-stripe": (
            "For stores using both Shopify and Stripe, automation keeps your payment "
            "data perfectly reconciled. Auto-create Stripe invoices for Shopify orders, "
            "sync refund data across both platforms, and get instant notifications "
            "for failed payment attempts."
        ),
        # ── Jasper pairs ──────────────────────────────────────────
        "slack-jasper": (
            "Content teams using Slack and Jasper can build a fully automated content "
            "pipeline. When a content brief is approved in Slack, trigger Jasper to "
            "generate the first draft automatically. Or post Jasper's AI-generated "
            "content suggestions directly into a Slack channel for team review — "
            "cutting your content production time in half."
        ),
        "notion-jasper": (
            "Connecting Notion and Jasper creates a seamless AI-powered content workspace. "
            "Auto-save Jasper-generated drafts as new Notion pages, trigger Jasper to "
            "expand Notion bullet points into full articles, or use Notion as your "
            "content calendar with Jasper automatically populating drafts on schedule."
        ),
        "hubspot-jasper": (
            "Marketing teams can supercharge HubSpot with Jasper's AI writing. "
            "Auto-generate personalised email sequences for new HubSpot contacts, "
            "create Jasper blog drafts from HubSpot campaign briefs, or trigger "
            "Jasper to write follow-up sequences when HubSpot deals reach a new stage."
        ),
 
        # ── Monday.com pairs ──────────────────────────────────────
        "slack-monday.com": (
            "Keep your Slack team and Monday.com boards perfectly in sync. Get instant "
            "Slack notifications when Monday tasks change status, create Monday items "
            "from Slack messages with a single emoji reaction, or post daily Monday "
            "board summaries to your team channel automatically."
        ),
        "asana-monday.com": (
            "Teams migrating between Asana and Monday.com, or using both simultaneously, "
            "can sync tasks across platforms automatically. New Asana tasks can create "
            "Monday items, status updates can flow both ways, and completion in one "
            "platform can trigger updates in the other — zero duplication."
        ),
        "hubspot-monday.com": (
            "Sales and marketing teams using HubSpot and Monday.com can automate their "
            "entire client lifecycle. New HubSpot deals automatically create Monday "
            "project boards, deal stage changes update Monday task statuses, and won "
            "deals trigger Monday onboarding workflows instantly."
        ),
 
        # ── ClickUp pairs ─────────────────────────────────────────
        "slack-clickup": (
            "Connect Slack and ClickUp to eliminate status update meetings. Get instant "
            "Slack notifications when ClickUp tasks are completed or overdue, create "
            "ClickUp tasks from Slack messages with a single command, and send daily "
            "ClickUp sprint summaries to your team channel automatically."
        ),
        "asana-clickup": (
            "Teams running both Asana and ClickUp can sync work across both platforms "
            "without manual copying. New Asana projects create ClickUp lists, task "
            "completions sync both ways, and due date changes update in real time — "
            "so every team member sees the same status regardless of which tool they use."
        ),
 
        # ── Linear pairs ──────────────────────────────────────────
        "slack-linear": (
            "Engineering teams using Slack and Linear can run fully automated sprint "
            "workflows. Get Slack notifications for new Linear bugs, post daily issue "
            "summaries to engineering channels, and allow developers to create or update "
            "Linear issues directly from Slack — no context switching required."
        ),
        "jira-linear": (
            "Teams migrating from Jira to Linear, or using both tools across departments, "
            "can sync issues automatically. New Jira epics create Linear projects, "
            "bug reports flow both ways, and sprint completions update status in both "
            "systems — keeping engineering and product always aligned."
        ),
        "github-linear": (
            "Connecting GitHub and Linear creates a fully automated development workflow. "
            "New GitHub pull requests automatically create or update Linear issues, "
            "merged PRs mark Linear tickets as done, and git commit messages reference "
            "Linear issue IDs to keep everything traceable and in sync."
        ),
 
        # ── Typeform pairs ────────────────────────────────────────
        "slack-typeform": (
            "When a new Typeform response comes in, instantly notify your Slack channel "
            "with the key details. Perfect for lead capture forms, NPS surveys, and "
            "support requests — your team sees responses in real time without logging "
            "into Typeform, so they can act fast on every submission."
        ),
        "hubspot-typeform": (
            "The most powerful use of Typeform and HubSpot together: every form "
            "submission automatically creates or updates a HubSpot contact, tags them "
            "with their survey answers, and triggers the right email nurture sequence. "
            "Your lead capture becomes a fully automated CRM pipeline."
        ),
        "google-sheets-typeform": (
            "Automatically log every Typeform response into a Google Sheet for easy "
            "analysis, reporting, and sharing with stakeholders. Set up once and every "
            "new response appears instantly as a new row — no exports, no manual work, "
            "always up to date."
        ),
        "activecampaign-typeform": (
            "When someone completes a Typeform survey, automatically add them to an "
            "ActiveCampaign list, tag them based on their answers, and trigger the "
            "right automation sequence. Build highly personalised email journeys based "
            "on exactly what your leads told you — without any manual segmentation."
        ),
 
        # ── Calendly pairs ────────────────────────────────────────
        "slack-calendly": (
            "Get instant Slack notifications when someone books a meeting via Calendly. "
            "Alert the right Slack channel or DM the assigned team member with the "
            "booking details, so your team is always prepared — no more missed "
            "meetings or last-minute scrambles to check the calendar."
        ),
        "hubspot-calendly": (
            "The ultimate sales workflow: when a prospect books a Calendly call, "
            "automatically create or update a HubSpot contact, log the meeting activity, "
            "and enrol them in a pre-meeting email sequence. Your CRM is always current "
            "without a single click from your sales team."
        ),
        "zoom-calendly": (
            "Calendly and Zoom are already connected natively, but with Make.com you "
            "can go further. Auto-send personalised prep materials before the meeting, "
            "save the Zoom recording link to your CRM after the call, and trigger "
            "follow-up emails based on whether the meeting actually happened."
        ),
        "salesforce-calendly": (
            "Enterprise sales teams using Salesforce and Calendly can automate their "
            "entire booking-to-pipeline workflow. Calendly bookings automatically create "
            "Salesforce leads, meeting notes sync to contact activity logs, and no-shows "
            "trigger automated re-engagement sequences — all without manual data entry."
        ),
 
        # ── ChatGPT pairs ─────────────────────────────────────────
        "slack-chatgpt": (
            "Build an AI assistant inside Slack using ChatGPT and Make.com. Messages "
            "sent to a specific channel or with a trigger word are automatically processed "
            "by ChatGPT, which generates intelligent replies, summaries, or action items "
            "— posted back to Slack in seconds. Your team gets AI superpowers without "
            "leaving their daily workflow."
        ),
        "notion-chatgpt": (
            "Connect Notion and ChatGPT to build an AI-powered knowledge system. "
            "Auto-generate Notion page summaries with ChatGPT, expand bullet-point "
            "meeting notes into full action plans, or trigger ChatGPT to research and "
            "enrich new Notion database entries automatically."
        ),
        "hubspot-chatgpt": (
            "Marketing and sales teams can use ChatGPT to enrich every HubSpot contact. "
            "When a new lead comes in, ChatGPT researches their company, generates a "
            "personalised outreach draft, and adds both to HubSpot automatically — "
            "giving your sales team a head start on every new prospect."
        ),
        "google-sheets-chatgpt": (
            "Use ChatGPT to process, classify, and enrich Google Sheets data automatically. "
            "New rows trigger ChatGPT to categorise entries, generate summaries, or "
            "translate content — with the AI's output written back to the sheet "
            "instantly. Turn static spreadsheets into intelligent, self-updating documents."
        ),
        "shopify-chatgpt": (
            "E-commerce stores can use ChatGPT to automate customer communication at "
            "scale. New Shopify orders trigger ChatGPT to generate personalised thank-you "
            "emails, refund requests get AI-drafted resolution responses, and product "
            "reviews are automatically analysed for sentiment and key themes."
        ),
 
        # ── GitHub pairs ──────────────────────────────────────────
        "slack-github": (
            "Engineering teams using Slack and GitHub can automate their entire "
            "development communication pipeline. Get Slack notifications for new pull "
            "requests, failed CI checks, and merged branches — tagged to the right "
            "channel. Developers stay informed without constantly checking GitHub."
        ),
        "jira-github": (
            "Connect Jira and GitHub to create a single source of truth for your "
            "engineering workflow. New GitHub pull requests automatically update linked "
            "Jira tickets, merged PRs move tickets to Done, and failed builds create "
            "new Jira bug reports — all automatically, no manual status updates needed."
        ),
        "notion-github": (
            "Use Notion as your engineering wiki and GitHub as your code repository — "
            "then connect them. New GitHub releases auto-create Notion changelog entries, "
            "open issues create Notion task cards, and merged PRs update your Notion "
            "project tracker. Documentation and code stay in sync effortlessly."
        ),
 
        # ── Google Drive pairs ─────────────────────────────────────
        "slack-google-drive": (
            "When a new file is added to a Google Drive folder, automatically notify "
            "the relevant Slack channel with a direct link. Perfect for shared client "
            "folders, design assets, and reporting dashboards — your team always knows "
            "when new files are ready without manually checking Drive."
        ),
        "notion-google-drive": (
            "Keep your Notion workspace and Google Drive perfectly aligned. New Notion "
            "pages can create corresponding Drive folders, Google Doc links can be "
            "auto-embedded in Notion databases, and Drive file updates can trigger "
            "Notion status changes — one seamless document management system."
        ),
        "zoom-google-drive": (
            "Automatically save Zoom meeting recordings to a specific Google Drive folder "
            "organised by date, team, or client. Every recording gets a Drive link that "
            "is automatically shared with the meeting participants — no more hunting "
            "through email for recording links."
        ),
 
        # ── ActiveCampaign pairs ───────────────────────────────────
        "hubspot-activecampaign": (
            "Teams using both HubSpot and ActiveCampaign can sync their contacts and "
            "campaign data automatically. New HubSpot leads are added to ActiveCampaign "
            "with their lifecycle stage and tags, email engagement from ActiveCampaign "
            "updates HubSpot contact scores, and deal stage changes trigger new "
            "ActiveCampaign automation sequences."
        ),
        "shopify-activecampaign": (
            "E-commerce brands using Shopify and ActiveCampaign can automate their "
            "entire customer lifecycle. New Shopify customers join the right "
            "ActiveCampaign list, abandoned carts trigger recovery sequences, repeat "
            "buyers get VIP tag and upgrade automation, and post-purchase review "
            "requests go out automatically — all hands-free."
        ),
        "stripe-activecampaign": (
            "SaaS and subscription businesses using Stripe and ActiveCampaign can "
            "automate every billing event. New Stripe subscribers trigger onboarding "
            "sequences, failed payments send dunning emails, and cancellations start "
            "win-back campaigns — all automatically based on real payment data."
        ),
 
        # ── Webflow pairs ──────────────────────────────────────────
        "hubspot-webflow": (
            "Connect your Webflow site to HubSpot to turn every form submission into "
            "a CRM contact instantly. Webflow form responses create HubSpot contacts, "
            "trigger lead nurture sequences, and notify your sales team via Slack — "
            "building a complete inbound marketing pipeline from your website."
        ),
        "mailchimp-webflow": (
            "Every visitor who fills out a Webflow form can automatically join the "
            "right Mailchimp audience, tagged with the page they came from. This means "
            "your email campaigns are always sending to properly segmented, up-to-date "
            "lists — with zero manual list management required."
        ),
        "slack-webflow": (
            "Get a Slack notification every time someone submits a form on your Webflow "
            "site. New contact requests, job applications, and demo bookings appear "
            "instantly in the right Slack channel — so your team can respond within "
            "minutes, not hours."
        ),
    }
    result = pairs.get(pair_key) or pairs.get(f"{tool_b.lower()}-{tool_a.lower()}")
    if result:
        return result
    return (
        f"Connecting {tool_a} and {tool_b} with Make.com eliminates the manual work "
        f"of copying data between the two tools. Automate data syncing, trigger actions "
        f"in {tool_b} when events happen in {tool_a}, and build workflows that save "
        f"your team hours every week — all without writing any code."
    )

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
 

# Initialize Templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Configure Gemini API
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- DATABASE CONNECTION ---
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set DATABASE_URL in the .env file next to main.py or export it in the shell."
        )

    try:
        conn = psycopg2.connect(db_url)
    except psycopg2.OperationalError as exc:
        raise RuntimeError(
            f"Database connection failed for DATABASE_URL host: {db_url}. "
            f"Original error: {exc}"
        ) from exc

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
                <p style="font-size:12px;color:#999;text-align:center;margin-top:30px;">
                You're receiving this because you subscribed at integration-directory.com.<br>
                <a href="https://integration-directory.com/unsubscribe?email={sub['email']}&token={generate_unsubscribe_token(sub['email'])}" style="color:#999;">Unsubscribe</a>
                · Integration Directory · contact@integration-directory.com
                </p>
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
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    
    # Pass dynamic back routing to the HTML template
    return templates.TemplateResponse("blog_post.html", {
        "request": request, 
        "post": post,
        "back_url": "/blog",
        "back_text": "Techie Blog"
    })

# --- 2. THE AI AGENT ENDPOINT (The Automated Writer) ---
# Posts up to 4 blog posts per call. Rate limit: 4 per 6-hour window.
# Schedule this cron 4x/day: 06:00, 10:00, 14:00, 18:00 IST

@app.get("/api/agent/daily-blog")
async def run_ai_agent(secret: str, background_tasks: BackgroundTasks, count: int = 4):
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    count = max(1, min(count, 4))

    conn, cursor = get_db_connection()

    # Rate limit: max 4 blog posts per 6-hour window
    cursor.execute(
        "SELECT COUNT(*) as c FROM blog_posts WHERE published_date >= NOW() - INTERVAL '6 hours'"
    )
    posts_recent = cursor.fetchone()["c"]
    if posts_recent >= 4:
        conn.close()
        return {"status": "Skipped", "reason": f"Already posted {posts_recent} blog posts in the last 6 hours."}

    slots_remaining = 4 - posts_recent
    to_post = min(count, slots_remaining)

    # Get existing titles to avoid duplicates
    cursor.execute("SELECT title FROM blog_posts")
    existing = {row["title"].lower() for row in cursor.fetchall()}

    # Topic pool — covers popular SaaS integrations and automation tutorials
    BLOG_TOPICS = [
        "5 Make.com automations every Shopify store owner should set up",
        "How to connect HubSpot and Slack automatically — no-code guide",
        "The best free Zapier alternatives for Indian startups in 2026",
        "How to automate your Google Sheets with Make.com step by step",
        "Notion + Slack integration: the complete 2026 setup guide",
        "How to send automatic WhatsApp messages using Make.com",
        "Top 7 automations to save 5 hours per week for remote teams",
        "How to build a no-code lead capture pipeline with Airtable and Gmail",
        "Make.com vs Zapier: which is better for Indian businesses in 2026?",
        "How to automate Trello card creation from Gmail emails",
        "The complete guide to automating customer onboarding with SaaS tools",
        "How to sync WooCommerce orders to Google Sheets automatically",
        "5 automations every freelancer should set up on Make.com",
        "How to build an AI-powered email responder using Make.com",
        "Automate your invoicing: connect Stripe, Notion and Gmail in one workflow",
        "How to create automatic Jira tickets from Slack messages",
        "How to auto-post new blog content to LinkedIn using Make.com",
        "The best Make.com templates for e-commerce businesses in 2026",
        "How to automate Salesforce data entry from Google Forms",
        "Setting up a no-code CRM pipeline: HubSpot + Notion + Gmail guide",
    ]
    available = [t for t in BLOG_TOPICS if t.lower() not in existing]
    if len(available) < to_post:
        # Pull random integration pairs from DB for extra variety
        cursor.execute("SELECT tool_a, tool_b FROM integrations ORDER BY RANDOM() LIMIT 10")
        pairs = cursor.fetchall()
        available += [f"How to Connect {r['tool_a']} and {r['tool_b']}: Step-by-Step Guide (2026)" for r in pairs]
    random.shuffle(available)

    posted = []
    errors = []

    for i in range(to_post):
        topic = available[i]

        # Check if it's an integration pair topic or a tutorial topic
        is_pair = topic.startswith("How to Connect ") and " and " in topic
        if is_pair:
            parts = topic.replace("How to Connect ", "").split(": ")[0]
            tool_a, tool_b = parts.split(" and ")[0], parts.split(" and ")[1]
            prompt = f"""You are a B2B tech writer for integration-directory.com.
Write a 900-word SEO blog post: "How to Connect {tool_a} and {tool_b}: Step-by-Step Guide (2026)"
Wrap the title in <h1>. Use <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <div> HTML only. No markdown.
Structure: Why connect → What you need → Step-by-step (numbered) → Popular use cases (3 bullets) → Time savings estimate.
Include this CTA after the steps:
<div style="background:#eff6ff;border-left:4px solid #2563eb;padding:16px;border-radius:6px;margin:24px 0;">
<strong>Ready to set this up?</strong> Build this automation free on Make.com.<br>
<a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored" style="color:#2563eb;font-weight:bold;">Start free on Make.com →</a>
</div>
End with FAQ: 3 questions in <h3> and answers in <p>.
Add author line at the end: <p style="font-size:13px;color:#6b7280;margin-top:32px;border-top:1px solid #e5e7eb;padding-top:12px;">Written by <strong>Vangari Sai Sampath</strong>, Automation Specialist · Integration Directory · Hyderabad, India</p>
NO hype words: unleash, nexus, supercharge, revolutionize, game-changer. Plain business language only."""
        else:
            prompt = f"""You are an expert automation consultant writing practical tutorials for integration-directory.com.
Write a comprehensive 800-word tutorial blog post on this topic: "{topic}"
The audience is non-technical business owners, freelancers, and operations managers in India and globally.
Wrap the title in <h1>. Use <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <div> HTML only. No markdown.
Structure: Introduction (2 paragraphs) → Why this matters → Step-by-step guide (numbered) → Pro tips → CTA → FAQ (3 questions).
Include this exact CTA:
<div style="background:#f0f4ff;padding:16px;border-radius:8px;margin:20px 0;">
<strong>Try this automation free →</strong> <a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored">Start on Make.com</a> — 1,000 free operations/month, no credit card needed.
</div>
Add author line at the end: <p style="font-size:13px;color:#6b7280;margin-top:32px;border-top:1px solid #e5e7eb;padding-top:12px;">Written by <strong>Vangari Sai Sampath</strong>, Automation Specialist · Integration Directory · Hyderabad, India</p>
Be specific, practical, action-oriented. NO hype words. Plain language."""

        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            html_content = response.text.replace("```html", "").replace("```", "").strip()
            title_match = re.search(r"<h1>(.*?)</h1>", html_content)
            title = title_match.group(1) if title_match else topic
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80]

            cursor.execute(
                "INSERT INTO blog_posts (title, slug, content) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
                (title, slug, html_content),
            )
            conn.commit()
            posted.append(title)
            # Send newsletter only for the first post of the batch
            if i == 0:
                background_tasks.add_task(send_newsletter, title, html_content)
        except Exception as e:
            errors.append(str(e))
            print(f"Blog Agent Error (post {i+1}): {e}")

    conn.close()
    return {"status": "Success", "posted_count": len(posted), "posted": posted, "errors": errors or None}

# --- 3. Lead Capture Route ---

@app.post("/request-integration")
async def request_integration(
    email: str = Form(...),
    tools: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    conn, cursor = get_db_connection()
    cursor.execute('INSERT INTO leads (email, requested_tools) VALUES (%s, %s)', (email, tools))
    conn.commit()
    conn.close()
    background_tasks.add_task(send_integration_request_emails, email, tools)
    return {"message": "Success! We will notify you when this integration is live."}


def send_integration_request_emails(user_email: str, tools: str):
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    if not sender_email or not sender_password:
        return
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # 1. Notify yourself (admin)
        admin_msg = MIMEMultipart()
        admin_msg['From'] = sender_email
        admin_msg['To'] = sender_email
        admin_msg['Subject'] = f"New Integration Request: {tools}"
        admin_msg.attach(MIMEText(f"<p>New request from: <b>{user_email}</b><br>Tools: <b>{tools}</b></p>", 'html'))
        server.send_message(admin_msg)

        # 2. Confirmation to user
        user_msg = MIMEMultipart()
        user_msg['From'] = f"Integration Directory <{sender_email}>"
        user_msg['To'] = user_email
        user_msg['Subject'] = "We received your integration request! ✅"
        user_body = f"""
<html><body style="font-family:sans-serif;padding:20px;color:#333;">
  <h2 style="color:#2563eb;">We got your request! 🙌</h2>
  <p>Thanks for reaching out. You requested: <strong>{tools}</strong></p>
  <p>Our team reviews all requests. We'll email you when this integration guide is live.</p>
  <a href="https://integration-directory.com" style="background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:6px;">Browse existing integrations →</a>
  <p style="font-size:12px;color:#999;margin-top:30px;">Integration Directory · Hyderabad, India</p>
</body></html>"""
        user_msg.attach(MIMEText(user_body, 'html'))
        server.send_message(user_msg)
        server.quit()
    except Exception as e:
        print(f"Integration request email error: {e}")

# --- NEW: Newsletter Subscription Route ---

# In main.py — replace your /subscribe route with this:

@app.post("/subscribe")
async def subscribe_newsletter(email: str = Form(...), background_tasks: BackgroundTasks = None):
    conn, cursor = get_db_connection()
    try:
        result = cursor.execute(
            'INSERT INTO newsletter_subscribers (email) VALUES (%s) ON CONFLICT (email) DO NOTHING RETURNING email',
            (email.strip().lower(),)
        )
        conn.commit()
        # Only send welcome if they were newly inserted (not a duplicate)
        inserted = cursor.fetchone()
        if inserted:
            background_tasks.add_task(send_welcome_email, email.strip().lower())
    except Exception as e:
        print(f"Subscription Error: {e}")
    finally:
        conn.close()
    return {"message": f"Success! {email} has been added to the Techie Newsletter."}


def send_welcome_email(email: str):
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    if not sender_email or not sender_password:
        print("SMTP credentials missing.")
        return
    token = generate_unsubscribe_token(email)
    unsubscribe_url = f"https://integration-directory.com/unsubscribe?email={email}&token={token}"
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Integration Directory <{sender_email}>"
        msg['To'] = email
        msg['Subject'] = "Welcome to The Techie Newsletter! 🚀"
        body = f"""
<html><body style="font-family: sans-serif; color: #333; line-height: 1.6;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #2563eb;">Welcome to The Techie Newsletter! 🎉</h2>
  <p>Hey Techie,</p>
  <p>You're now subscribed to the <strong>Integration Directory Newsletter</strong> — your weekly source for AI workflows, SaaS automation tips, and the latest in tech.</p>
  <p>We'll send you updates whenever we publish new guides or news. No spam, ever.</p>
  <hr style="border: 1px solid #eee; margin: 20px 0;">
  <p>In the meantime, explore the directory:</p>
  <a href="https://integration-directory.com" style="background:#2563eb;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold;">Browse Integrations →</a>
  <hr style="border: 1px solid #eee; margin: 20px 0;">
  <p style="font-size:12px;color:#999;">
    You subscribed at integration-directory.com. To unsubscribe,
    <a href="{unsubscribe_url}" style="color:#999;">click here</a>.
    <br>Integration Directory · contact@integration-directory.com · Hyderabad, India
  </p>
</div>
</body></html>
"""
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Welcome email sent to {email}")
    except Exception as e:
        print(f"Welcome email failed: {e}")


import hashlib

def generate_unsubscribe_token(email: str) -> str:
    secret = os.environ.get("UNSUBSCRIBE_SECRET", "integration-directory-secret-2026")
    return hashlib.sha256(f"{email}{secret}".encode()).hexdigest()[:32]

@app.get("/unsubscribe")
async def unsubscribe_page(request: Request, email: str = "", token: str = ""):
    """Show confirmation page — does NOT delete yet, just confirms intent."""
    if not email:
        return templates.TemplateResponse("unsubscribe.html", {
            "request": request, "email": "", "token": "",
            "valid": False, "success": False, "error": ""
        })
    valid = bool(token) and token == generate_unsubscribe_token(email)
    return templates.TemplateResponse("unsubscribe.html", {
        "request": request,
        "email": email,
        "token": token,
        "valid": valid,
        "success": False,
        "error": ""
    })

@app.post("/unsubscribe")
async def unsubscribe_confirm(
    request: Request,
    email: str = Form(...),
    token: str = Form(...)
):
    """Actually removes subscriber only after confirmation button is clicked."""
    if token != generate_unsubscribe_token(email):
        return templates.TemplateResponse("unsubscribe.html", {
            "request": request, "email": email, "token": token,
            "valid": False, "success": False,
            "error": "Invalid unsubscribe link. Please contact contact@integration-directory.com"
        })
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "DELETE FROM newsletter_subscribers WHERE email = %s",
            (email.strip().lower(),)
        )
        conn.commit()
    except Exception as e:
        print(f"Unsubscribe error: {e}")
    finally:
        conn.close()
    return templates.TemplateResponse("unsubscribe.html", {
        "request": request, "email": email, "token": token,
        "valid": True, "success": True, "error": ""
    })

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



@app.get("/api/compare-tools")
async def api_compare_tools(tool_a: str, tool_b: str):
    try:
        prompt = (
            f"Compare {tool_a} and {tool_b} as an expert tech analyst in 2026.\n"
            f"Provide exactly 3 items separated by the delimiter '|||'.\n"
            f"Item 1: A short 1-sentence summary of what {tool_a} is uniquely best at.\n"
            f"|||\n"
            f"Item 2: A short 1-sentence summary of what {tool_b} is uniquely best at.\n"
            f"|||\n"
            f"Item 3: A neutral 2-sentence verdict explaining that both are excellent and the ultimate choice depends entirely on the user's workflow requirements.\n"
            f"Do not include any markdown format tags or extra words."
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        parts = response.text.split("|||")
        
        return JSONResponse(content={
            "tool_a_text": parts[0].strip() if len(parts) > 0 else f"Elite choice for modern {tool_a} ecosystems.",
            "tool_b_text": parts[1].strip() if len(parts) > 1 else f"Optimized performance tracker for {tool_b}.",
            "verdict": parts[2].strip() if len(parts) > 2 else f"Both tools are outstanding. Select the application that satisfies your immediate automation goals."
        })
    except Exception as e:
        print(f"Gemini Comparison Error: {e}")
        return JSONResponse(content={
            "tool_a_text": f"Top-tier choice for specialized operational scaling.",
            "tool_b_text": f"Excellent choice for flexible workspace management.",
            "verdict": f"The decision rests on your requirements. Both integrate seamlessly using Make.com."
        })
    


@app.get("/api/faq-answers")
async def api_faq_answers(tool_a: str, tool_b: str):
    conn, cursor = get_db_connection()
    
    # FIX: Check both directions (tool_a + tool_b OR tool_b + tool_a)
    cursor.execute('''
        SELECT * FROM integrations 
        WHERE (tool_a ILIKE %s AND tool_b ILIKE %s) 
           OR (tool_a ILIKE %s AND tool_b ILIKE %s)
    ''', (tool_a, tool_b, tool_b, tool_a))
    row = cursor.fetchone()
    
    if row and row.get("faq_1"):
        # Return instantly from Database! 0 API Cost.
        conn.close()
        return JSONResponse(content={
            "ans1": row["faq_1"], "ans2": row["faq_2"], "ans3": row["faq_3"],
            "ans4": row["faq_4"], "ans5": row["faq_5"], "ans6": row["faq_6"]
        })

    # 2. If not in DB or columns are empty, ask Gemini
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
        while len(answers) < 6:
            answers.append("Refer to the official technical documentation for detailed usage.")

        # 3. SAVE TO DATABASE (Using the corrected row ID)
        if row:
            cursor.execute('''
                UPDATE integrations 
                SET faq_1=%s, faq_2=%s, faq_3=%s, faq_4=%s, faq_5=%s, faq_6=%s 
                WHERE id=%s
            ''', (answers[0], answers[1], answers[2], answers[3], answers[4], answers[5], row["id"]))
            conn.commit()
            
        conn.close()
        return JSONResponse(content={
            "ans1": answers[0], "ans2": answers[1], "ans3": answers[2],
            "ans4": answers[3], "ans5": answers[4], "ans6": answers[5]
        })

    except Exception as e:
        print(f"Gemini API Error/Exhausted: {e}")
        conn.close()
        # FALLBACK: If API is exhausted or hits rate limits, send clean generic answers
        return JSONResponse(content={
            "ans1": f"Use Make.com to connect {tool_a} and {tool_b} without code. Create a scenario with a trigger and action.",
            "ans2": "Yes. Make.com's free plan includes 1,000 operations/month — enough for most workflows.",
            "ans3": "No. Make.com is a visual drag-and-drop builder. No coding is required.",
            "ans4": f"You can sync data, trigger alerts, and push updates seamlessly between {tool_a} and {tool_b}.",
            "ans5": f"{tool_a} is a specialized platform optimized for scalable operational tasks.",
            "ans6": f"{tool_b} is an industry-standard tool designed to streamline your daily workflows."
        })  

# --- MAIN DIRECTORY HOMEPAGE ---
@app.get("/")
async def home(request: Request, page: int = 1, q: str = None):
    conn, cursor = get_db_connection()
    items_per_page = 15
    offset = (page - 1) * items_per_page

    try:
        if q:
            query = f"%{q.strip()}%"
            cursor.execute('INSERT INTO search_logs (query) VALUES (%s)', (q.strip().lower(),))
            conn.commit()

            cursor.execute(
                'SELECT COUNT(*) as count FROM integrations ' \
                'WHERE tool_a ILIKE %s OR tool_b ILIKE %s ' \
                'OR similarity(tool_a, %s) > 0.25 OR similarity(tool_b, %s) > 0.25',
                (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
            )
            total_items = cursor.fetchone()['count']

            cursor.execute(
                'SELECT * FROM integrations WHERE tool_a ILIKE %s OR tool_b ILIKE %s ' \
                'OR similarity(tool_a, %s) > 0.25 OR similarity(tool_b, %s) > 0.25 ' \
                'ORDER BY search_volume DESC NULLS LAST LIMIT %s OFFSET %s',
                (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', items_per_page, offset)
            )
        else:
            cursor.execute('SELECT COUNT(*) as count FROM integrations')
            total_items = cursor.fetchone()['count']

            cursor.execute(
                'SELECT * FROM integrations ORDER BY search_volume DESC NULLS LAST LIMIT %s OFFSET %s',
                (items_per_page, offset)
            )

        integrations = cursor.fetchall()

        cursor.execute('''
            SELECT query, COUNT(*) as search_count
            FROM search_logs
            GROUP BY query
            ORDER BY search_count DESC
            LIMIT 5
        ''')
        trending_raw = cursor.fetchall()
        trending_searches = [{"term": row['query'], "count": row['search_count']} for row in trending_raw]

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

        total_pages = math.ceil(total_items / items_per_page) if total_items > 0 else 1
        trust_stats = {
            "integrations": total_items,
            "rating": "4.8",
            "newsletter": "1,000+",
            "location": "🇮🇳 Built in India",
        }
        ga4_id = os.environ.get("GA4_ID", "")

    finally:
        conn.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "integrations": integrations,
        "q": q,
        "page": page,
        "total_pages": total_pages,
        "trending_searches": trending_searches,
        "daily_deals": daily_deals,
        "trust_stats": trust_stats,
        "ga4_id": ga4_id,
    })


@app.get("/glossary")
async def glossary(request: Request):   
    conn, cursor = get_db_connection()
    cursor.execute('SELECT * FROM glossary')
    terms = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("glossary.html", {"request": request, "terms": terms})


@app.get("/compare/{slug_a}-vs-{slug_b}")
async def compare_tools_page(request: Request, slug_a: str, slug_b: str):
    # 1. Clean slugs and strip common web extensions like '.com' for accurate matching
    tool_a_clean = slug_a.replace("-", " ").replace(".com", "").strip()
    tool_b_clean = slug_b.replace("-", " ").replace(".com", "").strip()

    # Pretty names for the UI
    tool_a_display = tool_a_clean.title()
    tool_b_display = tool_b_clean.title()

    conn, cursor = get_db_connection()
    
    # 2. Look up using stripped names with wildcards
    cursor.execute('''
        SELECT * FROM integrations 
        WHERE (tool_a ILIKE %s AND tool_b ILIKE %s) 
           OR (tool_a ILIKE %s AND tool_b ILIKE %s)
        LIMIT 1
    ''', (f"%{tool_a_clean}%", f"%{tool_b_clean}%", f"%{tool_b_clean}%", f"%{tool_a_clean}%"))
    row = cursor.fetchone()

    print(f"--- DEBUG: Looking for '{tool_a_clean}' vs '{tool_b_clean}' ---")

    # 3. CACHE CHECK: If it exists in DB with content, serve it instantly
    if row and row.get("verdict"):
        print("--- DEBUG: SUCCESS! Loaded instantly from Database Cache (0 API Cost). ---")
        if tool_a_clean.lower() in row["tool_a"].lower():
            final_tool_a_text = row["tool_a_text"]
            final_tool_b_text = row["tool_b_text"]
        else:
            final_tool_a_text = row["tool_b_text"]
            final_tool_a_text = row["tool_a_text"]
        
        final_verdict = row["verdict"]
        # Use actual DB names for display matching configuration
        tool_a_display = row["tool_a"]
        tool_b_display = row["tool_b"]
        conn.close()

    else:
        print("--- DEBUG: Cache missing or empty. Requesting Gemini AI... ---")
        try:
            prompt = (
                f"Compare {tool_a_display} and {tool_b_display} as an expert tech analyst in 2026.\n"
                f"Provide exactly 3 items separated by the delimiter '|||'.\n"
                f"Item 1: A short 1-sentence summary of what {tool_a_display} is uniquely best at.\n"
                f"|||\n"
                f"Item 2: A short 1-sentence summary of what {tool_b_display} is uniquely best at.\n"
                f"|||\n"
                f"Item 3: A clear, definitive verdict declaring exactly which tool is the absolute best choice for standard automation workflows, and why.\n"
                f"Pick one clear winner based on features, pricing, or ease of integration in 2026."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            parts = response.text.split("|||")
            
            final_tool_a_text = parts[0].strip() if len(parts) > 0 else f"Elite choice for modern {tool_a_display} ecosystems."
            final_tool_b_text = parts[1].strip() if len(parts) > 1 else f"Optimized performance tracker for {tool_b_display}."
            final_verdict = parts[2].strip() if len(parts) > 2 else f"{tool_a_display} is the superior choice for scalable applications."
            
            # 4. SAVE TO DATABASE (UPDATE existing row OR INSERT brand new row)
            if row:
                if tool_a_clean.lower() in row["tool_a"].lower():
                    save_a = final_tool_a_text
                    save_b = final_tool_b_text
                else:
                    save_a = final_tool_b_text
                    save_b = final_tool_a_text

                cursor.execute('''
                    UPDATE integrations 
                    SET tool_a_text=%s, tool_b_text=%s, verdict=%s 
                    WHERE id=%s
                ''', (save_a, save_b, final_verdict, row["id"]))
                print(f"--- DEBUG: SAVED! Successfully updated existing Database Row ID {row['id']}! ---")
            else:
                # If row completely missing from DB, dynamically CREATE IT right now!
                cursor.execute('''
                    INSERT INTO integrations (tool_a, tool_b, tool_a_text, tool_b_text, verdict, slug) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (tool_a_display, tool_b_display, final_tool_a_text, final_tool_b_text, final_verdict, f"{slug_a}-vs-{slug_b}"))
                print("--- DEBUG: SAVED! Created a brand new integration row in the database successfully! ---")
            
            conn.commit()

        except Exception as e:
            print(f"--- DEBUG: Gemini API Failed: {e} ---")
            print("--- DEBUG: Using fallback text. Save skipped to protect cache integrity. ---")
            final_tool_a_text = f"Top-tier choice for specialized operational scaling."
            final_tool_b_text = f"Excellent choice for flexible workspace management."
            final_verdict = f"{tool_a_display} wins due to its comprehensive ecosystem and robust connectivity."
        
        finally:
            conn.close()

    # 5. Return clean variables to your template
    return templates.TemplateResponse("compare.html", {
        "request": request,
        "tool_a": tool_a_display,
        "tool_b": tool_b_display,
        "slug_a": slug_a,
        "slug_b": slug_b,
        "tool_a_text": final_tool_a_text,
        "tool_b_text": final_tool_b_text,
        "verdict": final_verdict
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
    cursor.execute('SELECT * FROM integrations WHERE slug = %s', (slug,))
    integration = cursor.fetchone()
    conn.close()

    if not integration:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    tool_a_name = integration["tool_a"]
    tool_b_name = integration["tool_b"]

    tool_a_info = get_tool_info(tool_a_name)
    tool_b_info = get_tool_info(tool_b_name)
    together_desc = get_together_description(tool_a_name, tool_b_name)

    # NEW: Intelligent Database Caching for Setup Steps
    if integration.get("step_1"):
        # FAST PATH: Data already exists in database, no API call needed!
        integration_steps = [
            integration["step_1"], integration["step_2"], 
            integration["step_3"], integration["step_4"]
        ]
    else:
        # SLOW PATH: Ask Gemini, then save to Database for next time
        try:
            step_prompt = (
                f"Provide a clear, practical, 4-step guide on how to integrate {tool_a_name} and {tool_b_name} using Make.com.\n"
                f"Format it strictly as exactly 4 steps separated by '|||'. Keep each step brief (under 50 words)."
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=step_prompt,
            )
            steps_raw = response.text.split("|||")
            integration_steps = [step.strip() for step in steps_raw if step.strip()][:4]
            
            while len(integration_steps) < 4:
                integration_steps.append(f"Configure data mapping filters between {tool_a_name} and {tool_b_name}.")
                
            # SAVE TO DATABASE so we never have to ask Gemini for this again
            conn, cursor = get_db_connection()
            cursor.execute('''
                UPDATE integrations SET step_1=%s, step_2=%s, step_3=%s, step_4=%s WHERE slug=%s
            ''', (integration_steps[0], integration_steps[1], integration_steps[2], integration_steps[3], slug))
            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Gemini API Exhausted/Error: {e}")
            # FALLBACK: If API is exhausted, show generic text so the site doesn't break
            integration_steps = [
                f"Log into Make.com and add the {tool_a_name} connection module.",
                f"Select your triggering event inside the {tool_a_name} integration node.",
                f"Link the output connector directly to your target {tool_b_name} dashboard action.",
                "Run a test scenario mapping to confirm parameters transfer successfully."
            ]

    og_image = f"https://integration-directory.com/static/og-default.png"
    canonical = f"https://integration-directory.com/integrate/{slug}"
    ga4_id = os.environ.get("GA4_ID", "")

    return templates.TemplateResponse("integration.html", {
        "request": request,
        "data": integration,
        "integration": integration,
        "slug": slug,
        "tool_a": tool_a_name,
        "tool_b": tool_b_name,
        "review_date": "June 2026",
        "og_image": og_image,
        "canonical": canonical,
        "ga4_id": ga4_id,
        
        # Pass the steps directly to the frontend template
        "step_1": integration_steps[0],
        "step_2": integration_steps[1],
        "step_3": integration_steps[2],
        "step_4": integration_steps[3],

        # Tool infos...
        "tool_a_emoji": tool_a_info["emoji"],
        "tool_a_category": tool_a_info["category"],
        "tool_a_description": tool_a_info["description"],
        "tool_a_features": tool_a_info["features"],
        "tool_a_plan": tool_a_info["plan"],
        "tool_a_url": tool_a_info["url"],
        "tool_a_short": tool_a_info["short"],

        "tool_b_emoji": tool_b_info["emoji"],
        "tool_b_category": tool_b_info["category"],
        "tool_b_description": tool_b_info["description"],
        "tool_b_features": tool_b_info["features"],
        "tool_b_plan": tool_b_info["plan"],
        "tool_b_url": tool_b_info["url"],
        "tool_b_short": tool_b_info["short"],
        "together_description": together_desc,
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
    cursor.execute('SELECT slug FROM integrations')
    integrations = cursor.fetchall()
    cursor.execute('SELECT slug FROM blog_posts')
    blog_posts = cursor.fetchall()
    cursor.execute('SELECT slug FROM news_posts')
    news_posts = cursor.fetchall()
    conn.close()
 
    base_url = "https://integration-directory.com"
    today = datetime.now().strftime("%Y-%m-%d")
 
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
 
    # Static pages — Part 7B: expanded best-for pages added
    static_pages = [
        ("", "1.0", "daily"),
        ("/blog", "0.9", "daily"),
        ("/news", "0.9", "daily"),
        ("/gear", "0.8", "weekly"),
        ("/india-deals", "0.7", "weekly"),
        ("/about", "0.6", "monthly"),
        ("/contact", "0.6", "monthly"),
        ("/privacy", "0.4", "monthly"),
        ("/terms", "0.4", "monthly"),
        ("/glossary", "0.6", "weekly"),
        ("/compare/make-vs-zapier", "0.8", "weekly"),
        ("/compare/notion-vs-airtable", "0.7", "weekly"),
        ("/compare/slack-vs-teams", "0.7", "weekly"),
        ("/best-integrations-for/slack", "0.8", "weekly"),
        ("/best-integrations-for/notion", "0.8", "weekly"),
        ("/best-integrations-for/hubspot", "0.8", "weekly"),
        ("/best-integrations-for/shopify", "0.8", "weekly"),
        ("/best-integrations-for/airtable", "0.7", "weekly"),
        ("/best-integrations-for/zapier", "0.7", "weekly"),
        ("/best-integrations-for/chatgpt", "0.8", "weekly"),
        ("/best-integrations-for/monday", "0.8", "weekly"),
        ("/best-integrations-for/clickup", "0.8", "weekly"),
        ("/best-integrations-for/github", "0.7", "weekly"),
        ("/best-integrations-for/calendly", "0.7", "weekly"),
        ("/best-integrations-for/typeform", "0.7", "weekly"),
        ("/best-integrations-for/trello", "0.7", "weekly"),
        ("/best-integrations-for/asana", "0.7", "weekly"),
        ("/best-integrations-for/claude", "0.9", "weekly"),
        ("/best-integrations-for/gemini", "0.9", "weekly"),
        ("/best-integrations-for/ollama", "0.8", "weekly"),
        ("/best-integrations-for/n8n", "0.9", "weekly"),
        ("/best-integrations-for/telegram", "0.8", "weekly"),
        ("/best-integrations-for/whatsapp", "0.8", "weekly"),
        ("/best-integrations-for/deepseek", "0.8", "weekly"),
        ("/best-integrations-for/midjourney", "0.7", "weekly"),
        ("/best-integrations-for/cursor", "0.8", "weekly"),
        ("/best-integrations-for/langchain", "0.8", "weekly"),
        ("/best-integrations-for/perplexity", "0.7", "weekly"),
        ("/best-integrations-for/grok", "0.7", "weekly"),
        ("/best-integrations-for/mistral", "0.7", "weekly"),
    ]
    for path, priority, freq in static_pages:
        xml += f'  <url>\n    <loc>{base_url}{path}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n'
 
    # Integration pages
    for item in integrations:
        xml += f'  <url>\n    <loc>{base_url}/integrate/{item["slug"]}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
 
    # Blog posts
    for post in blog_posts:
        xml += f'  <url>\n    <loc>{base_url}/blog/{post["slug"]}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n'
 
    # News posts
    for post in news_posts:
        xml += f'  <url>\n    <loc>{base_url}/news/{post["slug"]}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n'
 
    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")
 
@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    content = "User-agent: *\nAllow: /\nSitemap: https://integration-directory.com/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")
 
 


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
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
        
    # Pass dynamic back routing to the HTML template
    return templates.TemplateResponse("blog_post.html", {
        "request": request, 
        "post": post,
        "back_url": "/news",
        "back_text": "AI News"
    })


# Real RSS sources — AI and automation news only
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
]

# Different angle templates so each article has a unique editorial angle
NEWS_ANGLES = [
    "What It Means for Your Automation Workflows",
    "How SaaS Teams Should Respond",
    "The Impact on No-Code and Low-Code Tools",
    "A Practical Guide for Operations Teams",
]

@app.get("/api/agent/daily-news")
async def run_news_agent(secret: str, background_tasks: BackgroundTasks, count: int = 4):
    """
    Cron job endpoint — posts up to `count` news articles per call (default 4).
    Call 4x/day via cron to publish up to 16 articles/day, or call once with ?count=4.
    Rate limit: max 4 posts per 6-hour window to avoid spam.
    """
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized Access"}

    # Clamp between 1 and 4
    count = max(1, min(count, 4))

    conn, cursor = get_db_connection()

    # Rate limit: max 4 posts in the last 6 hours
    cursor.execute(
        "SELECT COUNT(*) as c FROM news_posts WHERE published_date >= NOW() - INTERVAL '6 hours'"
    )
    posts_recent = cursor.fetchone()["c"]
    if posts_recent >= 4:
        conn.close()
        return {"status": "Skipped", "reason": f"Already posted {posts_recent} news articles in the last 6 hours."}

    slots_remaining = 4 - posts_recent
    to_post = min(count, slots_remaining)

    # Fetch real articles from RSS
    real_articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
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
        return {"status": "Failed", "error": "Could not fetch any RSS articles."}

    # Shuffle to get variety
    random.shuffle(real_articles)

    posted = []
    errors = []

    for i in range(to_post):
        source_article = real_articles[i % len(real_articles)]
        angle = NEWS_ANGLES[i % len(NEWS_ANGLES)]

        prompt = f"""You are a senior tech journalist writing for integration-directory.com, a site about software automation and AI tools.

A real news article was just published:
- Source: {source_article['source']}
- Headline: {source_article['title']}
- Summary: {source_article['summary']}

Write a 600-word original analysis article from this angle: "{angle}"
Inspired by the REAL news above. Do not invent company names or fake products.
Focus on: what this means for software integrations, workflow automation, and SaaS teams.

STRICT INSTRUCTIONS:
- Title must be: "[Real Topic]: {angle}" — use an <h1> tag.
- Use <h2>, <p>, <ul>, <li>, <strong> HTML only. No markdown.
- Do NOT use hype words like "unleash", "nexus", "revolutionizing".
- Include a "How to automate this with Make.com" section with this exact CTA:
  <div style="background:#f0f4ff;padding:16px;border-radius:8px;margin:20px 0;">
  <strong>Automate this workflow today →</strong> <a href="https://www.make.com/en/register?pc=sampath9" rel="sponsored">Start free on Make.com</a> — no code required.
  </div>
- End with a 3-question FAQ using <h3> for questions and <p> for answers.
- Do NOT invent statistics or product features not in the source article.
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            html_content = response.text.replace("```html", "").replace("```", "").strip()
            title_match = re.search(r"<h1>(.*?)</h1>", html_content)
            title = title_match.group(1) if title_match else f"{source_article['title']}: {angle}"
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80]

            cursor.execute(
                "INSERT INTO news_posts (title, slug, content) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
                (title, slug, html_content),
            )
            conn.commit()
            posted.append(title)

            # Only send newsletter for the FIRST post in batch (avoid spamming subscribers)
            if i == 0:
                background_tasks.add_task(send_newsletter, title, html_content)

        except Exception as e:
            errors.append(str(e))
            print(f"News Agent Error (article {i+1}): {e}")

    conn.close()
    return {
        "status": "Success",
        "posted_count": len(posted),
        "posted": posted,
        "errors": errors if errors else None
    }


# --- 8. Legal Pages (AdSense Compliance) ---
@app.get("/privacy")
async def privacy_page(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms")
async def terms_page(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/about")
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
 

#CONTACT_ROUTE = '''
@app.get("/contact")
async def contact_page(request: Request):
    sent = request.query_params.get("sent", "false") == "true"
    return templates.TemplateResponse("contact.html", {"request": request, "sent": sent})

# --- Contact Form Submission (POST - handle form + send emails) ---
@app.post("/contact")
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            '''INSERT INTO contact_submissions (name, email, subject, message)
               VALUES (%s, %s, %s, %s)''',
            (name, email, subject, message)
        )
        conn.commit()
    except Exception as e:
        print(f"Contact form error: {e}")
    finally:
        conn.close()
    if background_tasks:
        background_tasks.add_task(send_contact_email, name, email, subject, message)
    return RedirectResponse(url="/contact?sent=true", status_code=303)


def send_contact_email(name: str, user_email: str, subject: str, message: str):
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    if not sender_email or not sender_password:
        print("SMTP credentials missing — contact email not sent.")
        return
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        admin_msg = MIMEMultipart()
        admin_msg['From'] = sender_email
        admin_msg['To'] = sender_email
        admin_msg['Subject'] = f"📬 Contact Form: {subject} — from {name}"
        admin_msg.attach(MIMEText(f"""<html><body style="font-family:sans-serif;padding:20px;">
  <h2>New Contact Form Submission</h2>
  <p><b>Name:</b> {name}</p><p><b>Email:</b> {user_email}</p>
  <p><b>Subject:</b> {subject}</p><hr>
  <p><b>Message:</b></p><p style="white-space:pre-wrap;">{message}</p>
</body></html>""", 'html'))
        server.send_message(admin_msg)
        user_msg = MIMEMultipart()
        user_msg['From'] = f"Integration Directory <{sender_email}>"
        user_msg['To'] = user_email
        user_msg['Subject'] = "We received your message! ✅"
        user_msg.attach(MIMEText(f"""<html><body style="font-family:sans-serif;padding:20px;color:#333;">
  <h2 style="color:#2563eb;">Thanks, {name}! We got your message.</h2>
  <p>We'll get back to you within 1–2 business days.</p>
  <p style="background:#f3f4f6;padding:12px;border-radius:6px;font-style:italic;">{message[:300]}{'...' if len(message)>300 else ''}</p>
  <hr><p style="font-size:12px;color:#999;">Integration Directory · contact@integration-directory.com</p>
</body></html>""", 'html'))
        server.send_message(user_msg)
        server.quit()
        print(f"Contact emails sent for {user_email}")
    except Exception as e:
        print(f"Contact email error: {e}")
 


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


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

# ================================================================
# PART 7B — GLOSSARY SEED ENDPOINT
# Populates the glossary table with 60 SaaS/automation terms
# Call once: GET /api/admin/seed-glossary?secret=YOUR_SECRET
# ================================================================

GLOSSARY_TERMS = [
    ("API", "Application Programming Interface — a way for software applications to communicate with each other and share data automatically."),
    ("Automation", "Using software to perform repetitive tasks without human intervention, saving time and reducing errors."),
    ("CRM", "Customer Relationship Management — software used to manage interactions with current and potential customers."),
    ("Webhook", "A way for one app to send real-time data to another app whenever a specific event occurs, without polling."),
    ("Integration", "A connection between two or more software tools that allows them to share data and trigger actions in each other."),
    ("No-Code", "A software development approach that allows non-technical users to build applications using visual drag-and-drop interfaces."),
    ("Low-Code", "A development method that requires minimal hand-coding, using visual tools with some scripting for customisation."),
    ("SaaS", "Software as a Service — cloud-based software delivered via subscription, accessible from any browser without installation."),
    ("Workflow", "A defined sequence of tasks and processes that move work from one stage to another to achieve a goal."),
    ("Trigger", "An event that starts an automated workflow, such as a new form submission, email received, or record created."),
    ("Action", "The automated task performed after a trigger fires, such as sending an email, creating a record, or posting a message."),
    ("Scenario", "In Make.com, a visual automation that connects apps with triggers and actions to automate a workflow."),
    ("Zap", "In Zapier, a single automated workflow consisting of a trigger and one or more actions."),
    ("Kanban", "A visual project management method using boards, columns, and cards to track work progress through stages."),
    ("Scrum", "An agile framework for managing software development using short sprints, daily stand-ups, and retrospectives."),
    ("Sprint", "A fixed time period (usually 1-2 weeks) in which a development team completes a set of planned work."),
    ("OKR", "Objectives and Key Results — a goal-setting framework that defines objectives and measurable outcomes."),
    ("KPI", "Key Performance Indicator — a measurable value that shows how effectively a company is achieving key business objectives."),
    ("Lead", "A potential customer who has shown interest in a product or service by sharing contact information."),
    ("Funnel", "A marketing model describing the customer journey from awareness through consideration to purchase."),
    ("Drip Campaign", "A series of automated emails sent on a schedule or triggered by user actions to nurture leads."),
    ("Segmentation", "Dividing an audience into groups based on shared characteristics for targeted marketing."),
    ("A/B Testing", "Comparing two versions of a webpage, email, or ad to see which performs better with real users."),
    ("Churn", "The percentage of customers who stop using a product or cancel their subscription in a given period."),
    ("MRR", "Monthly Recurring Revenue — the predictable revenue a subscription business earns each month."),
    ("ARR", "Annual Recurring Revenue — the value of recurring subscription revenue for a full year."),
    ("LTV", "Lifetime Value — the total revenue a business expects from a customer over the entire relationship."),
    ("CAC", "Customer Acquisition Cost — the total cost of sales and marketing to acquire one new customer."),
    ("NPS", "Net Promoter Score — a customer loyalty metric based on one question: how likely are you to recommend us?"),
    ("Pipeline", "A visual representation of where prospects or deals are in the sales or project management process."),
    ("Deal Stage", "A step in the sales pipeline that represents how far a prospect is in the buying process."),
    ("ETL", "Extract, Transform, Load — a data integration process that moves data from one system to another."),
    ("REST API", "A type of API that uses HTTP requests to GET, POST, PUT, and DELETE data between systems."),
    ("OAuth", "An open standard for access delegation, allowing apps to access resources on behalf of a user without sharing passwords."),
    ("JSON", "JavaScript Object Notation — a lightweight data format used to exchange data between APIs and applications."),
    ("CSV", "Comma-Separated Values — a simple file format for tabular data, easily imported into spreadsheets and databases."),
    ("Dashboard", "A visual display of key metrics and data points, giving a real-time overview of performance."),
    ("Cron Job", "A scheduled task that runs automatically at specified time intervals on a server."),
    ("Rate Limit", "A restriction on how many API requests can be made in a given time period."),
    ("Pagination", "Breaking large sets of data into smaller pages to improve performance and usability."),
    ("Slug", "A URL-friendly version of a title or name, using lowercase letters and hyphens instead of spaces."),
    ("CDN", "Content Delivery Network — a distributed network of servers that delivers web content quickly based on user location."),
    ("Uptime", "The percentage of time a website or service is operational and accessible to users."),
    ("SSL/TLS", "Security protocols that encrypt data transmitted between a browser and a server, shown as HTTPS."),
    ("Two-Factor Authentication", "A security process requiring two forms of verification to access an account."),
    ("Sandbox", "A testing environment that isolates untested code changes and experimentation from the production environment."),
    ("Deployment", "The process of moving code changes from a development environment to a live production server."),
    ("CI/CD", "Continuous Integration/Continuous Deployment — automated processes that test and release software changes frequently."),
    ("Git", "A distributed version control system that tracks changes in source code during software development."),
    ("Agile", "An iterative software development methodology focused on collaboration, flexibility, and customer feedback."),
    ("Scaleup", "A startup that has found product-market fit and is focused on rapid growth and scaling operations."),
    ("White Label", "A product or service produced by one company that other companies rebrand and sell as their own."),
    ("Freemium", "A business model offering basic features for free while charging for premium features or higher usage."),
    ("Open Source", "Software with source code that anyone can inspect, modify, and distribute freely."),
    ("Data Enrichment", "Adding supplementary information to existing records, such as adding company size to a contact."),
    ("Deduplicate", "The process of identifying and removing duplicate records from a database."),
    ("Mapping", "Matching data fields from one application to corresponding fields in another during an integration."),
    ("Parse", "To analyse and convert data from one format to a structured format that can be processed by a program."),
    ("Middleware", "Software that connects different applications and enables them to communicate and exchange data."),
    ("Event-Driven", "An architecture where actions are triggered by specific events rather than running on a fixed schedule."),
]

@app.get("/api/admin/seed-glossary")
async def seed_glossary(secret: str):
    """One-time endpoint to populate the glossary table. Call once then ignore."""
    if secret != os.environ.get("AGENT_SECRET", "my_local_secret"):
        return {"error": "Unauthorized"}
    conn, cursor = get_db_connection()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS glossary (
                id SERIAL PRIMARY KEY,
                term TEXT UNIQUE NOT NULL,
                definition TEXT NOT NULL
            )
        """)
        inserted = 0
        for term, definition in GLOSSARY_TERMS:
            cursor.execute(
                "INSERT INTO glossary (term, definition) VALUES (%s, %s) ON CONFLICT (term) DO NOTHING",
                (term, definition)
            )
            if cursor.rowcount > 0:
                inserted += 1
        conn.commit()
        return {"status": "Success", "inserted": inserted, "total": len(GLOSSARY_TERMS)}
    except Exception as e:
        return {"status": "Error", "error": str(e)}
    finally:
        conn.close()


# ================================================================
# PART 7A — BREADCRUMB JSON-LD for homepage and blog/news listing
# Added as a helper function used in templates via request context
# ================================================================

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint for monitoring."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}