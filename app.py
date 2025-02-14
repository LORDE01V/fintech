from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# ... login manager and other routes ...

@app.route('/')
def home():
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',
                          name=current_user.username,
                          email=current_user.email,
                          profile_pic=current_user.profile_picture,
                          about_me=current_user.about_me,
                          phone=current_user.phone,
                          address=current_user.address)

@app.route('/uploadphoto', methods=['POST'])
@login_required
def upload_photo():
    if 'profile_pic' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Delete old profile picture if not default
        if current_user.profile_picture != 'default.jpg':
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture))
            except:
                pass
        
        current_user.profile_picture = filename
        db.session.commit()
        flash('Profile picture updated', 'success')
    
    return redirect(url_for('profile'))

@app.route('/changepassword', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_pw):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('profile'))
    
    if new_pw != confirm_pw:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('profile'))
    
    current_user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/updatebio', methods=['POST'])
@login_required
def update_bio():
    current_user.about_me = request.form.get('about_me')
    db.session.commit()
    flash('Bio updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/updatecontact', methods=['POST'])
@login_required
def update_contact():
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    db.session.commit()
    flash('Contact information updated', 'success')
    return redirect(url_for('profile'))

@app.route('/deleteaccount', methods=['POST'])
@login_required
def delete_account():
    # Delete profile picture if not default
    if current_user.profile_picture != 'default.jpg':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture))
        except:
            pass
    
    db.session.delete(current_user)
    db.session.commit()
    flash('Account deleted successfully', 'success')
    return redirect(url_for('home'))

@app.route('/analysis')
def analysis():
    # ... existing logic ...
    
    # Ensure all code paths return a response
    return render_template('analysis.html')  # Make sure this exists
        # pass required template variables here
    ) 

@app.route('/cards')
@login_required
def cards():
    return render_template('cards.html')

@app.route('/transfers')
@login_required
def transfers():
    return render_template('transfers.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')  # Corrected variable name
        confirm_password = request.form.get('confirm_password')
        
        # Add validation checks
        if not all([email, new_password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('reset'))
            
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('reset'))
            
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found', 'danger')
            return redirect(url_for('reset'))
            
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successfully', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error resetting password', 'danger')
            return redirect(url_for('reset'))
    
    return render_template('reset.html')

db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 