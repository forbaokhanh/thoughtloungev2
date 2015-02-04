from flask import Flask

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api
from lib.flask_marshmallow_local import Marshmallow
from flask.ext.mail import Mail

app = Flask(__name__)

app.config.from_object('thought_lounge.config')
# private_config.py is a file that sets MAIL_PASSWORD and SECRET_KEY
app.config.from_object('thought_lounge.private_config')

db = SQLAlchemy(app)
api = Api(app)
ma = Marshmallow(app)
mail = Mail(app)

import thought_lounge.models
import thought_lounge.views
import thought_lounge.mail
