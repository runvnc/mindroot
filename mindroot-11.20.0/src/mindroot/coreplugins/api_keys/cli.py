import click
from .mod import api_key_manager

@click.group()
def cli():
    """API Key management commands"""
    pass

@cli.command()
@click.argument('username')
@click.option('--description', '-d', default='', help='Description of the API key')
def create(username: str, description: str):
    """Create a new API key for a user"""
    key = api_key_manager.create_key(username, description)
    click.echo(f"Created API key for {username}: {key}")

@cli.command()
@click.argument('api_key')
def delete(api_key: str):
    """Delete an API key"""
    if api_key_manager.delete_key(api_key):
        click.echo(f"Deleted API key: {api_key}")
    else:
        click.echo(f"API key not found: {api_key}")

@cli.command()
@click.option('--username', '-u', help='Filter keys by username')
def list(username: str = None):
    """List API keys"""
    keys = api_key_manager.list_keys(username)
    if not keys:
        click.echo("No API keys found")
        return
    
    for key in keys:
        click.echo(f"Key: {key['key']}")
        click.echo(f"Username: {key['username']}")
        click.echo(f"Description: {key['description']}")
        click.echo(f"Created: {key['created_at']}")
        click.echo("---")

if __name__ == '__main__':
    cli()
