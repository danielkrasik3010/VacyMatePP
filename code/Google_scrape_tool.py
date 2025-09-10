import os
import json
from tavily import TavilyClient
import datetime
from typing import Optional
from urllib.parse import urlparse
from serpapi import GoogleSearch
from langchain.agents import tool
from dotenv import load_dotenv
load_dotenv()
# Load the Tavily API key from your environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPAPI_API_KEY = '297fdf48a26d5137d7068c6a7f7341cf0db14c16212b9a3eade05f4768521453'

@tool
def google_search_tool(query: str) -> str:
    """
    Performs a real-time web search using SerpApi.
    Returns top 10 results with title, link, snippet, and a list of links.
    """
    try:
        search = GoogleSearch({
            "q": query,
            "api_key": SERPAPI_API_KEY
        })
        results = search.get_dict().get("organic_results", [])[:10]
        simplified = [
            {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
            for r in results
        ]
        links = [r.get("link") for r in results if r.get("link")]
        return json.dumps({"results": simplified, "links": links}, indent=2)
    except Exception as e:
        return f"Error with Google Search API: {e}"
    
def scrape_with_tavily(urls: list, api_key: str):
    """
    Scrapes content from a list of URLs using the Tavily Extract API.

    Args:
        urls (list): A list of URLs to scrape.
        api_key (str): Your Tavily API key.
    
    Returns:
        A dictionary containing the scraped results.
    """
    if not api_key:
        return {"error": "Tavily API key not found."}
    
    tavily_client = TavilyClient(api_key=api_key)
    
    try:
        response = tavily_client.extract(
            urls=urls,
            include_images=False,
            extract_depth="basic" # Can be 'basic' or 'advanced'
        )
        return response
        
    except Exception as e:
        return {"error": f"An error occurred during extraction: {e}"}

if __name__ == "__main__":
    search_result_str = google_search_tool.invoke("top attractions in London PDF")
    search_result_json = json.loads(search_result_str)
    links_to_scrape = search_result_json.get('links', [])
    urls_to_scrape = links_to_scrape[:5]  # Limit to first 3 links for testing
    
    scraped_data = scrape_with_tavily(urls=urls_to_scrape, api_key=TAVILY_API_KEY)
    
    # Print the results in a readable format
    print(json.dumps(scraped_data, indent=2))