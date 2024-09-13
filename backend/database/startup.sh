#!/bin/bash

# PostgreSQL Portable Setup Script

set -e  # Exit immediately if a command exits with a non-zero status.

# Get the current directory
CURRENT_DIR=$(pwd)
POSTGRES_BASE_DIR="$CURRENT_DIR/postgresql_portable"
POSTGRES_BIN_DIR="$POSTGRES_BASE_DIR/bin"
POSTGRES_DATA_DIR="$POSTGRES_BASE_DIR/data"
POSTGRES_DOWNLOAD_URL="https://github.com/uliwitness/postgresql-portable/releases/download/v14.0/PostgreSQL-Portable-14.0.dmg"  # Update URL if necessary
POSTGRES_DMG="$CURRENT_DIR/postgresql_portable.dmg"
POSTGRES_MOUNT_DIR="/Volumes/PostgreSQL Portable"

# Ensure bin and data directories exist
mkdir -p "$POSTGRES_BASE_DIR"
mkdir -p "$POSTGRES_DATA_DIR"

# Download PostgreSQL Portable if the bin directory is empty
if [ ! -d "$POSTGRES_BIN_DIR" ] || [ -z "$(ls -A $POSTGRES_BIN_DIR)" ]; then
    echo "PostgreSQL Portable binaries not found. Downloading..."
    
    # Download PostgreSQL Portable DMG
    curl -L "$POSTGRES_DOWNLOAD_URL" -o "$POSTGRES_DMG"
    
    # Check if the download succeeded
    if [ ! -f "$POSTGRES_DMG" ] || [ $(stat -f%z "$POSTGRES_DMG") -lt 10000 ]; then
        echo "Error: Failed to download the PostgreSQL Portable DMG file. Please check the URL or your internet connection."
        exit 1
    fi
    
    echo "Mounting the DMG..."
    hdiutil attach "$POSTGRES_DMG" -mountpoint "$POSTGRES_MOUNT_DIR"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to mount the DMG. Please ensure the downloaded file is a valid disk image."
        exit 1
    fi
    
    echo "Copying PostgreSQL Portable binaries..."
    cp -r "$POSTGRES_MOUNT_DIR/PostgreSQL Portable/bin" "$POSTGRES_BASE_DIR/"
    
    echo "Unmounting the DMG..."
    hdiutil detach "$POSTGRES_MOUNT_DIR"
    
    echo "PostgreSQL Portable binaries set up at $POSTGRES_BIN_DIR."
fi

# Function to generate a random password
generate_password() {
    openssl rand -base64 12
}

# Check if PostgreSQL Portable is initialized
if [ ! -d "$POSTGRES_DATA_DIR" ] || [ ! "$(ls -A $POSTGRES_DATA_DIR)" ]; then
    echo "Initializing PostgreSQL Portable data directory..."
    "$POSTGRES_BIN_DIR/initdb" -D "$POSTGRES_DATA_DIR"
else
    echo "PostgreSQL Portable data directory already initialized."
fi

# Start PostgreSQL Portable
echo "Starting PostgreSQL Portable..."
"$POSTGRES_BIN_DIR/pg_ctl" -D "$POSTGRES_DATA_DIR" -l logfile start
sleep 5  # Wait for PostgreSQL to start

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
if "$POSTGRES_BIN_DIR/psql" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Database $DB_NAME already exists. Skipping creation."
else
    echo "Creating new user and database..."
    # Create user and database
    "$POSTGRES_BIN_DIR/psql" postgres <<EOF
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

echo "Setup complete! Your PostgreSQL Portable database is ready to use."
echo "Username: $DB_USER"
echo "Database: $DB_NAME"
echo "Database URL is saved in the .env file."
