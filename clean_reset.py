from thought_lounge import app, db
from thought_lounge.models import *
import getpass

print('Clean resetting database...starting...')

db.drop_all()
db.create_all()

first_name = input('First name')
last_name = input('Last name')
email = input('Email')
password = getpass.getpass()

admin = User(email = email, first_name = first_name, last_name = last_name, password = password)

db.session.add(admin)
admin.role = 'admin'
db.session.commit()

print('Clean resetting database...completed.')
