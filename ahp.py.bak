import click
import requests
import json

API_BASE_URL = "http://localhost:8000"  # Replace with your API base URL

@click.group()
def cli():
    pass

@cli.command()
@click.option("--username", prompt=True, help="Username for login")
@click.option("--password", prompt=True, hide_input=True, help="Password for login")
def login(username, password):
    url = f"{API_BASE_URL}/token"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        with open(".token", "w") as file:
            file.write(token)
        click.echo("Login successful. Token saved.")
    else:
        click.echo("Login failed. Please check your credentials.")

@cli.command()
@click.option("--title", prompt=True, help="Title of the content")
@click.option("--description", prompt=True, help="Description of the content")
@click.option("--category", prompt=True, help="Category of the content")
@click.option("--content-type", prompt=True, help="Type of the content")
@click.option("--data", prompt=True, help="Data of the content (JSON)")
def publish(title, description, category, content_type, data):
    url = f"{API_BASE_URL}/publish"
    headers = {
        "Authorization": f"Bearer {get_token()}"
    }
    payload = {
        "title": title,
        "description": description,
        "category": category,
        "content_type": content_type,
        "data": json.loads(data)
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        click.echo("Content published successfully.")
    else:
        click.echo("Failed to publish content.")

@cli.command()
@click.option("--query", prompt=True, help="Search query")
def search(query):
    url = f"{API_BASE_URL}/search"
    headers = {
        "Authorization": f"Bearer {get_token()}"
    }
    params = {
        "query": query
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        results = response.json()
        click.echo(f"Search Results for '{query}':")
        for result in results:
            click.echo(f"Title: {result['title']}")
            click.echo(f"Description: {result['description']}")
            click.echo(f"Category: {result['category']}")
            click.echo(f"Content Type: {result['content_type']}")
            click.echo(f"Data: {result['data']}")
            click.echo("---")
    else:
        click.echo("Search failed.")

def get_token():
    try:
        with open(".token", "r") as file:
            token = file.read().strip()
        return token
    except FileNotFoundError:
        click.echo("No token found. Please login first.")
        exit(1)

if __name__ == "__main__":
    cli()
