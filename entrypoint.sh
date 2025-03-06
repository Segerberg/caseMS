#!/bin/bash
set -e

# Function to check if database exists and has tables
check_db() {
  if [ ! -f "$1" ]; then
    return 1  # Database doesn't exist
  fi

  # Check if AERENDE table exists
  tables=$(sqlite3 "$1" "SELECT name FROM sqlite_master WHERE type='table' AND name='AERENDE';")
  if [ -z "$tables" ]; then
    return 1  # Table doesn't exist
  fi

  return 0  # Database exists and has tables
}

# Initialize the database if needed
if ! check_db "/app/case_management.db"; then
  echo "Database not found or incomplete. Initializing..."
  python init_db.py
else
  echo "Database already exists. Skipping initialization."
fi

# Run the application
exec "$@"