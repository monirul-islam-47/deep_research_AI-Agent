import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import trafilatura
import re
import requests # Keep for the old custom fetch_html for comparison or non-JS sites if desired
from bs4 import BeautifulSoup # Keep for the old custom heuristic if needed

# --- Playwright HTML Fetching ---
async def fetch_html_with_playwright_async(url: str, timeout: int = 20000) -> str | None: # timeout in ms
    """
    Fetches fully rendered HTML content from a URL using Playwright (async version).
    """
    print(f"🕸️ Attempting to fetch dynamic HTML with Playwright from: {url}")
    browser = None # Initialize browser to None for finally block
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 DeepResearchBot/2.0'
            })

            await page.goto(url, timeout=timeout, wait_until='networkidle')
            
            html_content = await page.content()
            # Ensure browser is closed even if page.content() somehow fails before this
            # await browser.close() # Moved to finally block

            if html_content:
                print(f"   Successfully fetched dynamic HTML (Length: {len(html_content)}) from {url}")
                return html_content
            else:
                print(f"   Playwright returned empty content for {url}")
                return None
    except PlaywrightTimeoutError:
        print(f"❌ Playwright timed out loading URL: {url}")
        return None
    except Exception as e:
        print(f"❌ Error fetching HTML with Playwright for {url}: {e}")
        return None
    finally:
        if browser:
            await browser.close()


def fetch_html_with_playwright_sync(url: str, timeout: int = 20000) -> str | None:
    """
    Synchronous wrapper for fetch_html_with_playwright_async.
    Uses asyncio.run() which is the standard way to call an async function
    from synchronous code in Python 3.7+.
    The DeprecationWarning "There is no current event loop" from
    `asyncio.get_event_loop().is_running()` is generally benign for simple CLI scripts
    where asyncio.run() manages its own loop.
    """
    # The simplest way for a synchronous script to call an async function:
    # asyncio.run() creates a new event loop, runs the async function, and closes the loop.
    try:
        return asyncio.run(fetch_html_with_playwright_async(url, timeout))
    except Exception as e:
        # Catch any exception from asyncio.run or the async function itself
        print(f"❌ Error in playwright sync wrapper for {url}: {e}")
        return None


# --- Trafilatura Content Extraction ---
def extract_text_with_trafilatura(html_content: str, url: str = "") -> str | None:
    """
    Extracts main textual content from HTML using Trafilatura.
    """
    if not html_content:
        print(f"⚠️ No HTML content provided to Trafilatura for URL: {url}")
        return None

    print(f"📄 Attempting extraction with Trafilatura (URL: {url})")
    
    # Simplified call to trafilatura.extract, relying on its defaults initially.
    # Common parameters that are usually safe:
    # include_comments=False, include_tables=False
    # url=url (providing the original URL can sometimes help trafilatura)
    try:
        text_content = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
            #deduplicate=True, # Optional: can remove duplicate text sections
            url=url # Pass the original URL to trafilatura as it can use it
        )
    except Exception as e:
        print(f"❌ Error during Trafilatura extraction for {url}: {e}")
        return None


    if text_content:
        # Trafilatura does a good job of cleaning, but an extra pass for excessive newlines
        cleaned_text = re.sub(r'\n(\s*\n)+', '\n\n', text_content).strip()
        print(f"   Successfully extracted text (Length: {len(cleaned_text)} chars) using Trafilatura from {url}.")
        return cleaned_text
    else:
        print(f"⚠️ Trafilatura extracted no main text from {url}.")
        return None

# --- Main public function for the research agent ---
def fetch_and_extract_content(url: str) -> str | None:
    """
    Fetches HTML from a URL using Playwright (for dynamic content)
    and then extracts text using Trafilatura.
    """
    # 1. Fetch with Playwright
    print(f"🚀 Starting Playwright fetch for: {url}")
    html_content = fetch_html_with_playwright_sync(url)
    
    if html_content:
        # 2. Extract with Trafilatura
        print(f"🔬 HTML fetched, proceeding to Trafilatura extraction for: {url}")
        return extract_text_with_trafilatura(html_content, url)
    
    print(f"ℹ️ Failed to fetch HTML with Playwright for {url}. No content to extract.")
    return None


# --- Keep the old custom heuristic and requests-based fetch for comparison or fallback ---
def fetch_html_requests_custom(url: str, timeout: int = 15) -> str | None:
    """Fetches HTML content from a URL using requests (for static sites or fallback)."""
    print(f"🕸️ Attempting to fetch static HTML with requests from: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 DeepResearchTSPort/1.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching static HTML with requests for {url}: {e}")
        return None

def extract_text_from_html_custom_heuristic(html_content: str, url:str ="") -> str | None:
    """
    Custom heuristic extraction (from previous version, mimicking TS project).
    """
    if not html_content: return None
    print(f"📄 Attempting custom heuristic text extraction from HTML (URL: {url})")
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = ""
    article_tag = soup.find('article')
    if article_tag:
        text_content = article_tag.get_text(separator='\n', strip=False)
    if not text_content or len(text_content) < 100:
        body_tag = soup.find('body')
        if body_tag:
            for element in body_tag(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'noscript', 'iframe', 'svg', 'canvas']):
                element.decompose()
            text_content = body_tag.get_text(separator='\n', strip=False)
        else: # Fallback if no body tag
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'noscript', 'iframe', 'svg', 'canvas']):
                element.decompose()
            text_content = soup.get_text(separator='\n', strip=False)
    if not text_content:
        print(f"⚠️ Custom heuristic extraction yielded no text content from {url}.")
        return None
    
    lines = [line.strip() for line in text_content.splitlines()]
    cleaned_lines = [line for line in lines if line and len(line.strip()) > 10 or re.search(r'[a-zA-Z]', line)]
    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r'\n(\s*\n)+', '\n\n', cleaned_text).strip()
    
    if not cleaned_text:
        print(f"⚠️ Text content became empty after custom heuristic cleaning for {url}.")
        return None
    print(f"   Successfully extracted (custom heuristic) text (Length: {len(cleaned_text)} chars) from {url}.")
    return cleaned_text

# --- Test block ---
if __name__ == '__main__':
    print("--- Testing scraper_utils.py (Playwright + Trafilatura) ---")

    test_urls = [
        "https://www.theguardian.com/international", # News homepage, often dynamic
        "https://www.nature.com/articles/d41586-023-03713-x", # Nature article
        "https://waitbutwhy.com/2015/01/artificial-intelligence-revolution-1.html", # Blog post
        "https://nonexistentfakedomain123abc.com/" # A URL that should fail fetching
    ]

    for t_url in test_urls:
        print(f"\n--- Scraping Test URL: {t_url} ---")
        
        content = fetch_and_extract_content(t_url)

        if content:
            print(f"  Extracted (Playwright+Trafilatura) Snippet (first 300 chars):\n  '{content[:300].strip()}...'")
            print(f"  Total extracted length: {len(content)} characters.")
        else:
            print(f"  Failed to extract content or no main content found using Playwright+Trafilatura for {t_url}.")