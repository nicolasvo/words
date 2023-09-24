from fastapi import Cookie
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from constants import db_path

# Define a User model using SQLAlchemy
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


# Define a function to establish a SQLite database connection
def connect_db():
    import sqlite3

    return sqlite3.connect(db_path)


# Function to check if a user is logged in using a cookie
async def get_current_user(username: str = Cookie(None)):
    if username:
        db_user = get_user_by_username(username)
        if db_user:
            return db_user
    return None


# Function to get a user by username from the database
def get_user_by_username(username: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    conn.close()
    if not user is None:
        return {
            "id": user[0],
            "username": user[1],
            "password": user[2],
        }
    return user


# Function to create a new user
def create_user(username: str, password: str):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
    )
    conn.commit()

    conn.close()


def insert_user_word_and_translations(user_id, original_word, translations):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Insert the original word into UserSubmissions table
        cursor.execute(
            "INSERT INTO user_submissions (user_id, original_word) VALUES (?, ?)",
            (user_id, original_word),
        )
        submission_id = cursor.lastrowid  # Get the ID of the newly inserted submission

        # Insert translations into Translations table for each language
        for language_code, translated_word in translations.items():
            cursor.execute(
                "INSERT INTO translations (submission_id, language_code, translated_word) VALUES (?, ?, ?)",
                (submission_id, language_code, translated_word),
            )

        conn.commit()
        return submission_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_user_word_and_translations(submission_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # Delete the word from the Translations table
        cursor.execute(
            """
            DELETE FROM translations
            WHERE submission_id = ?
        """,
            (submission_id,),
        )

        # Delete the word from the UserSubmissions table
        cursor.execute(
            """
            DELETE FROM user_submissions
            WHERE submission_id = ?
        """,
            (submission_id,),
        )

        # Commit the transaction to save changes
        conn.commit()
    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_user_translations(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Retrieve translated words for the current user
        cursor.execute(
            """
            SELECT us.submission_id, us.original_word, t.language_code, t.translation_id, t.translated_word
            FROM user_submissions us
            JOIN translations t ON us.submission_id = t.submission_id
            WHERE us.user_id = ?
        """,
            (user_id,),
        )

        translations = cursor.fetchall()

        # Organize the translations into a list of dictionaries
        user_translations = []
        word_entry = {}
        submission_id_current = None
        for index, (
            submission_id,
            original_word,
            language_code,
            translation_id,
            translated_word,
        ) in enumerate(sorted(translations)):
            if not submission_id_current:
                submission_id_current = submission_id
            if submission_id_current != submission_id:
                user_translations.append(word_entry)
                word_entry = {}
                submission_id_current = submission_id
            word_entry["submission_id"] = submission_id
            word_entry["origin"] = original_word
            word_entry[language_code] = {
                "word": translated_word,
                "translation_id": translation_id,
            }
            if index == len(translations) - 1:
                user_translations.append(word_entry)
        return user_translations
    finally:
        conn.close()


def add_new_language(user_id, new_language_code):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if the new language already exists in UserLanguages table
        cursor.execute(
            """
            SELECT language_code
            FROM user_languages
            WHERE user_id = ? AND language_code = ?
        """,
            (user_id, new_language_code),
        )

        existing_language = cursor.fetchone()

        # If the language doesn't exist, insert it into UserLanguages table
        if not existing_language:
            cursor.execute(
                """
                INSERT INTO user_languages (user_id, language_code)
                VALUES (?, ?)
            """,
                (user_id, new_language_code),
            )

        # Identify the user's submitted words for which translations need to be added
        cursor.execute(
            """
            SELECT submission_id
            FROM user_submissions
            WHERE user_id = ?
        """,
            (user_id,),
        )

        submission_ids = cursor.fetchall()

        # Insert new entries for translations with the new language code and empty translated word
        for submission_id in submission_ids:
            cursor.execute(
                """
                INSERT INTO translations (submission_id, language_code, translated_word)
                VALUES (?, ?, ?)
            """,
                (submission_id[0], new_language_code, ""),
            )

        conn.commit()
    finally:
        conn.close()


def get_user_languages(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Retrieve the list of languages associated with the user
        cursor.execute(
            """
            SELECT language_code
            FROM user_languages
            WHERE user_id = ?
        """,
            (user_id,),
        )

        languages = [row[0] for row in cursor.fetchall()]
        return languages
    finally:
        conn.close()


def delete_user_language(user_id, language_code):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # Delete the language from the UserLanguages table
        cursor.execute(
            """
            DELETE FROM user_languages
            WHERE user_id = ? AND language_code = ?
        """,
            (user_id, language_code),
        )

        # Delete the corresponding translations from the Translations table
        cursor.execute(
            """
            DELETE FROM translations
            WHERE submission_id IN (
                SELECT submission_id
                FROM user_submissions
                WHERE user_id = ?
            ) AND language_code = ?
        """,
            (user_id, language_code),
        )

        # Commit the transaction to save changes
        conn.commit()
    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_user_languages(user_id, old_languages, updated_languages):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Begin a transaction
        conn.execute("BEGIN TRANSACTION")

        # Calculate differences: languages to add and languages to delete
        print(updated_languages)
        print(old_languages)
        languages_to_add = list(set(updated_languages) - set(old_languages))
        languages_to_delete = list(set(old_languages) - set(updated_languages))

        # Add languages to UserLanguages table
        for language_code in languages_to_add:
            cursor.execute(
                """
                INSERT INTO user_languages (user_id, language_code)
                VALUES (?, ?)
            """,
                (user_id, language_code),
            )

        # Remove languages from UserLanguages table
        for language_code in languages_to_delete:
            cursor.execute(
                """
                DELETE FROM user_languages
                WHERE user_id = ? AND language_code = ?
            """,
                (user_id, language_code),
            )

        # Add translations for new languages with empty values
        for language_code in languages_to_add:
            cursor.execute(
                """
                INSERT INTO translations (submission_id, language_code, translated_word)
                SELECT submission_id, ?, ''
                FROM user_submissions
                WHERE user_id = ?
            """,
                (language_code, user_id),
            )

        # Remove translations for deleted languages
        for language_code in languages_to_delete:
            cursor.execute(
                """
                DELETE FROM translations
                WHERE submission_id IN (
                    SELECT submission_id
                    FROM user_submissions
                    WHERE user_id = ?
                ) AND language_code = ?
            """,
                (user_id, language_code),
            )

        # Commit the transaction to save changes
        conn.commit()
    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        raise e
    finally:
        conn.close()
