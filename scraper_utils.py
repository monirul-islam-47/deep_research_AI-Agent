import requests
from readability import Document # from readability-lxml
from bs4 import BeautifulSoup    # To convert readability's HTML output to plain text

# Optional: Import trafilatura if you prefer to use it
# import trafilatura

def fetch_and_extract_content_readability(url: str) -> str | None:
    """
    Fetches a URL and extracts the main textual content using readability-lxml.

    Args:
        url (str): The URL of the web page to scrape.

    Returns:
        str | None: The extracted main text content of the page, 
                    or None if fetching or extraction fails.
    """
    print(f"🕸️ Attempting to fetch and extract content from: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 DeepResearchBot/1.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15) # Increased timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)

        # Use readability-lxml to parse the HTML and extract main content
        doc = Document(response.text)
        
        title = doc.title()
        content_html = doc.summary() # This gives the main content as HTML

        # Convert the main content HTML to plain text using BeautifulSoup
        soup = BeautifulSoup(content_html, 'html.parser')
        main_text = soup.get_text(separator='\n', strip=True)
        
        if main_text:
            print(f"📄 Successfully extracted content (Title: \"{title}\", Length: {len(main_text)} chars) from {url}")
            return main_text
        else:
            print(f"⚠️ Readability extracted no main text from {url} (Title: \"{title}\")")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error fetching URL {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        # Catch other potential errors during readability processing
        print(f"❌ Error processing content from {url}: {e}")
        return None

# --- Alias for the chosen scraper ---
# This makes it easy to switch scraping methods if you implement others.
fetch_and_extract_content = fetch_and_extract_content_readability

# --- Alternative using trafilatura (if you prefer) ---
# def fetch_and_extract_content_trafilatura(url: str) -> str | None:
#     """
#     Fetches a URL and extracts main content using trafilatura.
#     (Uncomment this and `import trafilatura` if you want to use it)
#     """
#     print(f"🕸️ Attempting to fetch and extract content from: {url} (using trafilatura)")
#     try:
#         # Fetch the page first (trafilatura can do this, but requests gives more control over headers/timeout)
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 DeepResearchBot/1.0'
#         }
#         downloaded_html = requests.get(url, headers=headers, timeout=15).text
        
#         if downloaded_html:
#             # Extract main text using trafilatura
#             # favour_recall=True can sometimes get more text but might include more noise
#             main_text = trafilatura.extract(downloaded_html, include_comments=False, include_tables=False, favour_recall=False)
#             if main_text:
#                 print(f"📄 Successfully extracted content (Length: {len(main_text)} chars) from {url} using trafilatura")
#                 return main_text
#             else:
#                 print(f"⚠️ Trafilatura couldn't extract main text from {url}")
#                 return None
#         else:
#             print(f"⚠️ Failed to download HTML from {url} for trafilatura")
#             return None
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Error fetching URL {url} for trafilatura: {e}")
#         return None
#     except Exception as e:
#         print(f"❌ Error during trafilatura extraction for {url}: {e}")
#         return None
# If you use trafilatura, change the alias:
# fetch_and_extract_content = fetch_and_extract_content_trafilatura


if __name__ == '__main__':
    # Example usage for testing this module directly
    print("--- Testing scraper_utils.py ---")

    # A well-structured article page
    test_url_article = "https://www.theverge.com/2023/10/26/23933370/ai-image-generators-data-scraping-midjourney-stability-ai-deviantart"
    # A more complex page, or one that might be tricky
    test_url_blog = "https://waitbutwhy.com/2015/01/artificial-intelligence-revolution-1.html"
    # A URL that might fail or return non-article content
    test_url_problematic = "http://example.com/nonexistentpage.html" # Will likely cause HTTPError
    test_url_simple_site = "https://www.google.com" # Not an article, readability might return little

    test_urls = [test_url_article, test_url_blog, test_url_simple_site, test_url_problematic]

    for t_url in test_urls:
        print(f"\n--- Scraping Test URL: {t_url} ---")
        # content = fetch_and_extract_content_readability(t_url) # Explicitly call for testing
        content = fetch_and_extract_content(t_url) # Uses the alias

        if content:
            print(f"  Extracted Content Snippet (first 300 chars):\n  '{content[:300].strip()}...'")
            print(f"  Total extracted length: {len(content)} characters.")
        else:
            print("  Failed to extract content or no main content found.")