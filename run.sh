#!/bin/bash

# Check if /data/words.db exists
if [ -e "/data/words.db" ]; then
    echo "Found /data/words.db"
    # If it exists, run app.py
    python3 app.py
else
    echo "File /data/words.db not found"
    # If it doesn't exist, run init_db.py and copy words.db to /data/
    python3 init_db.py words.db
    cp words.db /data/words.db
    echo "Initialized and copied words.db to /data/"
    # Then, run app.py
    python3 app.py
fi
