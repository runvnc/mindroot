import requests
from bs4 import BeautifulSoup
import random
from ..services import service
from ..commands import command
import trafilatura

@service()
async def web_search(query, num_results=5):
    """Perform a web search using Google.

    Args:
        query (str): The search query.
        num_results (int, optional): The number of results to return. Defaults to 5.

    Returns:
        list: A list of dictionaries containing search results.
    """
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(80, 108)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)} Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Response status: {response.status_code}")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    seen_links = set()
    for result in soup.find_all('div', class_=['g', 'tF2Cxc']):
        if len(results) >= num_results:
            break
        
        title_elem = result.find('h3')
        link_elem = result.find('a')
        snippet_elem = result.find(['div', 'span'], class_=['VwiC3b', 'yXK7lf', 'MUxGbd', 'yDYNvb', 'lyLwlc', 'lEBKkf'])
        
        if title_elem and link_elem:
            title = title_elem.text
            link = link_elem['href']
            if link in seen_links:
                continue
            seen_links.add(link)
            snippet = snippet_elem.text.strip() if snippet_elem else 'No description available'
            results.append({'title': title, 'link': link, 'snippet': snippet})
    
    return results

def fetch_and_extract(url):
    """Fetch and extract the main content from a given URL using trafilatura.

    Args:
        url (str): The URL to fetch and extract content from.

    Returns:
        str: The extracted main content of the webpage, or None if extraction fails.
    """
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None
    content = trafilatura.extract(downloaded, include_comments=False, 
                                  include_tables=True, no_fallback=False)
    return content

@command()
async def google(query, num_results=15, fetch_first=False, context=None):
    """Perform a Google search and return the results.

    Args:
        query (str): The search query.
        num_results (int, optional): The number of results to return. Defaults to 15.
        fetch_first (bool, optional): Whether to fetch the content of the first result. Defaults to False.
        context (object, optional): The context object for the current session.

    Returns:
        str: Formatted string containing search results and optionally the content of the first result.

    Example:
        [
            { "google": { "query": "Python programming", "num_results": 3, "fetch_first": true } }
        ]
    """
    try:
        search_results = await web_search(query, num_results)
        if not search_results:
            return "No results found. Please check the parsing logic or Google's response structure."
        
        formatted_results = []
        for result in search_results:
            formatted_result = f"Title: {result['title']}\nLink: {result['link']}\nDescription: {result['snippet']}"
            if fetch_first and len(formatted_results) == 0:
                content = fetch_and_extract(result['link'])
                if content:
                    formatted_result += f"\n\nExtracted Content:\n{content[:500]}..."
            formatted_results.append(formatted_result)
        
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Error performing Google search: {str(e)}"

@command()
async def fetch_webpage(url, context=None):
    """Fetch and extract the main content from a given URL.

    Args:
        url (str): The URL to fetch and extract content from.
        context (object, optional): The context object for the current session.

    Returns:
        str: The extracted main content of the webpage, or an error message if extraction fails.

    Example:
        [
            { "fetch_webpage": { "url": "https://www.example.com/article" } }
        ]
    """
    content = fetch_and_extract(url)
    if content is None:
        return f"Failed to fetch or extract content from {url}"
    return f"Extracted content from {url}:\n\n{content}"

if __name__ == "__main__":
    # This block is for testing purposes
    import asyncio
    
    async def test_google_search():
        results = await google("Padres schedule", num_results=5, fetch_first=True)
        print(results)
    
    asyncio.run(test_google_search())
