@app.route('/analysis')
def analysis():
    # ... existing logic ...
    
    # Ensure all code paths return a response
    return render_template('analysis.html')  # Make sure this exists
        # pass required template variables here
    ) 

def change_password():
    # ... existing checks ...
    if len(new_password) < 8:
        flash('Password must be at least 8 characters')
        return redirect(url_for('profile'))
    if not any(char.isdigit() for char in new_password):
        flash('Password must contain at least one number')
        return redirect(url_for('profile')) 

def upload_photo():
    # ... existing checks ...
    if file and allowed_file(file.filename):
        # Delete old profile picture if not default
        if current_user.profile_picture != 'default.jpg':
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture))
            except:
                pass
        
        # Generate unique filename
        ext = filename.rsplit('.', 1)[1].lower()
        filename = f"user_{current_user.id}_{int(time.time())}.{ext}"
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.profile_picture = filename
        db.session.commit() 

def delete_account():
    # Delete profile picture
    if current_user.profile_picture != 'default.jpg':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture))
        except:
            pass
    
    # Delete user from database
    db.session.delete(current_user)
    db.session.commit()
    logout_user() 