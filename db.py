
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection(database_name=None):
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3307)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=database_name or os.getenv("DB_NAME", "yottaflex_db")
        )

        return connection

    except mysql.connector.Error as error:
        print("Database connection failed:", error)
        return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")
        print("Connected database:", cursor.fetchone()[0])

        cursor.execute("SHOW TABLES")
        print("\nAvailable tables:")

        for table in cursor.fetchall():
            print("-", table[0])

        cursor.close()
        connection.close()

        print("\nDatabase connection successful!")
