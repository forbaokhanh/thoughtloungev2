from thought_lounge import db

import uuid, datetime
from datetime import timezone
from passlib.apps import custom_app_context as pwd_context

class Key(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    key = db.Column(db.String, unique = True, nullable = False)

    def __init__(self):
        self.key = str(uuid.uuid4())

    def __repr__(self):
        return '<Key {0}>'.format(self.key)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String, nullable = False, unique = True)
    password = db.Column(db.String, nullable = False, server_default = '')

    first_name = db.Column(db.String)
    last_name = db.Column(db.String)

    bio = db.Column(db.String)

    # 'host' or 'lounger' or 'admin'
    role = db.Column(db.String)

    # in number of weeks
    # 0 = never, 1 = every week, 2 = every two weeks, etc.
    notifications = db.Column(db.Integer, nullable = False)

    picture_id = db.Column(db.Integer, db.ForeignKey('picture.id'))
    picture = db.relationship('Picture')

    user_lounges = db.relationship('UserLounge', backref = 'user')

    #verification_code = db.Column(db.Integer, unique = True, server_default = None)

    host_applications = db.relationship('HostApplication', backref = 'user', lazy = 'dynamic', cascade = 'all, delete-orphan')

    key_id = db.Column(db.Integer, db.ForeignKey('key.id'))
    key = db.relationship('Key', backref = db.backref('user', uselist = False))

    def hash_password(self, plaintext_password):
        self.password = pwd_context.encrypt(plaintext_password)

    def verify_password(self, plaintext_password):
        return pwd_context.verify(plaintext_password, self.password)

    def __init__(self, email, password, first_name = None, last_name = None, bio = None, role = 'lounger', notifications = 2):
        self.email = email
        self.hash_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.role = role
        self.notifications = notifications
        self.key = Key()

    def __repr__(self):
        return '<User {0}: {1} {2}>'.format(self.email, self.first_name, self.last_name)

class UserLounge(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    lounge_id = db.Column(db.Integer, db.ForeignKey('lounge.id'), primary_key = True)

    lounge = db.relationship('Lounge', backref = 'user_lounges')

    is_host = db.Column(db.Boolean)
    topic = db.Column(db.String)
    summary = db.Column(db.String)

    showed_up = db.Column(db.Boolean)

    def __init__(self, is_host, topic = None, summary = None, showed_up = None):
        self.is_host = is_host
        self.summary = summary
        self.topic = topic
        self.showed_up = showed_up

    def __repr__(self):
        return '<UserLounge {0}: hosting {1}>'.format(self.topic, self.is_host)

class Lounge(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    date_time = db.Column(db.DateTime, nullable = False)

    location = db.Column(db.String)
    campus = db.Column(db.String) #CHANGE
    community = db.Column(db.String)
    is_reserved = db.Column(db.Boolean, nullable = False)

    topic = db.Column(db.String)
    summary = db.Column(db.String)

    pictures = db.relationship('Picture', backref = 'lounge', lazy = 'dynamic', cascade = 'all, delete-orphan')

    @property
    def host(self):
        try:
            return [lounge_user.user for lounge_user in self.user_lounges if lounge_user.is_host][0]
        except IndexError:
            return None

    @property
    def local_date_time(self):
        return self.date_time.replace(tzinfo = timezone.utc).astimezone(tz = None)

    @property
    def formatted_local_date_time(self):
        return self.local_date_time.strftime('%A, %d %B at %I:%M %p')

    def __init__(self, date_time, is_reserved, location = None, community = None, topic = None, summary = None):
        self.date_time = date_time
        self.location = location
        self.community = community
        self.is_reserved = is_reserved
        self.topic = topic
        self.summary = summary

    def __repr__(self):
        return '<Lounge {0}>'.format(self.date_time)

class Picture(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    extension = db.Column(db.String)
    description = db.Column(db.String)

    lounge_id = db.Column(db.Integer, db.ForeignKey('lounge.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

    def __init__(self, extension, description = None):
        self.extension = extension
        self.description = description

    def __repr__(self):
        return '<Picture {0}.{1}>'.format(self.id, self.extension)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    title = db.Column(db.String, nullable = False)
    description = db.Column(db.String)

    date_time = db.Column(db.DateTime)

    # Google Maps-able
    location = db.Column(db.String)

    pictures = db.relationship('Picture', backref = 'event', lazy = 'dynamic', cascade = 'all, delete-orphan')

    # Markdown
    article = db.Column(db.String)

    def __init__(self, title, description = None, date_time = None, location = None, article = None):
        self.title = title
        self.description = description
        self.date_time = date_time
        self.location = location
        self.article = article

    def __repr__(self):
        return '<Event {0}: {1}>'.format(self.title, self.date_time)

class HostApplication(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    application = db.Column(db.String, nullable = False)

    is_approved = db.Column(db.Boolean)

    def __init__(self, application, is_approved = None):
        self.application = application
        self.is_approved = is_approved

    def __repr__(self):
        return '<HostApplication {0}>'.format(self.is_approved)
