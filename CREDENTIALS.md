# MindRoot Credentials Setup

## Automatic Credential Generation

This project includes a script to automatically generate secure random credentials for your MindRoot deployment.

### Steps to Generate Credentials

1. Make the script executable:
   ```bash
   chmod +x generate_credentials.sh
   ```

2. Run the script:
   ```bash
   ./generate_credentials.sh
   ```

3. The script will generate:
   - A random JWT secret key
   - A random admin username
   - A random admin password

4. These credentials will be saved to:
   - `.env` file (used by Docker Compose)
   - `credentials.txt` (for your records)

5. The script will also display the credentials in the terminal.

### Starting MindRoot with Generated Credentials

After generating credentials, you can start MindRoot using Docker Compose:

```bash
docker-compose up -d
```

The container will automatically use the credentials from the `.env` file.

### Sharing Credentials with Users

You can share the generated admin credentials with your users by:

1. Copying the information from `credentials.txt`
2. Securely transmitting the credentials to your users

### Manual Configuration

If you prefer to set credentials manually:

1. Create a `.env` file with the following content:
   ```
   JWT_SECRET_KEY=your_custom_jwt_secret
   ADMIN_USER=your_admin_username
   ADMIN_PASS=your_admin_password
   ```

2. Start MindRoot using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Security Considerations

- Keep your `.env` and `credentials.txt` files secure
- Change the admin password regularly
- Consider using a password manager to store credentials
- For production deployments, consider using a secrets management solution
