from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(100), default='default.jpg')
    about_me = db.Column(db.Text)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<User {self.username}>' 