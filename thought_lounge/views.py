from thought_lounge import app, api, ma, db
from thought_lounge.models import *
from thought_lounge.mail import *

from flask import render_template, request, g, session, url_for, send_file, redirect
from flask import abort as flask_abort
import werkzeug

from sqlalchemy import asc, desc, or_, func
from flask.ext.restful import Resource, abort
from marshmallow import ValidationError

from io import StringIO
import os, re, nose, sys, datetime, random

@app.before_request
def preload_user():
    g.user = None

    if 'user_id' in session and session['user_id'] is not None:
        g.user = User.query.get(session['user_id'])

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user/')
def user():
    if not g.user:
        flask_abort(401)
    elif g.user.role == 'lounger':
        return render_template('user.html')
    elif g.user.role == 'host':
        return render_template('host.html')
    elif g.user.role == 'admin':
        return render_template('admin.html')

@app.route('/user_new/')
def user_new():
    if not g.user:
        flask_abort(401)
    elif g.user.role == 'lounger':
        return render_template('user_new.html')
    elif g.user.role == 'host':
        return render_template('host_new.html')
    elif g.user.role == 'admin':
        return render_template('admin_new.html')

@app.route('/admin_new/')
def admin_new():
    return render_template('admin_new.html')

@app.route('/user/<int:host_id>/')
def host_preview(host_id):
    host = User.query.get_or_404(host_id)
    if not host or host.role not in ['host', 'admin']:
        flask_abort(403)
    # If a host accesses their own hostpage
    if g.user and g.user.id == host_id:
        return redirect(url_for('user'))
    return render_template('host_preview.html', hostHref = url_for('user_ep', user_id = host.id))

@app.route('/manifesto/')
def manifesto():
    return render_template('manifesto.html')

@app.route('/log/')
@app.route('/log/<int:lounge_id>')
def log(lounge_id = None):
    if lounge_id is None:
        return render_template('log.html', lounge_href = "")
    else:
        lounge_href = url_for('lounge_ep', lounge_id = lounge_id)
        return render_template('log.html', lounge_href = lounge_href)

@app.route('/contact/')
def contact():
    return render_template('contact.html')

@app.route('/accounts/')
def accounts():
    return render_template('accounts.html')

@app.errorhandler(401)
def not_authenticated(e):
    return render_template('401.html'), 401

@app.errorhandler(403)
def not_authorized(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# @app.errorhandler(500)
# def internal_server_error(e):
#     # Doesn't work.
#     send_error_mail()
#     return render_template('500.html'), 500

###########################
####### RESTful API #######
###########################

@app.route('/api/')
def developers():
    return 'Thought Lounge API: <a href="https://github.com/raj-kesavan/thought-lounge" target="_blank">Docs</a>'

#### Helper Functions ####

# Returns the first instance of a model with provided attributes; if none exists then 404
def get_or_404(model, **kwargs):
    rv = model.query.filter_by(**kwargs).first()
    if rv is None:
        abort(404, message = '{0} with attributes {1} not found.'.format(model.__tablename__, kwargs), code = 404)
    return rv

# Returns None given there exists no model with provided attributes; if at least one exists then 409
def none_or_409(model, error_code, **kwargs):
    rv = model.query.filter_by(**kwargs).first()
    if rv is not None:
        abort(409, message = '{0} with attributes {1} already exists.'.format(model.__tablename__, kwargs), code = 409, error_code = error_code)
    return None

def invalid_authentication():
    abort(401, message = 'Either no API key provided or API key provided is invalid: unable to authenticate. Add the Authorization-API-Key header.', code = 401)

def invalid_authorization():
    abort(403, message = 'The API key provided does not have sufficient privileges. Authorization not granted.', code = 403)

class AuthenticationSchema(ma.Schema):
    key = ma.String(attribute = 'Authorization-API-Key', required = True)

# Returns provided key->user; 401 if key not provided or key not valid
def authenticate():
    data, errors = AuthenticationSchema().dump(request.headers)
    if errors or not data['key']:
        invalid_authentication()

    key = Key.query.filter_by(key = data['key']).first()
    if key is None:
        invalid_authentication()

    return key.user

ROLES = {
    'lounger': 1,
    'host': 2,
    'admin': 3
}

# Returns user_id->user if provided key->user is that user or provided key->user is admin.
def authorize(user_id):
    user = authenticate()

    if user.id == user_id or user.role == 'admin':
        return get_or_404(User, id = user_id)

    invalid_authorization()

# 403 if provided key->user does not have specified privileges
def authorize_role(role, soft = False):
    user = authenticate()
    return authorize_role_by_id(role, user.id, soft = soft)

# 403 if user_id->user does not have specified privileges
def authorize_role_by_id(role, user_id, soft = False):
    user = get_or_404(User, id = user_id)
    if not ROLES[user.role] >= ROLES[role]:
        if soft:
            return False
        else:
            invalid_authorization()
    return user

# 403 if provided key->user is not the lounge's host or an admin
def authorize_lounge(lounge):
    user = authenticate()
    if user is not lounge.host:
        authorize_role('admin')
    return user

# Loads a schema with given payload; returns dictionary. 400 if there is an error.
def load_payload(schema,  payload):
    data, errors = schema().load(payload)
    if errors:
        abort(400, message = str(errors))
    return data

# Converts a camelCase variable to snake_case. Used for updating a model during PUT requests.
# Source: http://stackoverflow.com/a/1176023/3024025
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def camel_to_snake(string):
    s1 = first_cap_re.sub(r'\1_\2', string)
    return all_cap_re.sub(r'\1_\2', s1).lower()

# Converts a lisp-case variable to snake_case. Used for get query parameters.
def lisp_to_snake(string):
    return string.replace('-', '_')

# Maps a given href to an endpoint, returning the variables of that endpoint.
# Example:
# >>> url_map('user_ep', '/api/users/1/')
# {'user_id': 1}
# If the given href does not map to an endpoint, throws a 400.
def url_map(endpoint, href):
    try:
        map = app.url_map.bind(endpoint).match(href)
        return map[1]
    except werkzeug.exceptions.NotFound:
        rule = app.url_map._rules_by_endpoint[endpoint][0].rule
        abort(400, message = "Malformed href input: endpoint rule '{0}' not matched to href '{1}'.".format(rule, href))
    except werkzeug.routing.RequestRedirect:
        rule = app.url_map._rules_by_endpoint[endpoint][0].rule
        abort(400, message = "Malformed href input: endpoint rule '{0}' not matched to href '{1}'. You may have omitted a trailing slash ('/').".format(rule, href))

# Returns a schema with all optional attributes filled with empty values.
# Example: if a 'bio' optional attribute is not provided in a dictionary for a user, the bio key is created with an empty string.
# For use with HTTP PUT; ensures idempotence.
def schema_cycle(schema, payload):
    data, errors = schema().load(payload)
    if errors:
        abort(400, message = str(errors))
    data = schema().dump(data).data
    return schema().load(data).data

def put(model, data):
    for attribute, value in data.items():
        attribute = camel_to_snake(attribute)
        if hasattr(model, attribute):
            try:
                setattr(model, attribute, value)
            except AttributeError:
                pass

#### Schemas and APIs ####

def validate_role(role):
    if role not in ['lounger', 'host', 'admin']:
        raise ValidationError('role attribute must be either \'lounger\', \'host\', or \'admin\'.')

class UserPictureSchema(ma.Schema):
    href = ma.URLFor('picture_ep', picture_id = '<id>')

class UserSchema(ma.Schema):
    email = ma.Email(required = True)
    firstName = ma.String(attribute = 'first_name', required = True)
    lastName = ma.String(attribute = 'last_name')
    bio = ma.String()
    notifications = ma.Integer(required = True)
    picture = ma.Nested(UserPictureSchema, default = dict())

class PasswordedUserSchema(UserSchema):
    password = ma.String(required = True)

class RoledUserSchema(UserSchema):
    role = ma.String(validate = validate_role)

class LinkedUserSchema(RoledUserSchema):
    href = ma.URLFor('user_ep', user_id = '<id>')
    key = ma.Hyperlinks({
        'href': ma.URLFor('key_ep', user_id = '<id>')
    })
    userLounges = ma.Hyperlinks({
        'href': ma.URLFor('user_lounges_ep', user_id = '<id>')
    })
    hostApplications = ma.Hyperlinks({
        'href': ma.URLFor('user_host_applications_ep', user_id = '<id>')
    })
    web = ma.Hyperlinks({
        'href': ma.URLFor('host_preview', host_id = '<id>')
    })

class UserListSchema(ma.Schema):
    items = ma.Nested(LinkedUserSchema, many = True, attribute = 'users')
    href = ma.URLFor('users_ep')

class UserAPI(Resource):
    def get(self, user_id):
        user = get_or_404(User, id = user_id)
        return LinkedUserSchema().dump(user).data

    def put(self, user_id):
        user = authorize(user_id)

        payload = request.get_json()

        schema = UserSchema
        if 'role' in payload and authorize_role('admin', soft = True):
            schema = RoledUserSchema

        picture_data = payload.pop('picture', None)
        user_data = schema_cycle(schema, payload)

        put(user, user_data)

        if picture_data and 'href' in picture_data:
            mapping = url_map('picture_ep', picture_data['href'])
            user.picture = get_or_404(Picture, id = mapping['picture_id'])
        else:
            user.picture = None

        db.session.commit()

        return self.get(user.id)

class UserListAPI(Resource):
    def get(self):
        sort = request.args.get('sort')
        role = request.args.get('role')
        require = request.args.get('require')
        limit = request.args.get('limit')

        if sort == 'random':
            users = User.query.order_by(func.random())
        else:
            users = User.query.order_by(desc(User.first_name))

        if role:
            roles = role.split(',')
            users = users.filter(User.role.in_(roles))

        if require:
            # Return only users that have attributes that are lists with at least one element
            # example, if require = 'host-applications', only return users with at least one host application
            requires = require.split(',')
            requires = [getattr(User, lisp_to_snake(require)).any() for require in requires]
            users = User.query.filter(*requires)

        if limit:
            limit = int(limit)
            users = users[:limit]
        else:
            users = users.all()

        users = {'users': users}
        return UserListSchema().dump(users).data

    def post(self):
        user_data = load_payload(PasswordedUserSchema, request.get_json())
        picture_data = user_data.pop('picture', None)
        user = User(**user_data)

        none_or_409(User, 'DUPLICATE_EMAIL', email = user.email)

        if picture_data is not None and 'href' in picture_data:
            mapping = url_map('picture_ep', picture_data['href'])
            user.picture = get_or_404(Picture, id = mapping['picture_id'])
        else:
            user.picture = None

        db.session.add(user)
        db.session.commit()

        # send_welcome_mail(user)

        # Signing user in
        session['user_id'] = user.id

        return LinkedUserSchema().dump(user).data, 201

api.add_resource(UserAPI, '/api/users/<int:user_id>/', endpoint = 'user_ep')
api.add_resource(UserListAPI, '/api/users/', endpoint = 'users_ep')

class UserSignInSchema(ma.Schema):
    email = ma.String(required = True)
    password = ma.String(required = True)

class UserSignInAPI(Resource):
    def get(self):
        if g.user:
            return LinkedUserSchema().dump(g.user).data
        else:
            return {}, 204

    def post(self):
        sign_in_data = load_payload(UserSignInSchema, request.get_json())

        user = get_or_404(User, email = sign_in_data['email'])
        if not user.verify_password(sign_in_data['password']):
            abort(403, message = 'Incorrect password.')

        # Signing user in
        session['user_id'] = user.id

        return LinkedUserSchema().dump(user).data

class UserSignOutAPI(Resource):
    def post(self):
        session.clear()
        return {}, 204

api.add_resource(UserSignInAPI, '/api/auth/sign_in/', endpoint = 'user_sign_in_ep')
api.add_resource(UserSignOutAPI, '/api/auth/sign_out/', endpoint = 'user_sign_out_ep')

class KeySchema(ma.Schema):
    key = ma.String(required = True)
    href = ma.URLFor('key_ep', user_id = '<user.id>')

class KeyAPI(Resource):
    def get(self, user_id):
        # Keys can be accessed through sign in instead of via API key
        if g.user and g.user.id == user_id:
            user = g.user
        else:
            user = authorize(user_id)

        key = user.key
        return KeySchema().dump(key).data

    def post(self, user_id):
        user = authorize(user_id)

        user.key = Key()
        db.session.commit()

        return KeySchema().dump(user.key), 201

api.add_resource(KeyAPI, '/api/users/<int:user_id>/key/', endpoint = 'key_ep')

class PictureSchema(ma.Schema):
    href = ma.URLFor('picture_ep', picture_id = '<id>')
    image = ma.URLFor('picture_image_ep', picture_id = '<id>')

class PictureListSchema(ma.Schema):
    items = ma.Nested(PictureSchema, many = True, attribute = 'pictures')
    href = ma.URLFor('pictures_ep')

def file_extension(filename):
    return filename.rsplit('.')[1]

def allowed_file(filename):
    return '.' in filename and file_extension(filename) in app.config['ALLOWED_EXTENSIONS']

class PictureAPI(Resource):
    def get(self, picture_id):
        picture = get_or_404(Picture, id = picture_id)
        return PictureSchema().dump(picture).data

class PictureListAPI(Resource):
    def get(self):
        pictures = {'pictures': Picture.query.all()}
        return PictureListSchema().dump(pictures).data

    def post(self):
        file = request.files['file']
        if file:
            if allowed_file(file.filename):
                extension = file_extension(file.filename)

                picture = Picture(extension = extension)
                db.session.add(picture)
                db.session.commit()

                filename = str(picture.id) + '.' + extension
                file.save(os.path.join(app.config['PICTURES_FOLDER'], filename))
            else:
                abort(400, message = 'Picture must be either either {0}.'.format(', '.join(app.config['ALLOWED_EXTENSIONS'])))
        else:
            abort(400, message = 'Picture must exist.')

        return PictureSchema().dump(picture).data, 201

class PictureImageAPI(Resource):
    def get(self, picture_id):
        picture = get_or_404(Picture, id = picture_id)
        directory = app.config['PICTURES_FOLDER']
        return send_file(directory + str(picture.id) + '.' + picture.extension)

api.add_resource(PictureAPI, '/api/pictures/<int:picture_id>/', endpoint = 'picture_ep')
api.add_resource(PictureListAPI, '/api/pictures/', endpoint = 'pictures_ep')
api.add_resource(PictureImageAPI, '/api/pictures/cdn/<int:picture_id>/', endpoint = 'picture_image_ep')

class LoungeSchema(ma.Schema):
    dateTime = ma.DateTime(attribute = 'date_time', required = True)
    location = ma.String()
    campus = ma.String()
    isReserved = ma.Boolean(attribute = 'is_reserved', required = True)
    topic = ma.String()
    summary = ma.String()

class LinkedLoungeSchema(LoungeSchema):
    href = ma.URLFor('lounge_ep', lounge_id = '<id>')
    loungeUsers = ma.Hyperlinks({
        'href': ma.URLFor('lounge_users_ep', lounge_id = '<id>')
    })
    pictures = ma.Hyperlinks({
        'href': ma.URLFor('lounge_pictures_ep', lounge_id = '<id>')
    })
    web = ma.Hyperlinks({
        'href': ma.URLFor('log', lounge_id = '<id>')
    })

class LoungeListSchema(ma.Schema):
    items = ma.Nested(LinkedLoungeSchema, many = True, attribute = 'lounges')
    href = ma.URLFor('lounges_ep')

class LoungeAPI(Resource):
    def get(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        return LinkedLoungeSchema().dump(lounge).data

    def put(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        authorize_lounge(lounge)

        lounge_data = schema_cycle(LoungeSchema, request.get_json())
        put(lounge, lounge_data)

        db.session.commit()

        return self.get(lounge.id)

    def delete(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        user = authorize_lounge(lounge)

        # Does SQLAlchemy support delete cascades on association objects? Not right now (22JAN2015), maybe later.
        for lounge_user in lounge.user_lounges:
            db.session.delete(lounge_user)
        db.session.delete(lounge)
        db.session.commit()

        return {}, 204

class LoungeListAPI(Resource):
    def get(self):
        lounges = Lounge.query.order_by(desc(Lounge.date_time)).all()

        time = request.args.get('time')
        limit = request.args.get('limit')

        if time == 'future':
            now = datetime.datetime.now()
            lounges = [lounge for lounge in lounges if lounge.date_time > now]
        elif time == 'past':
            now = datetime.datetime.now()
            lounges = [lounge for lounge in lounges if lounge.date_time <= now]

        if limit:
            limit = int(limit)
            lounges = lounges[:limit]

        lounges = {'lounges': lounges}
        return LoungeListSchema().dump(lounges).data

    def post(self):
        user = authorize_role('host')

        lounge_data = load_payload(LoungeSchema, request.get_json())
        lounge = Lounge(**lounge_data)

        db.session.add(lounge)

        # The user who creates a lounge is the host
        user_lounge = UserLounge(is_host = True)
        user.user_lounges.append(user_lounge)
        user_lounge.lounge = lounge

        db.session.commit()

        return LinkedLoungeSchema().dump(lounge).data, 201

api.add_resource(LoungeAPI, '/api/lounges/<int:lounge_id>/', endpoint = 'lounge_ep')
api.add_resource(LoungeListAPI, '/api/lounges/', endpoint = 'lounges_ep')

class LoungePictureSchema(ma.Schema):
    picture = ma.Nested(PictureSchema, allow_null = True, default = dict(), required = True)

class LinkedLoungePictureSchema(LoungePictureSchema):
    href = ma.URLFor('lounge_picture_ep', picture_id = '<id>', lounge_id = '<lounge_id>')

class LoungePictureListSchema(ma.Schema):
    items = ma.Nested(LinkedLoungePictureSchema, many = True, attribute = 'lounge_pictures')
    href = ma.URLFor('lounge_pictures_ep', lounge_id = '<lounge_id>')

class LoungePictureAPI(Resource):
    def get(self, lounge_id, picture_id):
        lounge_picture = get_or_404(Picture, id = picture_id, lounge_id = lounge_id)
        data = {
            'lounge_id': lounge_picture.lounge_id,
            'id': lounge_picture.id,
            'picture': lounge_picture
        }
        return LinkedLoungePictureSchema().dump(data).data

    def delete(self, lounge_id, picture_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        authorize_lounge(lounge)

        picture = get_or_404(Picture, id = picture_id)
        lounge.pictures.remove(picture)
        db.session.commit()
        return {}, 204

class LoungePictureListAPI(Resource):
    def get(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        lounge_pictures = {
            'lounge_pictures': [{'lounge_id': lounge_picture.lounge_id, 'id': lounge_picture.id, 'picture': lounge_picture} for lounge_picture in lounge.pictures.all()],
            'lounge_id': lounge.id
        }
        return LoungePictureListSchema().dump(lounge_pictures).data

    def post(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        authorize_lounge(lounge)

        lounge_picture_data = load_payload(LoungePictureSchema, request.get_json())
        picture_data = lounge_picture_data.pop('picture')

        mapping = url_map('picture_ep', picture_data['href'])
        picture = get_or_404(Picture, id = mapping['picture_id'])

        if picture not in lounge.pictures.all():
            lounge.pictures.append(picture)
        else:
            abort(409, message = 'This picture is already part of the lounge\'s pictures.')

        db.session.commit()
        lounge_picture = get_or_404(Picture, id = picture.id, lounge_id = lounge_id)
        data = {
            'lounge_id': lounge_picture.lounge_id,
            'id': lounge_picture.id,
            'picture': lounge_picture
        }
        return LinkedLoungePictureSchema().dump(data).data

api.add_resource(LoungePictureAPI, '/api/lounges/<int:lounge_id>/pictures/<int:picture_id>/', endpoint = 'lounge_picture_ep')
api.add_resource(LoungePictureListAPI, '/api/lounges/<int:lounge_id>/pictures/', endpoint = 'lounge_pictures_ep')

class UserLoungeBaseSchema(ma.Schema):
    topic = ma.String()
    summary = ma.String()
    showedUp = ma.Boolean(attribute = 'showed_up')
    isHost = ma.Boolean(attribute = 'is_host', required = True)

class UserLoungeSchema(UserLoungeBaseSchema):
    lounge = ma.Hyperlinks({
        'href': ma.URLFor('lounge_ep', lounge_id = '<lounge_id>')
    }, required = True)

class LinkedUserLoungeSchema(UserLoungeSchema):
    href = ma.URLFor('user_lounge_ep', user_id = '<user_id>', lounge_id = '<lounge_id>')

class UserLoungeListSchema(ma.Schema):
    items = ma.Nested(LinkedUserLoungeSchema, many = True, attribute = 'user_lounges')
    href = ma.URLFor('user_lounges_ep', user_id = '<user_id>')

class UserLoungeAPI(Resource):
    def get(self, user_id, lounge_id):
        user_lounge = get_or_404(UserLounge, user_id = user_id, lounge_id = lounge_id)
        return LinkedUserLoungeSchema().dump(user_lounge).data

    def put(self, user_id, lounge_id):
        authorize(user_id)
        user_lounge = get_or_404(UserLounge, user_id = user_id, lounge_id = lounge_id)

        payload = request.get_json()
        lounge_data = payload.pop('lounge')
        user_lounge_data = schema_cycle(UserLoungeBaseSchema, payload)

        mapping = url_map('lounge_ep', lounge_data['href'])
        lounge = get_or_404(Lounge, id = mapping['lounge_id'])

        if lounge_id != lounge.id:
            none_or_409(UserLounge, 'ALREADY_REGISTERED', user_id = user_id, lounge_id = lounge.id)
            user_lounge.lounge = lounge

        # Only one user can be a host for a specific lounge
        # If sending a PUT with isHost = true and this user isn't the current host, then de-host the old host.
        if user_lounge_data['is_host'] and not user_lounge.is_host:
            authorize_role_by_id('host', user_id)
            current_host = lounge.host
            current_host_user_lounge = get_or_404(UserLounge, user_id = current_host.id, lounge_id = lounge.id)
            current_host_user_lounge.is_host = False

        put(user_lounge, user_lounge_data)

        db.session.commit()

        return self.get(user_lounge.user_id, user_lounge.lounge_id)

class UserLoungeListAPI(Resource):
    def get(self, user_id):
        user = get_or_404(User, id = user_id)

        time = request.args.get('time')
        type = request.args.get('type')

        user_lounges = user.user_lounges
        user_lounges.sort(key = lambda user_lounge: user_lounge.lounge.date_time, reverse = True)

        if type == 'host':
            user_lounges = [user_lounge for user_lounge in user_lounges if user_lounge.is_host == True]

        if time == 'future':
            now = datetime.datetime.now()
            user_lounges = [user_lounge for user_lounge in user_lounges if user_lounge.lounge.date_time > now]
        elif time == 'past':
            now = datetime.datetime.now()
            user_lounges = [user_lounge for user_lounge in user_lounges if user_lounge.lounge.date_time <= now]

        user_lounges = {
            'user_lounges': user_lounges,
            'user_id': user_id
        }
        return UserLoungeListSchema().dump(user_lounges).data

    def post(self, user_id):
        user = authorize(user_id)

        user_lounge_data = load_payload(UserLoungeSchema, request.get_json())
        lounge_data = user_lounge_data.pop('lounge')

        # No autoflush is required for querying the database (getting the lounge) before the user_lounge is populated with user and lounge (since they're primary keys).
        with db.session.no_autoflush:
            user_lounge = UserLounge(**user_lounge_data)

            mapping = url_map('lounge_ep', lounge_data['href'])
            lounge = get_or_404(Lounge, id = mapping['lounge_id'])

            # Only one user can be a host for a specific lounge
            if user_lounge.is_host:
                authorize_role_by_id('host', user_id)
                current_host = lounge.host
                current_host_user_lounge = get_or_404(UserLounge, user_id = current_host.id, lounge_id = lounge.id)
                current_host_user_lounge.is_host = False

            none_or_409(UserLounge, 'ALREADY_REGISTERED', user_id = user_id, lounge_id = lounge.id)
            user.user_lounges.append(user_lounge)
            user_lounge.lounge = lounge

        db.session.commit()

        return LinkedUserLoungeSchema().dump(user_lounge).data, 201

api.add_resource(UserLoungeAPI, '/api/users/<int:user_id>/lounges/<int:lounge_id>/', endpoint = 'user_lounge_ep')
api.add_resource(UserLoungeListAPI, '/api/users/<int:user_id>/lounges/', endpoint = 'user_lounges_ep')

class LoungeUserSchema(UserLoungeBaseSchema):
    user = ma.Hyperlinks({
        'href': ma.URLFor('user_ep', user_id = '<user_id>')
    }, required = True)

class LinkedLoungeUserSchema(LoungeUserSchema):
    href = ma.URLFor('lounge_user_ep', user_id = '<user_id>', lounge_id = '<lounge_id>')

class LoungeUserListSchema(ma.Schema):
    items = ma.Nested(LinkedLoungeUserSchema, many = True, attribute = 'lounge_users')
    href = ma.URLFor('lounge_users_ep', lounge_id = '<lounge_id>')

class LoungeUserAPI(Resource):
    def get(self, lounge_id, user_id):
        lounge_user = get_or_404(UserLounge, user_id = user_id, lounge_id = lounge_id)

        expand = request.args.get('expand')
        if expand == 'user':
            schema = LinkedLoungeUserSchemaExpanded
        else:
            schema = LinkedLoungeUserSchema

        return schema().dump(lounge_user).data

    def put(self, lounge_id, user_id):
        lounge_user = get_or_404(UserLounge, user_id = user_id, lounge_id = lounge_id)
        authorize_lounge(lounge_user.lounge)

        payload = request.get_json()
        user_data = payload.pop('user')
        lounge_user_data = schema_cycle(UserLoungeBaseSchema, payload)

        mapping = url_map('user_ep', user_data['href'])
        user = get_or_404(User, id = mapping['user_id'])

        if user_id != user.id:
            none_or_409(UserLounge, 'ALREADY_REGISTERED', user_id = user.id, lounge_id = lounge_id)
            # SQLAlchemy automatically purges the lounge_user from the old user when we append it to the new user.
            user.user_lounges.append(lounge_user)

        # Only one user can be a host for a specific lounge
        # If sending a PUT with isHost = true and this user isn't the current host, then de-host the old host.
        if lounge_user_data['is_host'] and not lounge_user.is_host:
            authorize_role_by_id('host', user.id)
            current_host = lounge_user.lounge.host
            current_host_user_lounge = get_or_404(UserLounge, user_id = current_host.id, lounge_id = lounge_id)
            current_host_user_lounge.is_host = False

        put(lounge_user, lounge_user_data)

        db.session.commit()

        return self.get(lounge_user.lounge_id, lounge_user.user_id)

class LoungeUserListAPI(Resource):
    def get(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)

        type = request.args.get('type')
        expand = request.args.get('expand')

        lounge_users = lounge.user_lounges
        lounge_users.sort(key = lambda lounge_user: lounge_user.user.first_name)

        if type == 'host':
            lounge_users = [lounge_user for lounge_user in lounge_users if lounge_user.is_host == True]
        elif type == 'showed-up':
            lounge_users = [lounge_user for lounge_user in lounge_users if lounge_user.showed_up == True]

        if expand == 'user':
            schema = LoungeUserListSchemaExpanded
        else:
            schema = LoungeUserListSchema

        lounge_users = {
            'lounge_users': lounge_users,
            'lounge_id': lounge.id
        }

        return schema().dump(lounge_users).data

    def post(self, lounge_id):
        lounge = get_or_404(Lounge, id = lounge_id)
        authorize_lounge(lounge)

        lounge_user_data = load_payload(LoungeUserSchema, request.get_json())
        user_data = lounge_user_data.pop('user')

        # No autoflush is required for querying the database (getting the user) before the lounge_user is populated with user and lounge (since they're primary keys).
        with db.session.no_autoflush:
            lounge_user = UserLounge(**lounge_user_data)

            lounge_user.lounge = lounge

            mapping = url_map('user_ep', user_data['href'])
            user = get_or_404(User, id = mapping['user_id'])

            # Only one user can be a host for a specific lounge
            if lounge_user.is_host:
                authorize_role_by_id('host', user.id)
                current_host = lounge.host
                current_host_user_lounge = get_or_404(UserLounge, user_id = current_host.id, lounge_id = lounge_id)
                current_host_user_lounge.is_host = False

            none_or_409(UserLounge, 'ALREADY_REGISTERED', user_id = user.id, lounge_id = lounge_id)

            user.user_lounges.append(lounge_user)

        db.session.commit()

        return LinkedLoungeUserSchema().dump(lounge_user).data, 201

api.add_resource(LoungeUserAPI, '/api/lounges/<int:lounge_id>/users/<int:user_id>/', endpoint = 'lounge_user_ep')
api.add_resource(LoungeUserListAPI, '/api/lounges/<int:lounge_id>/users/', endpoint = 'lounge_users_ep')

class UserHostApplicationSchema(ma.Schema):
    application = ma.String(required = True)
    isApproved = ma.Boolean(attribute = 'is_approved')

class LinkedUserHostApplicationSchema(UserHostApplicationSchema):
    href = ma.URLFor('user_host_application_ep', host_application_id = '<id>', user_id = '<user.id>')

class UserHostApplicationListSchema(ma.Schema):
    items = ma.Nested(LinkedUserHostApplicationSchema, many = True, attribute = 'user_host_applications')
    href = ma.URLFor('user_host_applications_ep', user_id = '<user_id>')

class UserHostApplicationAPI(Resource):
    def get(self, user_id, host_application_id):
        user_host_application = get_or_404(HostApplication, id = host_application_id, user_id = user_id)
        return LinkedUserHostApplicationSchema().dump(user_host_application).data

    def put(self, user_id, host_application_id):
        user = authorize_role('admin')
        user_host_application = get_or_404(HostApplication, id = host_application_id, user_id = user_id)

        user_host_application_data = schema_cycle(UserHostApplicationSchema, request.get_json())
        put(user_host_application, user_host_application_data)

        if user_host_application.is_approved is True:
            user_host_application.user.role = 'host'
            db.session.delete(user_host_application)
        elif user_host_application.is_approved is False:
            db.session.delete(user_host_application)

        db.session.commit()

        # If approved or denied, resource is deleted
        if user_host_application.is_approved is None:
            return self.get(user_id, host_application_id)
        else:
            return {}, 204

class UserHostApplicationListAPI(Resource):
    def get(self, user_id):
        user = get_or_404(User, id = user_id)
        user_host_applications = {
            'user_host_applications': user.host_applications.all(),
            'user_id': user.id
        }
        return UserHostApplicationListSchema().dump(user_host_applications).data

    def post(self, user_id):
        user = authorize(user_id)

        user_host_application_data = load_payload(UserHostApplicationSchema, request.get_json())

        # Can only be approved by an admin
        if 'is_approved' in user_host_application_data:
            user_host_application_data.pop('is_approved')

        host_application = HostApplication(**user_host_application_data)
        user.host_applications.append(host_application)
        db.session.commit()

        return LinkedUserHostApplicationSchema().dump(host_application).data, 201

api.add_resource(UserHostApplicationAPI, '/api/users/<int:user_id>/host_applications/<int:host_application_id>/', endpoint = 'user_host_application_ep')
api.add_resource(UserHostApplicationListAPI, '/api/users/<int:user_id>/host_applications/', endpoint = 'user_host_applications_ep')

### Expanded Schemas ###
# (sometimes reference later schemas)
# How to expand a list?
class LinkedLoungeUserSchemaExpanded(LinkedLoungeUserSchema):
    user = ma.Nested(LinkedUserSchema)

class LoungeUserListSchemaExpanded(LoungeUserListSchema):
    items = ma.Nested(LinkedLoungeUserSchemaExpanded, many = True, attribute = 'lounge_users')
