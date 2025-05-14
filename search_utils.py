import os
import time
from dotenv import load_dotenv
from googleapiclient.discovery import build # For Google Search

# Load environment variables to get Google API credentials
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def search_web_google(query: str, max_results: int = 5):
    """
    Performs a web search using Google Custom Search API.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of search results to return.
                           (Note: Google API returns up to 10 per request)

    Returns:
        list: A list of search result dictionaries, formatted to be similar
              to what DDG provided: {'title': ..., 'href': ..., 'body': ...}.
              Returns an empty list if the search fails or yields no results.
    """
    print(f"🔎 Searching Google for: \"{query}\" (requesting up to {max_results} results)")

    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("❌ Google API Key or CSE ID not found in environment variables.")
        print("   Please ensure GOOGLE_API_KEY and GOOGLE_CSE_ID are set in your .env file.")
        return []

    # Add a small delay to be a good citizen, though API usage is metered by Google
    time.sleep(1)

    try:
        # Build a service object for interacting with the API
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Google API returns 10 results by default, and max 10 per request using 'num' parameter.
        # If max_results > 10, multiple requests would be needed, but for simplicity,
        # we'll cap at 10 for a single request here, or adjust 'num'.
        num_results_to_request = min(max_results, 10) # Google API 'num' parameter max is 10

        response = service.cse().list(
            q=query,                # Search query
            cx=GOOGLE_CSE_ID,       # Custom Search Engine ID
            num=num_results_to_request  # Number of results to return (1-10)
            # You can add other parameters like 'lr' for language restrictions, etc.
            # e.g., lr='lang_en'
        ).execute()

        formatted_results = []
        if 'items' in response:
            for item in response['items']:
                formatted_results.append({
                    'title': item.get('title'),
                    'href': item.get('link'), # Google calls the URL 'link'
                    'body': item.get('snippet') # Google calls the snippet 'snippet'
                })
            print(f"🔍 Found {len(formatted_results)} results from Google for \"{query}\".")
        else:
            print(f"⚠️ No results found from Google for \"{query}\".")
        
        return formatted_results

    except Exception as e:
        print(f"❌ Error during Google Custom Search for \"{query}\": {e}")
        # Potentially check for specific quota errors if needed
        if "quotaExceeded" in str(e).lower() or "daily limit exceeded" in str(e).lower():
            print("   This might be a Google API quota issue. Check your Google Cloud Console.")
        return []

# --- Alias to the preferred search function ---
# Now explicitly point to the Google search function
search_web = search_web_google


if __name__ == '__main__':
    # Example usage for testing this module directly
    print("--- Testing search_utils.py with Google Search ---")
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("🚫 GOOGLE_API_KEY or GOOGLE_CSE_ID not set. Skipping live Google Search test.")
    else:
        test_queries = [
            "latest advancements in AI",
            # "benefits of learning Python",
        ]
        
        for t_query in test_queries:
            print(f"\n--- Testing Google query: \"{t_query}\" ---")
            # Requesting fewer results for testing to conserve quota
            search_results = search_web_google(t_query, max_results=3) 
            
            if search_results:
                for i, result in enumerate(search_results):
                    print(f"\n  Result {i+1}:")
                    print(f"    Title: {result.get('title', 'N/A')}")
                    print(f"    URL: {result.get('href', 'N/A')}")
                    print(f"    Snippet: {result.get('body', 'N/A')[:150]}...")
            else:
                print("  No search results returned from Google search_web function.")