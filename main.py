
import os
import time
from parser import parse_file
from db2 import FOLDER_PATH, get_connection_thread,get_connection, create_table, create_database, insert_multiple_data
from concurrent.futures import ThreadPoolExecutor, as_completed

BATCH_SIZE = 2000
MAX_WORKERS =8

def insert_batch(batch):
    conn = get_connection_thread()
    cursor = conn.cursor()
    insert_multiple_data(cursor, batch)
    conn.commit()
    cursor.close()
    conn.close()

def process_file(file_path):
    try:
        return parse_file(file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def main():
    start_time = time.time()
    conn = get_connection()
    cursor = conn.cursor()
    create_database(cursor)
    create_table(cursor)
    conn.commit()
    cursor.close()
    conn.close()
    
    batch = []
    db_futures = []
    count=0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as parser_executor:
        data = {}
        for f in os.listdir(FOLDER_PATH):
            file_path = os.path.join(FOLDER_PATH, f)
            future = parser_executor.submit(process_file, file_path)
            data[future] = f
            
            count+=1
            if count>=2000:
                break

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as db_executor:
            for future in as_completed(data):
                result = future.result()
                if result:
                    batch.append(result)
                if len(batch) >= BATCH_SIZE:
                    db_futures.append(db_executor.submit(insert_batch, batch.copy()))
                    batch.clear()

            if batch:
                db_futures.append(db_executor.submit(insert_batch, batch.copy()))
        for db_future in as_completed(db_futures):
            db_future.result()  

    end_time= time.time()
    print(f"Total runtime: {end_time - start_time} seconds")

if __name__ == "__main__":
    main()
