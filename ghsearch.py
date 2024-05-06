import requests

def search_github_plugins(tag="pluggy-plugin"):
    url = f"https://api.github.com/search/repositories?q=topic:{tag}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['items']  # List of repositories
    else:
        return None

# Fetch plugins tagged as 'pluggy-plugin'
plugins = search_github_plugins()
if plugins:
    for plugin in plugins:
        print(plugin['name'], plugin['html_url'])

