#!/bin/bash

# Improved PostgreSQL Setup Script for macOS

set -e  # Exit immediately if a command exits with a non-zero status.

# Function to generate a random password
generate_password() {
    openssl rand -base64 12
}

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Installing via Homebrew..."
    brew install postgresql@14
    brew services start postgresql@14
    sleep 5  # Wait for PostgreSQL to start
else
    echo "PostgreSQL is already installed."
    brew services start postgresql@14
fi

# Check if .env file exists and source it
if [ -f .env ]; then
    echo "Existing .env file found. Attempting to use cached credentials."
    set +e  # Temporarily disable exit on error
    source .env
    DB_USER=$(echo $DATABASE_URL | sed -n 's/^postgresql:\/\/\([^:]*\):.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)$/\1/p')
    set -e  # Re-enable exit on error
    
    if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
        echo "Error: Failed to extract database credentials from .env file."
        echo "Generating new credentials."
        DB_USER="dayplanner_user"
        DB_PASSWORD=$(generate_password)
        DB_NAME="day_planner"
    else
        echo "Successfully extracted credentials from .env file."
        echo "Username: $DB_USER"
        echo "Database: $DB_NAME"
    fi
else
    echo "No existing .env file. Generating new credentials."
    DB_USER="dayplanner_user"
    DB_PASSWORD=$(generate_password)
    DB_NAME="day_planner"
fi

# Check if the user and database already exist
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Database $DB_NAME already exists. Skipping creation."
else
    echo "Creating new user and database..."
    # Create user and database
    psql postgres <<EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

    echo "User and database created successfully."
    
    # Create or update .env file
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME" > .env
    echo ".env file created/updated with database credentials."
fi

# Create .env.sample file if it doesn't exist
if [ ! -f .env.sample ]; then
    echo "DATABASE_URL=postgresql://username:password@localhost/day_planner" > .env.sample
    echo ".env.sample file created."
fi

# Add .env to .gitignore if it doesn't exist
if ! grep -q "^.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "Added .env to .gitignore"
fi

echo "Setup complete! Your database is ready to use."
echo "Username: $DB_USER"
echo "Database: $DB_NAME"
echo "Database URL is saved in the .env file."