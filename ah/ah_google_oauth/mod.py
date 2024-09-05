from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from ..services import service
from ..commands import command
import pickle
import os

# Set up the OAuth flow
flow = Flow.from_client_secrets_file(
    'path/to/your/client_secret.json',
    scopes=['https://www.googleapis.com/auth/cse']
)

# Get the search engine ID from the environment
SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

@service()
async def authenticate():
    if not os.path.exists('token.pickle'):
        flow.run_local_server(port=8080, prompt='consent')
        credentials = flow.credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    else:
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    return credentials

@service()
async def web_search(query, num_results=5):
    credentials = await authenticate()
    service = build('customsearch', 'v1', credentials=credentials)
    
    try:
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=num_results).execute()
        results = []
        for item in res['items']:
            results.append({
                'title': item['title'],
                'link': item['link'],
                'snippet': item.get('snippet', 'No description available')
            })
        return results
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

@command()
async def google(query, num_results=5, context=None):
    """Perform a Google search using OAuth and return the results.

    Parameters:
    query (str): The search query.
    num_results (int, optional): The number of results to return. Default is 5.

    Example:
    [
        { "google": { "query": "Python programming", "num_results": 3 } }
    ]
    """
    try:
        search_results = await web_search(query, num_results)
        formatted_results = "\n\n".join([f"Title: {result['title']}\nLink: {result['link']}\nDescription: {result['snippet']}" for result in search_results])
        return formatted_results
    except Exception as e:
        return f"Error performing Google search: {str(e)}"

if __name__ == "__main__":
    # This block is for testing purposes
    import asyncio
    
    async def test_google_search():
        results = await google("Python programming", num_results=3)
        print(results)
    
    asyncio.run(test_google_search())
