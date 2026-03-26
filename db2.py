
import mysql.connector
import json

FOLDER_PATH = "pdp/pdp"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "actowiz",
}

DATABASE = 'join_database'

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_connection_thread():
    return mysql.connector.connect(**{**DB_CONFIG,"database":DATABASE})

def create_database(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
    cursor.execute(f"USE {DATABASE}")
def create_table(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Product (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(255),
        brand VARCHAR(100),
        media JSON,
        product_details JSON
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Price (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT,
        weight VARCHAR(50),
        original_price DECIMAL(10,2),
        discounted_price DECIMAL(10,2),
        is_selected BOOLEAN,
        FOREIGN KEY (product_id) REFERENCES Product(id)
    )
    """)

import json

def insert_multiple_data(cursor, data_list):

    if not data_list:
        return 0

    product_values = []

    for data in data_list:
        product_values.append((
            data.product_name,
            data.brand,
            json.dumps(data.media.model_dump()) if data.media else None,
            json.dumps(data.product_details) if data.product_details else None
        ))

    product_query = """
    INSERT INTO Product (product_name, brand, media, product_details)
    VALUES (%s, %s, %s, %s)
    """

    cursor.executemany(product_query, product_values)

    # Get first inserted ID
    start_id = cursor.lastrowid
    product_ids = list(range(start_id, start_id + len(product_values)))

   
    price_values = []

    for i, data in enumerate(data_list):
        product_id = product_ids[i]

        for p in data.price:
            price_values.append((
                product_id,
                p.weight,
                p.original,
                p.discounted,
                p.is_selected
            ))

    price_query = """
    INSERT INTO Price (product_id, weight, original_price, discounted_price, is_selected)
    VALUES (%s, %s, %s, %s, %s)
    """

    if price_values:
        cursor.executemany(price_query, price_values)

    return len(product_values)