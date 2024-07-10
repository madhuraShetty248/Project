import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, 
                  start_lat REAL, start_lon REAL,
                  end_lat REAL, end_lon REAL, 
                  distance REAL, toll REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def add_user(username):
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def add_transaction(username, start_lat, start_lon, end_lat, end_lon, distance, toll):
    conn = sqlite3.connect('toll_system.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user_id = c.fetchone()[0]
    c.execute('''INSERT INTO transactions 
                 (user_id, start_lat, start_lon, end_lat, end_lon, distance, toll) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
              (user_id, start_lat, start_lon, end_lat, end_lon, distance, toll))
    conn.commit()
    conn.close()

def get_transaction_history(username):
    conn = sqlite3.connect('toll_system.db')
    query = '''SELECT transactions.* FROM transactions
               JOIN users ON transactions.user_id = users.id
               WHERE users.username = ?'''
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df