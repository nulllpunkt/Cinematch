from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

user_likes = db.Table('user_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_imdb_id', db.String(20), db.ForeignKey('movies.imdb_id'), primary_key=True),
    db.Column('liked_at', db.DateTime(timezone=True), server_default=func.now())
)

user_dislikes = db.Table('user_dislikes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('movie_imdb_id', db.String(20), db.ForeignKey('movies.imdb_id'), primary_key=True),
    db.Column('disliked_at', db.DateTime(timezone=True), server_default=func.now())
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    likes = db.relationship('Movie', secondary=user_likes, back_populates='liked_by')
    dislikes = db.relationship('Movie', secondary=user_dislikes, back_populates='disliked_by')

    def __repr__(self):
        return f'<User {self.username}>'

class Movie(db.Model):
    __tablename__ = 'movies'
    imdb_id = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer)
    poster_url = db.Column(db.Text)
    genre = db.Column(db.String(255))
    plot = db.Column(db.Text)
    imdb_rating = db.Column(db.String(10))
    last_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    liked_by = db.relationship('User', secondary=user_likes, back_populates='likes')
    disliked_by = db.relationship('User', secondary=user_dislikes, back_populates='dislikes')

    def __repr__(self):
        return f'<Movie {self.title}>'


