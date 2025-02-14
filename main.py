from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS  # Add this import
import openai
import sqlite3
from init_db import init_database  # Add this import

warnings.filterwarnings("ignore")

load_dotenv()  # Add this to load .env file

# Add this after load_dotenv() to test
print("API Key exists?", bool(os.getenv("OPENAI_API_KEY")))  # Should print True

# Add this right after load_dotenv()
print(f"Flask Secret Key: {os.getenv('FLASK_SECRET_KEY')}")
print(f"OpenAI Key: {os.getenv('OPENAI_API_KEY')[:5]}...")  # Shows first 5 chars

app = Flask(__name__)
CORS(app)  # Add this line after creating Flask app
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)  # Add fallback
app.permanent_session_lifetime = timedelta(minutes=15)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Get the API key (works with both conda env vars and .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Access key here

# Add OpenAI client initialization
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
)

# Add validation check
if not client.api_key:
    raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY in .env file")

# Load your OpenAI API key from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/')
@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    
    query = "SELECT * FROM user_login WHERE email = ?"
    user = support.execute_query('search', query, (email,))
    
    if user and check_password_hash(user[0][3], password):
        session['user_id'] = user[0][0]
        session['user_name'] = user[0][1]
        return redirect(url_for('home'))
    
    flash("Invalid email or password")
    return redirect(url_for('login'))

@app.route('/reset', methods=['POST'])
def reset():
    if 'user_id' not in session:
        email = request.form.get('femail')
        passwd = request.form.get('password')
        hashed_password = generate_password_hash(passwd)  # Use corrected variable name
        query = "SELECT * FROM user_login WHERE email = ?"
        userdata = support.execute_query('search', query, (email,))
        if len(userdata) > 0:
            try:
                query = "UPDATE user_login SET password = ? WHERE email = ?"
                support.execute_query('insert', query, (hashed_password, email))  # Store hashed password
                flash("Password has been changed!!")
                return redirect('/')
            except:
                flash("Something went wrong!!")
                return redirect('/')
        else:
            flash("Invalid email address!!")
            return redirect('/')
    else:
        return redirect('/home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if email already exists
        query = "SELECT * FROM user_login WHERE email = ?"
        existing_user = support.execute_query("search", query, (email,))
        
        if existing_user:
            flash("Email already exists!")
            return redirect(url_for('register'))
        
        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        # Insert new user
        try:
            query = "INSERT INTO user_login (username, email, password) VALUES (?, ?, ?)"
            support.execute_query("insert", query, (username, email, hashed_password))
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration error: {e}")
            flash("Registration failed. Please try again.")
            return redirect(url_for('register'))

    return redirect(url_for('register'))

@app.route('/registration', methods=['POST'])
def registration():
    if 'user_id' not in session:
        name = request.form.get('name')
        email = request.form.get('email')
        passwd = request.form.get('password')
        if len(name) > 2 and len(email) > 5 and len(passwd) > 3:  # More reasonable validation
            try:
                hashed_password = generate_password_hash(passwd)  # Hash password
                query = "INSERT INTO user_login(username, email, password) VALUES(?,?,?)"
                cur = support.execute_query('insert', query, (name, email, hashed_password))
                session['user_id'] = cur[0][0]  # set session on successful registration
                flash("Successfully Registered!!")
                return redirect('/home')
            except Exception as e:
                app.logger.error(f"Registration error: {str(e)}")
                flash("Server error during registration")
                return redirect('/register')
        else:  # if input condition length not satisfy
            flash("Not enough data to register, try again!!")
            return redirect('/register')
    else:  # if already logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')

@app.route('/add_customer', methods=['POST'])
def add_customer():
    if 'user_id' in session:
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        dob = request.form.get('dob')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        query = '''INSERT INTO Customers 
                   (FirstName, LastName, DateOfBirth, Email, Phone, Address)
                   VALUES (?, ?, ?, ?, ?, ?)'''
        try:
            support.execute_query('insert', query, 
                                 (first_name, last_name, dob, email, phone, address))
            flash("Customer added successfully!")
        except sqlite3.IntegrityError:
            flash("Email already exists!")
        return redirect('/customers')

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    sub = request.form.get("sub")
    message = request.form.get("message")
    flash("Thanks for reaching out to us. We will contact you soon.")
    return redirect('/')

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get recent transactions
    query = """
        SELECT pdate, expense, pdescription, amount 
        FROM user_expenses 
        WHERE user_id = ? 
        ORDER BY pdate DESC LIMIT 5
    """
    transactions = support.execute_query('search', query, (user_id,))
    
    # Format transactions for display
    recent_transactions = []
    if transactions:
        for t in transactions:
            recent_transactions.append({
                'date': t[0],
                'expense': t[1],
                'description': t[2],
                'amount': t[3]
            })
    
    return render_template('home.html',
                         user_name=session.get('user_name'),
                         recent_transactions=recent_transactions)

@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:
        user_id = session['user_id']
        date = request.form.get('e_date')
        expense = request.form.get('e_type')
        amount = request.form.get('amount')
        notes = request.form.get('notes')
        
        try:
            query = "INSERT INTO user_expenses (user_id, pdate, expense, amount, pdescription) VALUES (?, ?, ?, ?, ?)"
            support.execute_query('insert', query, (user_id, date, expense, amount, notes))
            flash("Record added successfully!")
        except Exception as e:
            print(f"Error adding record: {e}")
            flash("Error adding record!")
            
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/analysis')
def analysis():
    if 'user_id' in session:  # if already logged-in
        query = "SELECT * FROM user_login WHERE user_id = ?"
        userdata = support.execute_query('search', query, (session['user_id'],))
        query2 = "SELECT pdate,expense, pdescription, amount FROM user_expenses WHERE user_id = ?"

        data = support.execute_query('search', query2, (session['user_id'],))
        df = pd.DataFrame(data, columns=['Date', 'Expense', 'Note', 'Amount(₹)'])
        df = support.generate_df(df)

        if df.shape[0] > 0:
            pie = support.meraPie(df=df, names='Expense', values='Amount(₹)', hole=0.7, hole_text='Expense',
                                  hole_font=20,
                                  height=180, width=180, margin=dict(t=1, b=1, l=1, r=1))
            df2 = df.groupby(['Note', "Expense"]).sum().reset_index()[["Expense", 'Note', 'Amount(₹)']]
            bar = support.meraBarChart(df=df2, x='Note', y='Amount(₹)', color="Expense", height=180, x_label="Category",
                                       show_xtick=False)
            line = support.meraLine(df=df, x='Date', y='Amount(₹)', color='Expense', slider=False, show_legend=False,
                                    height=180)
            scatter = support.meraScatter(df, 'Date', 'Amount(₹)', 'Expense', 'Amount(₹)', slider=False, )
            heat = support.meraHeatmap(df, 'Day_name', 'Month_name', height=200, title="Transaction count Day vs Month")
            month_bar = support.month_bar(df, 280)
            sun = support.meraSunburst(df, 280)

            return render_template('analysis.html',
                                   user_name=userdata[0][1],
                                   pie=pie,
                                   bar=bar,
                                   line=line,
                                   scatter=scatter,
                                   heat=heat,
                                   month_bar=month_bar,
                                   sun=sun
                                   )
        else:
            flash("No data records to analyze.")
            return redirect('/home')

    else:  # if not logged-in
        return redirect('/')

@app.route('/profile')
def profile():
    if 'user_id' in session:  # if logged-in
        query = "SELECT * FROM user_login WHERE user_id = ?"
        userdata = support.execute_query('search', query, (session['user_id'],))
        return render_template('profile.html', user_name=userdata[0][1], email=userdata[0][2])
    else:  # if not logged-in
        return redirect('/')

@app.route("/updateprofile", methods=['POST'])
def update_profile():
    name = request.form.get('name')
    email = request.form.get("email")
    query = "SELECT * FROM user_login WHERE user_id = ?"
    userdata = support.execute_query('search', query, (session['user_id'],))
    query = "SELECT * FROM user_login WHERE email = ?"
    email_list = support.execute_query('search', query, (email,))
    if name != userdata[0][1] and email != userdata[0][2] and len(email_list) == 0:
        query = "UPDATE user_login SET username = ?, email = ? WHERE user_id = ?"
        support.execute_query('insert', query, (name, email, session['user_id']))
        flash("Name and Email updated!!")
        return redirect('/profile')
    elif name != userdata[0][1] and email != userdata[0][2] and len(email_list) > 0:
        flash("Email already exists, try another!!")
        return redirect('/profile')
    elif name == userdata[0][1] and email != userdata[0][2] and len(email_list) == 0:
        query = "UPDATE user_login SET email = ? WHERE user_id = ?"
        support.execute_query('insert', query, (email, session['user_id']))
        flash("Email updated!!")
        return redirect('/profile')
    elif name == userdata[0][1] and email != userdata[0][2] and len(email_list) > 0:
        flash("Email already exists, try another!!")
        return redirect('/profile')

    elif name != userdata[0][1] and email == userdata[0][2]:
        query = "UPDATE user_login SET username = ? WHERE user_id = ?"
        support.execute_query('insert', query, (name, session['user_id']))
        flash("Name updated!!")
        return redirect("/profile")
    else:
        flash("No Change!!")
        return redirect("/profile")

@app.route('/logout')
def logout():
    try:
        session.pop("user_id")  # delete the user_id in session (deleting session)
        return redirect('/')
    except:  # if already logged-out but in another tab still logged-in
        return redirect('/')

@app.route('/ask-copilot', methods=['POST'])
def money_copilot():
    user_question = request.json.get('question')
    user_id = session['user_id']
    
    # Get full financial history
    financial_data = support.get_financial_health(user_id)
    
    # Get AI response
    answer = support.ask_money_copilot(user_question, financial_data.to_dict())
    
    return jsonify({"answer": answer})

# Add custom error handler
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

def main():
    # Core application logic
    print("Running main program")

def load_config():
    """Load application configuration"""
    return {"db_host": "localhost", "db_port": 5432}

def generate_text(prompt):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# Add this API endpoint for chat completions
@app.route('/api/ask', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=data['question'],
            max_tokens=150
        )
        return jsonify({
            "answer": response.choices[0].text.strip()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_db_connection():
    conn = sqlite3.connect('expense.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('/mnt/c/Users/PEX/Desktop/fintech-main/expense.db')
    cur = conn.cursor()
    # Create tables if they don't exist
    cur.execute('''CREATE TABLE IF NOT EXISTS user_login (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(30) NOT NULL UNIQUE,
        email VARCHAR(30) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    )''')
    # Add other table creation statements as needed
    conn.commit()
    conn.close()

# Call init_db before app.run
init_db()

if __name__ == '__main__':
    init_database()  # Initialize the database
    app.run(debug=True)
