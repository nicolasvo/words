import sqlite3
import sys

# Check if the user provided a database name as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python your_script.py <db_name>")
    sys.exit(1)

# Get the database name from the command-line argument
db_name = sys.argv[1]

# Create a SQLite database connection (change the database name as needed)
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create the users table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )
"""
)

# Create the user_submissions table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_submissions (
        submission_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        original_word TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
"""
)

# Create the translations table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS translations (
        translation_id INTEGER PRIMARY KEY,
        submission_id INTEGER,
        language_code TEXT,
        translated_word TEXT,
        FOREIGN KEY (submission_id) REFERENCES user_submissions(submission_id)
    )
"""
)


# Function to create the UserLanguages table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_languages (
        user_id INTEGER,
        language_code TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        PRIMARY KEY (user_id, language_code)
    )
"""
)


# Commit and close the database connection
conn.commit()
conn.close()
