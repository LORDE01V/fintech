import sqlite3

def init_database():
    conn = sqlite3.connect('expense.db')
    cur = conn.cursor()
    
    # Create tables
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS user_login (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(30) NOT NULL UNIQUE,
            email VARCHAR(30) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS user_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pdate DATE NOT NULL,
            expense VARCHAR(30) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            pdescription VARCHAR(100),
            category VARCHAR(30),
            transaction_type VARCHAR(10),
            FOREIGN KEY (user_id) REFERENCES user_login(user_id)
        );
        
        CREATE TABLE IF NOT EXISTS user_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(30) NOT NULL,
            type VARCHAR(10) NOT NULL
        );
    ''')
    
    # Insert default categories
    categories = [
        ('Housing', 'expense'),
        ('Transport', 'expense'),
        ('Food', 'expense'),
        ('Utilities', 'expense'),
        ('Entertainment', 'expense'),
        ('Salary', 'income'),
        ('Investment', 'income')
    ]
    
    cur.executemany('INSERT OR IGNORE INTO user_categories (name, type) VALUES (?, ?)', categories)
    conn.commit()
    conn.close() 