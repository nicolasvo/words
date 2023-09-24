#!/bin/bash

# Check if the specified DB_PATH exists
if [ -e "$DB_PATH" ]; then
    echo "Found $DB_PATH"
    # If it exists, run app.py
    python3 app.py
else
    echo "File $DB_PATH not found"
    # If it doesn't exist, run init_db.py and copy words.db to $DB_PATH
    python3 init_db.py words.db
    cp words.db "$DB_PATH"
    echo "Initialized and copied words.db to $DB_PATH"
    # Then, run app.py
    python3 app.py
fi
