from email.policy import default
from enum import unique
from operator import index
import re

from sqlalchemy.orm import defaultload
from main import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin,current_user
from sqlalchemy import and_, or_





#掲示板DB
class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now())
    name = db.Column(db.Text)
    article = db.Column(db.Text)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    send_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return '<Entry id={id} date={date} name={name!r} article={article} thread_id={thread_id}>'.format(id=self.id,
                 date=self.date, title=self.title, text=self.text, thread_id=self.thread_id)


#スレッドDB
class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    threadname = db.Column(db.String(80), unique=True)
    articles = db.relationship('Entry', backref='thread', lazy=True)

    def __init__(self, threadname, articles=[]):
        self.threadname = threadname
        self.articles = articles
    
    def __repr__(self):
        return '<Thread id={id} threadname={threadname} articles={articles}>'.format(id=self.id, threadname=self.threadname, articles=self.articles)


#ユーザー管理DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    login_user_id = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    picture_path = db.Column(db.Text, nullable=True)


#フォロー・フォロワー管理
class UserRelationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.Integer, default=0)

    def __init__(self, from_user_id, to_user_id, state=0):
        self.from_user_id  = from_user_id 
        self.to_user_id  = to_user_id 
        self.state = state

#ダイレクトメッセージDB
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    create_date = db.Column(db.DateTime, default=datetime.now)
    
    def __init__(self, from_user_id, to_user_id, message):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.message = message

      

def init():
    db.create_all()