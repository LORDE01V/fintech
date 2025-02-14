import sqlite3

def init_database():
    conn = sqlite3.connect('expense.db')
    cur = conn.cursor()
    
    # Create tables
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS Customers (
            CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            DateOfBirth TEXT NOT NULL,
            Email TEXT UNIQUE NOT NULL,
            Phone TEXT NOT NULL,
            Address TEXT NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS user_login (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(30) NOT NULL UNIQUE,
            email VARCHAR(30) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL  # Increased length for password hash
        );
        
        CREATE TABLE IF NOT EXISTS user_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pdate DATE NOT NULL,
            expense VARCHAR(10) NOT NULL,
            amount INTEGER NOT NULL,
            pdescription VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES user_login(user_id)
        );
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    print("Database initialized") 