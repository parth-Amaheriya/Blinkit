import os
import time
import threading
from parser import parse_file
from db import (
    FOLDER_PATH,
    get_connection_thread,
    get_connection,
    create_table,
    create_database,
    insert_multiple_data
)

BATCH_SIZE=2000
MAX_WORKERS=5

batch=[]
batch_lock=threading.Lock()
db_threads=[]

def insert_batch(batch_to_insert):
    conn=get_connection_thread()
    cursor=conn.cursor()
    insert_multiple_data(cursor, batch_to_insert)
    conn.commit()
    cursor.close()
    conn.close()

def process_file(file_path):
    try:
        result=parse_file(file_path)
        if result:
            trigger_db_insert(result)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

def trigger_db_insert(parsed_item):
    global batch, db_threads
    with batch_lock:
        batch.append(parsed_item)
        if len(batch) >= BATCH_SIZE:
            batch_copy=batch.copy()
            batch.clear()
            t=threading.Thread(target=insert_batch, args=(batch_copy,))
            t.start()
            db_threads.append(t)

            if len(db_threads) >= MAX_WORKERS:
                for th in db_threads:
                    th.join()
                db_threads.clear()

def main():
    start_time=time.time()

    conn=get_connection()
    cursor=conn.cursor()
    create_database(cursor)
    create_table(cursor)
    conn.commit()
    cursor.close()
    conn.close()

    parser_threads=[]
    for f in os.listdir(FOLDER_PATH):
        print("Processing :- ",f)
        file_path=os.path.join(FOLDER_PATH, f)
        t=threading.Thread(target=process_file, args=(file_path,))
        t.start()
        parser_threads.append(t)

        if len(parser_threads) >= MAX_WORKERS:
            for th in parser_threads:
                th.join()
            parser_threads.clear()

    for th in parser_threads:
        th.join()

    with batch_lock:
        if batch:
            t=threading.Thread(target=insert_batch, args=(batch.copy(),))
            t.start()
            db_threads.append(t)
            batch.clear()

    for th in db_threads:
        th.join()

    end_time=time.time()
    print(f"Total runtime: {end_time - start_time} seconds")


if __name__ == "__main__":
    main()

