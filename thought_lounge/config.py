import os
APP_SUBROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.abspath(os.path.join(APP_SUBROOT, os.pardir))

ADMIN_EMAILS = ['raj.ksvn@gmail.com', 'tranthibaokhanh@berkeley.edu', 'vadrevu@twitter.com']

PICTURES_FOLDER = APP_ROOT + '/thought_lounge/static/pictures/'
DATABASE_FOLDER = APP_ROOT + '/database/'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_FOLDER + 'thought_lounge.db'

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

PROPAGATE_EXCEPTIONS = True

MAIL_USERNAME = 'thoughtloungeucb@gmail.com'
MAIL_DEFAULT_SENDER = '"Thought Lounge" <thoughtloungeucb@gmail.com>'
MAIL_PASSWORD = 'thoughtloungeorg6'
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False
