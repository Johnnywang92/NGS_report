import os
import time
import json
import mysql.connector
import shutil
import subprocess

DATA_DIR = 'data'
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
ERROR_DIR = os.path.join(DATA_DIR, 'error')
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

def get_db_conn():
    return mysql.connector.connect(
        host='localhost',
        port=3307,
        user='gene_reports',
        password='rooT@321',
        database='gene_data'
    )

def import_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sample_id = list(data.keys())[0]
    info = data[sample_id]
    name = info.get('name', '')
    status = 'pending'  # 可根据实际情况调整
    # 插入到samples表
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO samples (id, name, status) VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE name=VALUES(name), status=VALUES(status)",
        (sample_id, name, status)
    )
    # 插入到gene_data表（如有）
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS gene_data ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "patient_id VARCHAR(255) NOT NULL,"
        "raw_data JSON NOT NULL,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    cursor.execute(
        "INSERT INTO gene_data (patient_id, raw_data) VALUES (%s, %s)",
        (sample_id, json.dumps(data, ensure_ascii=False))
    )
    conn.commit()
    cursor.close()
    conn.close()

def scan_and_import():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(DATA_DIR, filename)
            try:
                import_json_file(filepath)
                print(f"Imported {filename}")
                shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
            except Exception as e:
                print(f"Failed to import {filename}: {e}")
                shutil.move(filepath, os.path.join(ERROR_DIR, filename))

if __name__ == '__main__':
    while True:
        scan_and_import()
        time.sleep(60)

@app.route('/import_samples_once')
def import_samples_once():
    try:
        subprocess.run(['python', 'import_samples.py'], timeout=60)
        return '导入完成'
    except Exception as e:
        return f'导入失败: {e}' 