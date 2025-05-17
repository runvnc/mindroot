#!/bin/bash

# Generate a random JWT secret key (32 characters)
JWT_SECRET_KEY=$(openssl rand -hex 16)

# Generate a random admin username (8 characters)
ADMIN_USER="admin_$(openssl rand -hex 4)"

# Generate a random admin password (12 characters)
ADMIN_PASS=$(openssl rand -base64 12 | tr -d '/+=' | cut -c1-12)

# Create a .env file with the generated credentials
cat > .env << EOF
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ADMIN_USER=${ADMIN_USER}
ADMIN_PASS=${ADMIN_PASS}
EOF

# Create a credentials.txt file for the user
cat > credentials.txt << EOF
=== MindRoot Credentials ===

Admin Username: ${ADMIN_USER}
Admin Password: ${ADMIN_PASS}
JWT Secret Key: ${JWT_SECRET_KEY}

Keep this information secure!
EOF

echo "Credentials generated successfully!"
echo "Admin Username: ${ADMIN_USER}"
echo "Admin Password: ${ADMIN_PASS}"
echo "JWT Secret Key: ${JWT_SECRET_KEY}"
echo ""
echo "These credentials have been saved to:"
echo "- .env file (for Docker Compose)"
echo "- credentials.txt (for your records)"
