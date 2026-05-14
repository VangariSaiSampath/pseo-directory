import pandas as pd
import random

def generate_integration_data():
    # A list of highly searched B2B SaaS tools
    tools = [
        "Slack", "Notion", "HubSpot", "Salesforce", "Jira", 
        "Trello", "Asana", "Zoom", "Mailchimp", "Stripe",
        "Shopify", "Zendesk", "Airtable", "Google Sheets", "Discord",
        "Intercom", "Dropbox", "Typeform", "Figma", "GitHub"
    ]

    integrations_data = []
    print("Generating programmatic SEO dataset...")

    # Loop through the tools and pair them with every other tool
    for tool_a in tools:
        for tool_b in tools:
            # Don't pair a tool with itself (e.g., Slack + Slack)
            if tool_a != tool_b:
                slug = f"{tool_a.lower().replace(' ', '-')}-and-{tool_b.lower().replace(' ', '-')}"
                
                # Create a dynamic, SEO-friendly description
                description = f"Automate your workflow by connecting {tool_a} with {tool_b}. Sync data instantly, trigger automatic actions, and save hours of manual data entry every week."
                
                # Mock search volume for the UI
                search_volume = random.randint(50, 15000)

                integrations_data.append({
                    "slug": slug,
                    "tool_a": tool_a,
                    "tool_b": tool_b,
                    "description": description,
                    "search_volume": search_volume,
                    "affiliate_link": "https://www.make.com/en/register?pc=sampath9" # <-- ADD THIS LINE
                })

    return integrations_data

if __name__ == "__main__":
    data = generate_integration_data()
    
    # Save the generated data to a CSV file
    df = pd.DataFrame(data)
    df.to_csv('raw_integrations.csv', index=False)
    print(f"Success! Generated {len(data)} unique integrations and saved them to raw_integrations.csv")