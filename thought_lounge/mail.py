from flask import render_template
from flask.ext.mail import Message

from thought_lounge import app, mail
from thought_lounge.views import *
from thought_lounge.models import *

from sqlalchemy import and_
import datetime, subprocess

def send_welcome_mail(user):
    message = Message("Welcome to Thought Lounge!", recipients = [user.email])
    message.body = render_template('welcome.mail', user = user)
    if not app.config['TESTING']:
        mail.send(message)

def reminder():
    now = datetime.datetime.now()
    lounges = Lounge.query.filter(Lounge.date_time > now).all()

    for lounge in lounges:
        interval = lounge.date_time - now
        if interval < datetime.timedelta(days = 4):
            message = Message("Reminder to remind your loungers: lounge on {0}".format(lounge.formatted_local_date_time), recipients = [lounge.host.email])
            message.body = render_template('remind_host.mail', lounge = lounge)
            mail.send(message)

def digest(notifications):
    now = datetime.datetime.utcnow()
    week_ahead = now + datetime.timedelta(weeks = 1)
    lounges = Lounge.query.filter(and_(Lounge.date_time > now, Lounge.date_time < week_ahead)).all()

    # Only send mail if there are lounges in the next week
    if lounges:
        users = User.query.filter_by(notifications = notifications)
        with mail.connect() as connection:
            for user in users:
                message = Message("Thought Lounge Digest: lounges for the next week", recipients = [user.email])
                message.body = render_template('digest.mail', user = user, lounges = lounges)
                connection.send(message)

def send_error_mail():
    message = Message("Thought Lounge: Internal Server Error 500", recipients = app.config['ADMIN_EMAILS'])

    try:
        error_log = subprocess.call(['./.err.sh'])
        message.body = render_template('error.mail', error_log = error_log)
    except FileNotFoundError:
        message.body = render_template('error.mail', error_log = 'No error log available.')

    mail.send(message)
