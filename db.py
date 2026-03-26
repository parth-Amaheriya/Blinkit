
import mysql.connector
import json

FOLDER_PATH = "pdp/pdp"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "actowiz",
}

DATABASE = 'Blinkit2'


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_connection_thread():
    return mysql.connector.connect(**{**DB_CONFIG,"database":DATABASE})

def create_database(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    cursor.execute(f"USE {DATABASE}")

def create_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,

        product_name TEXT,
        brand TEXT,

        price JSON,
        media JSON,

        product_details JSON
    )
    """)


def insert_multiple_data(cursor, product_list):
    if not product_list:
        return 0

    query = """
    INSERT INTO products (
        product_name,
        brand,
        price,
        media,
        product_details
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    rows = []
    for pro in product_list:
        rows.append((
            pro.product_name,
            pro.brand,
            json.dumps([p.model_dump() for p in pro.price]) if pro.price else None,
            json.dumps(pro.media.model_dump()) if pro.media else None,
            json.dumps(pro.product_details) if pro.product_details else None
        ))

    cursor.executemany(query, rows)
    return cursor.rowcount