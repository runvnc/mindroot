import click
import sys
import os
import json
import bcrypt
import secrets
import uuid
from datetime import datetime
from pathlib import Path

USER_DATA_ROOT = 'data/users'
KEYS_DIR = 'data/apikeys'

@click.group()
def cli():
    """MindRoot CLI for user and API key management"""
    pass

@cli.group()
def user():
    """User management commands"""
    pass

@user.command()
@click.argument('username')
@click.argument('email')
@click.option('--password', '-p', default=None, help='Password (auto-generated if not provided)')
@click.option('--roles', '-r', default='user,verified', help='Comma-separated roles')
def create(username, email, password, roles):
    """Create a new user"""
    if not password:
        password = secrets.token_urlsafe(16)
    user_dir = os.path.join(USER_DATA_ROOT, username)
    os.makedirs(USER_DATA_ROOT, exist_ok=True)
    if os.path.exists(user_dir):
        click.echo(f'Error: Username {username} already exists', err=True)
        sys.exit(1)
    os.makedirs(user_dir)
    role_list = []
    if roles:
        role_list = [r.strip() for r in roles.split(',')]
    if 'user' not in role_list:
        role_list.append('user')
    now = datetime.utcnow().isoformat()
    auth_data = {
        'username': username,
        'email': email,
        'password_hash': bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        'created_at': now,
        'last_login': None,
        'email_verified': True,
        'verification_token': None,
        'verification_expires': None,
        'roles': role_list
    }
    with open(os.path.join(user_dir, 'auth.json'), 'w') as f:
        json.dump(auth_data, f, indent=2)
    with open(os.path.join(user_dir, 'settings.json'), 'w') as f:
        json.dump({}, f)
    with open(os.path.join(user_dir, 'workspace.json'), 'w') as f:
        json.dump({}, f)
    click.echo(f'Created user: {username}')
    click.echo(f'Email: {email}')
    click.echo(f'Password: {password}')
    click.echo(f'Roles: {role_list}')

@user.command()
@click.argument('username')
@click.option('--include-email', is_flag=True)
def get(username, include_email):
    """Get user info"""
    auth_file = os.path.join(USER_DATA_ROOT, username, 'auth.json')
    if not os.path.exists(auth_file):
        click.echo(f'User {username} not found', err=True)
        sys.exit(1)
    with open(auth_file, 'r') as f:
        data = json.load(f)
    click.echo(f'Username: {data["username"]}')
    if include_email:
        click.echo(f'Email: {data.get("email", "")}')
    click.echo(f'Roles: {data.get("roles", [])}')
    click.echo(f'Created: {data.get("created_at", "")}')
    click.echo(f'Verified: {data.get("email_verified", False)}')

@user.command()
def list():
    """List all users"""
    if not os.path.exists(USER_DATA_ROOT):
        click.echo('No users found')
        return
    users = [d for d in os.listdir(USER_DATA_ROOT) if os.path.isdir(os.path.join(USER_DATA_ROOT, d))]
    if users:
        click.echo('Users:')
        for u in users:
            click.echo(f'  {u}')
    else:
        click.echo('No users found')

@cli.group()
def apikey():
    """API key management commands"""
    pass

@apikey.command()
@click.argument('username')
@click.option('--description', '-d', default='', help='Description of the key')
def create(username, description):
    """Create an API key for a user"""
    os.makedirs(KEYS_DIR, exist_ok=True)
    api_key = str(uuid.uuid4())
    key_data = {
        'key': api_key,
        'username': username,
        'description': description,
        'created_at': datetime.utcnow().isoformat()
    }
    with open(os.path.join(KEYS_DIR, api_key + '.json'), 'w') as f:
        json.dump(key_data, f, indent=4)
    click.echo(f'Created API key for {username}')
    click.echo(f'Key: {api_key}')
    click.echo(f'Description: {description}')

@apikey.command()
@click.argument('api_key')
def delete(api_key):
    """Delete an API key"""
    key_file = os.path.join(KEYS_DIR, api_key + '.json')
    if os.path.exists(key_file):
        os.remove(key_file)
        click.echo(f'Deleted API key: {api_key}')
    else:
        click.echo(f'API key not found: {api_key}', err=True)
        sys.exit(1)

@apikey.command()
@click.option('--username', '-u', default=None, help='Filter by username')
def list(username):
    """List API keys"""
    if not os.path.exists(KEYS_DIR):
        click.echo('No API keys found')
        return
    found = False
    for fname in os.listdir(KEYS_DIR):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(KEYS_DIR, fname), 'r') as f:
            data = json.load(f)
        if username and data.get('username') != username:
            continue
        found = True
        click.echo(f'Key: {data["key"]}')
        click.echo(f'Username: {data["username"]}')
        click.echo(f'Description: {data.get("description", "")}')
        click.echo(f'Created: {data["created_at"]}')
        click.echo('---')
    if not found:
        click.echo('No API keys found')

if __name__ == '__main__':
    cli()
