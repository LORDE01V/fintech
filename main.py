from flask import Flask, render_template, request, redirect, session, flash, jsonify
import os
from datetime import timedelta  # used for setting session timeout
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import support
from dotenv import load_dotenv  # Add this
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS  # Add this import

warnings.filterwarnings("ignore")

load_dotenv()  # Add this to load .env file

app = Flask(__name__)
CORS(app)  # Add this line after creating Flask app
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # Use proper secret key
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

NEW_AI_FEATURE = os.getenv("ENABLE_NEW_AI_FEATURE", "false").lower() == "true"

@app.route('/')
def login():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    if 'user_id' in session:  # if logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("login.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    if 'user_id' not in session:
        email = request.form.get('email')
        passwd = request.form.get('password')
        query = "SELECT * FROM user_login WHERE email = ?"
        users = support.execute_query("search", query, (email,))
        if users and check_password_hash(users[0][3], passwd):  # Verify hash properly
            session['user_id'] = users[0][0]
            return redirect('/home')
        else:
            flash("Invalid email or password!")
            return redirect('/')
    else:  # if user already logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')


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


@app.route('/register')
def register():
    if 'user_id' in session:  # if user is logged-in
        flash("Already a user is logged-in!")
        return redirect('/home')
    else:  # if not logged-in
        return render_template("register.html")


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
                support.execute_query('insert', query, (name, email, hashed_password))  # Store hash

                query = "SELECT * FROM user_login WHERE email = ?"
                user = support.execute_query('search', query, (email,))
                session['user_id'] = user[0][0]  # set session on successful registration
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
    if 'user_id' in session:  # if user is logged-in
        query = "SELECT * FROM user_login WHERE user_id = ?"
        userdata = support.execute_query("search", query, (session['user_id'],))

        table_query = "SELECT * FROM user_expenses WHERE user_id = ? ORDER BY pdate DESC"
        table_data = support.execute_query("search", table_query, (session['user_id'],))
        df = pd.DataFrame(table_data, columns=['#', 'User_Id', 'Date', 'Expense', 'Amount', 'Note'])

        df = support.generate_df(df)
        try:
            earning, spend, invest, saving = support.top_tiles(df)
        except:
            earning, spend, invest, saving = 0, 0, 0, 0

        try:
            bar, pie, line, stack_bar = support.generate_Graph(df)
        except:
            bar, pie, line, stack_bar = None, None, None, None
        try:
            monthly_data = support.get_monthly_data(df, res=None)
        except:
            monthly_data = []
        try:
            card_data = support.sort_summary(df)
        except:
            card_data = []

        try:
            goals = support.expense_goal(df)
        except:
            goals = []
        try:
            size = 240
            pie1 = support.makePieChart(df, 'Earning', 'Month_name', size=size)
            pie2 = support.makePieChart(df, 'Spend', 'Day_name', size=size)
            pie3 = support.makePieChart(df, 'Investment', 'Year', size=size)
            pie4 = support.makePieChart(df, 'Saving', 'Note', size=size)
            pie5 = support.makePieChart(df, 'Saving', 'Day_name', size=size)
            pie6 = support.makePieChart(df, 'Investment', 'Note', size=size)
        except:
            pie1, pie2, pie3, pie4, pie5, pie6 = None, None, None, None, None, None
        return render_template('home.html',
                               user_name=userdata[0][1],
                               df_size=df.shape[0],
                               df=jsonify(df.to_json()),
                               earning=earning,
                               spend=spend,
                               invest=invest,
                               saving=saving,
                               monthly_data=monthly_data,
                               card_data=card_data,
                               goals=goals,
                               table_data=table_data[:4],
                               bar=bar,
                               line=line,
                               stack_bar=stack_bar,
                               pie1=pie1,
                               pie2=pie2,
                               pie3=pie3,
                               pie4=pie4,
                               pie5=pie5,
                               pie6=pie6,
                               )
    else:  # if not logged-in
        return redirect('/')


@app.route('/home/add_expense', methods=['POST'])
def add_expense():
    try:
        amount = float(request.form.get('amount'))
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Invalid amount entered")
        return redirect('/home')

    if 'user_id' in session:
        user_id = session['user_id']
        if request.method == 'POST':
            date = request.form.get('e_date')
            expense = request.form.get('e_type')
            amount = request.form.get('amount')
            notes = request.form.get('notes')
            try:
                query = "INSERT INTO user_expenses (user_id, pdate, expense, amount, pdescription) VALUES (?, ?, ?, ?, ?)"
                support.execute_query('insert', query, (user_id, date, expense, amount, notes))
                flash("Saved!!")
            except:
                flash("Something went wrong.")
                return redirect("/home")
            return redirect('/home')
    else:
        return redirect('/')


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
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].text.strip()  # Fix attribute access

# Add this API endpoint for chat completions
@app.route('/api/ask', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": data['question']}]
        )
        return jsonify({
            "answer": response.choices[0].message.content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/new-ai-endpoint')
def new_ai_feature():
    if not NEW_AI_FEATURE:
        return jsonify({"status": "feature disabled"}), 501
    # New OpenAI integration code here
    return jsonify({"result": "new feature response"})

if os.getenv('ENABLE_SUBSCRIPTION_PREDICTOR', 'false').lower() == 'true':
    @app.route('/predict-subscriptions', methods=['GET'])
    def predict_subscriptions():
        if 'user_id' not in session:  # Add authorization check
            return jsonify({"error": "Unauthorized"}), 401
        
        user_id = session['user_id']  # Get from session
        transactions = support.get_recurring_payments(user_id)  # Pass user_id to query
        
        forecast = support.time_series_forecast(dates, amounts)
        visualization = support.generate_forecast_chart(forecast)
        
        return jsonify({
            "prediction": forecast.tolist(),
            "chart": visualization
        })

@app.route('/financial-personality', methods=['GET'])
def financial_personality():
    user_id = session['user_id']
    transactions = support.get_transaction_history(user_id)
    analysis = support.analyze_spending_patterns(transactions)
    
    prompt = f"""
    Analyze this financial behavior: {analysis}
    Generate a personality type (e.g., 'Cautious Conservator', 'Bold Investor') 
    with 3 actionable insights and 1 emoji representation.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return jsonify({"persona": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Update run configuration
