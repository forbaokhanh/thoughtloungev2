import sys
sys.path.insert(0, '../thought_lounge')
from thought_lounge import app
from thought_lounge.models import *
from samples import *

from nose.tools import *
from io import BytesIO
import json, importlib

test_app = app.test_client()

def setup_func():
    app.config['ORIGINAL_SQLALCHEMY_DATABASE_URI'] = str(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FOLDER'] + 'test.db'
    app.config['TESTING'] = True
    db.create_all()

def teardown_func():
    db.session.remove()
    db.drop_all()
    app.config['SQLALCHEMY_DATABASE_URI'] = str(app.config['ORIGINAL_SQLALCHEMY_DATABASE_URI'])
    app.config['TESTING'] = False

def check_content_type(headers):
    eq_(headers['Content-Type'], 'application/json')

def test_arithmetic():
    eq_(100 + 20 + 3, 123)

headers = {
    'Content-Type': 'application/json'
}

@with_setup(setup_func, teardown_func)
def test_picture():
    # No pictures
    url = '/api/pictures/'
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('items' in resp)
    eq_(len(resp['items']), 0)

    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('image' in resp)

@with_setup(setup_func, teardown_func)
def test_user():
    # No users
    url = '/api/users/'
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('items' in resp)
    eq_(len(resp['items']), 0)

    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    resp = json.loads(rv.data.decode('utf-8'))

    # Creating a user
    url = '/api/users/'
    data = dict(users[0])
    data['picture'] = resp
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 11)
    ok_('href' in resp)
    ok_('key' in resp)
    ok_('href' in resp['key'])
    ok_('picture' in resp)
    ok_('href' in resp['picture'])
    ok_('userLounges' in resp)
    ok_('href' in resp['userLounges'])
    ok_('hostApplications' in resp)
    ok_('href' in resp['hostApplications'])
    ok_('web' in resp)
    ok_('href' in resp['web'])
    eq_(resp['email'], 'ludwig@uvienna.edu')
    eq_(resp['firstName'], 'Ludwig')
    eq_(resp['lastName'], 'Wittgenstein')
    eq_(resp['bio'], 'I\'ve solved philosophy!')
    eq_(resp['role'], 'lounger')

    # Creating a user without a picture
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[2]), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 11)
    ok_('href' in resp)
    ok_('key' in resp)
    ok_('href' in resp['key'])
    ok_('picture' in resp)
    ok_('href' not in resp['picture'])
    eq_(resp['email'], 'richard@caltech.fake.edu')

@with_setup(setup_func, teardown_func)
def test_password_auth():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    # Creating a user
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    href = json.loads(rv.data.decode('utf-8'))['href']

    # Signing in
    url = '/api/auth/sign_in/'
    data = {
        'email': 'ludwig@uvienna.edu',
        'password': 'BeetleinaBox'
    }
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(href, resp['href'])

    # Checking current user
    url = '/api/auth/sign_in/'
    rv = test_app.get(url)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(href, resp['href'])

    # Signing out
    url = '/api/auth/sign_out/'
    rv = test_app.post(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 204)

    # Checking current user (none)
    url = '/api/auth/sign_in/'
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 204)

@with_setup(setup_func, teardown_func)
def test_key():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    # Creating user
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    resp = json.loads(rv.data.decode('utf-8'))
    user_href = resp['href']
    user_key_href = resp['key']['href']
    user = User.query.all()[0]
    user_key = user.key.key
    # Creating admin
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp = json.loads(rv.data.decode('utf-8'))
    admin_href = resp['href']
    admin_key_href = resp['key']['href']
    # Hack because no admins exist yet; in practice one admin would be manually added to the database
    admin = User.query.all()[-1]
    admin.role = 'admin'
    db.session.commit()
    admin_key = admin.key.key
    # Users are signed in automatically. Last test fails because the current user signed in is an admin, we fix this by signing her out.
    rv = test_app.post('/api/auth/sign_out/')

    # Must authenticate to access keys
    url = user_key_href
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 401)

    # Admin can access admin key
    url = admin_key_href
    headers['Authorization-API-Key'] = admin_key
    rv = test_app.get(url, headers = headers)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(len(resp), 2)
    eq_(admin_key_href, resp['href'])
    eq_(admin_key, resp['key'])

    # Admin can access lounger key
    url = user_key_href
    headers['Authorization-API-Key'] = user_key
    rv = test_app.get(url, headers = headers)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(user_key_href, resp['href'])

    # Lounger can access lounger key
    url = user_key_href
    headers['Authorization-API-Key'] = user_key
    rv = test_app.get(url, headers = headers)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(user_key_href, resp['href'])

    # Lounger cannot access admin key
    url = admin_key_href
    headers['Authorization-API-Key'] = user_key
    rv = test_app.get(url, headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 403)

@with_setup(setup_func, teardown_func)
def test_user_put():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    pic2_resp = json.loads(rv.data.decode('utf-8'))

    # Creating user
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    resp = json.loads(rv.data.decode('utf-8'))
    user_href = resp['href']
    user_key_href = resp['key']['href']
    user = User.query.all()[0]
    user_key = user.key.key

    # Creating admin
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp = json.loads(rv.data.decode('utf-8'))
    admin_href = resp['href']
    admin_key_href = resp['key']['href']
    # Hack because no admins exist yet; in practice one admin would be manually added to the database
    admin = User.query.all()[-1]
    admin.role = 'admin'
    db.session.commit()
    admin_key = admin.key.key

    # Lounger can change own information but not role
    url = user_href
    # dict() to prevent mutating
    data = dict(users[0])
    data['lastName'] = data['lastName'].upper()
    data['bio'] = data['bio'].lower()
    headers['Authorization-API-Key'] = user_key
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(len(resp), 11)
    eq_('href' in resp, True)
    eq_('key' in resp, True)
    eq_('href' in resp['key'], True)
    eq_(resp['email'], 'ludwig@uvienna.edu')
    eq_(resp['firstName'], 'Ludwig')
    eq_(resp['lastName'], 'WITTGENSTEIN')
    eq_(resp['bio'], 'i\'ve solved philosophy!')
    eq_(resp['role'], 'lounger')

    # Admin can change lounger's information including role
    url = user_href
    data = dict(users[0])
    data['lastName'] = data['lastName'].lower()
    data['bio'] = data['bio'].upper()
    data['role'] = 'host'
    data['picture'] = {'href': pic2_resp['href']}
    headers['Authorization-API-Key'] = admin_key
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(rv.status_code, 200)
    eq_(len(resp), 11)
    eq_('href' in resp, True)
    eq_('key' in resp, True)
    eq_('href' in resp['key'], True)
    eq_(resp['email'], 'ludwig@uvienna.edu')
    eq_(resp['firstName'], 'Ludwig')
    eq_(resp['lastName'], 'wittgenstein')
    eq_(resp['bio'], 'I\'VE SOLVED PHILOSOPHY!')
    eq_(resp['role'], 'host')
    eq_(resp['picture']['href'], pic2_resp['href'])

@with_setup(setup_func, teardown_func)
def test_lounge():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    # Creating user
    url = '/api/users/'

    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp_host1 = json.loads(rv.data.decode('utf-8'))
    for host in User.query.all():
        host.role = 'host'
    db.session.commit()

    # No lounges
    url = '/api/lounges/'
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('items' in resp)
    eq_(len(resp['items']), 0)

    # Need authentication to create a lounge
    url = '/api/lounges/'
    rv = test_app.post(url, data = json.dumps(lounges[0]))
    check_content_type(rv.headers)
    eq_(rv.status_code, 401)
    resp = json.loads(rv.data.decode('utf-8'))

    # Creating a lounge
    url = '/api/lounges/'
    headers['Authorization-API-Key'] = User.query.get(2).key.key,
    rv = test_app.post(url, data = json.dumps(lounges[0]), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 10)
    ok_('href' in resp)
    ok_('pictures' in resp)
    eq_(resp['dateTime'], '2015-02-25T03:00:00+00:00')
    eq_(resp['location'], '')
    eq_(resp['campus'], 'UC Berkeley')
    eq_(resp['isReserved'], False)
    eq_(resp['summary'], '')
    # Checking if the host was added properly
    rv = test_app.get(resp['loungeUsers']['href'] + '?type=host?expand=user', headers = headers)
    host_resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(host_resp), 2)
    ok_('href' in host_resp)
    ok_('href' in host_resp['items'][0])
    eq_(len(host_resp['items']), 1)
    eq_(host_resp['items'][0]['user']['href'], resp_host1['href'])

    # Changing the lounge
    url = '/api/lounges/1/'
    headers['Authorization-API-Key'] = User.query.get(2).key.key,
    data = dict(lounges[0])
    data.pop('campus')
    data['location'] = 'Haas B2'
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 10)
    ok_('href' in resp)
    ok_('pictures' in resp)
    eq_(resp['dateTime'], '2015-02-25T03:00:00+00:00')
    eq_(resp['location'], 'Haas B2')
    eq_(resp['campus'], '')
    eq_(resp['isReserved'], False)
    eq_(resp['summary'], '')

@with_setup(setup_func, teardown_func)
def test_lounge_picture():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    resp_picture1 = json.loads(rv.data.decode('utf-8'))

    # Creating user
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    resp_user1 = json.loads(rv.data.decode('utf-8'))
    for host in User.query.all():
        host.role = 'host'
    db.session.commit()

    # Creating a lounge
    url = '/api/lounges/'
    headers['Authorization-API-Key'] = User.query.get(1).key.key,
    rv = test_app.post(url, data = json.dumps(lounges[3]), headers = headers)
    resp_lounge1 = json.loads(rv.data.decode('utf-8'))

    # Need authorization to add a picture
    url = resp_lounge1['pictures']['href']
    headers['Authorization-API-Key'] = "mywrongapikey",
    data = {'picture': {'href': resp_picture1['href']}}
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 401)

    # Adding a picture
    url = resp_lounge1['pictures']['href']
    headers['Authorization-API-Key'] = User.query.get(1).key.key,
    data = {'picture': {'href': resp_picture1['href']}}
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp_lounge_picture1 = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp_lounge_picture1), 2)
    print(resp_lounge_picture1)
    ok_('href' in resp_lounge_picture1)
    ok_('picture' in resp_lounge_picture1)
    ok_('href' in resp_lounge_picture1['picture'])
    eq_(resp_lounge_picture1['picture']['href'], resp_picture1['href'])
    eq_(resp_lounge_picture1['picture']['image'], resp_picture1['image'])

    # Deleting a picture
    url = resp_lounge_picture1['href']
    headers['Authorization-API-Key'] = User.query.get(1).key.key,
    rv = test_app.delete(url, headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 204)

    # No pictures in lounge
    url = resp_lounge1['pictures']['href']
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('items' in resp)
    eq_(len(resp['items']), 0)

@with_setup(setup_func, teardown_func)
def test_user_lounge():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    # Creating user
    url = '/api/users/'

    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    resp_user1 = json.loads(rv.data.decode('utf-8'))
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp_user2 = json.loads(rv.data.decode('utf-8'))

    for host in User.query.all():
        host.role = 'host'
    db.session.commit()

    # Creating a lounge
    url = '/api/lounges/'
    headers['Authorization-API-Key'] = User.query.get(1).key.key

    rv = test_app.post(url, data = json.dumps(lounges[0]), headers = headers)
    resp_lounge1 = json.loads(rv.data.decode('utf-8'))
    rv = test_app.post(url, data = json.dumps(lounges[1]), headers = headers)
    resp_lounge2 = json.loads(rv.data.decode('utf-8'))

    headers['Authorization-API-Key'] = User.query.get(2).key.key
    # Adding a user lounge
    url = resp_user2['userLounges']['href']
    data = dict(user_lounges[1])
    data['isHost'] = False
    data['lounge'] = {'href': resp_lounge1['href']}
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = resp_user_lounge1 = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 6)
    ok_('href' in resp)
    ok_('lounge' in resp)
    ok_('href' in resp['lounge'])
    eq_(resp['topic'], 'I saw the best minds of my generation destroyed by madness.')
    eq_(resp['summary'], 'Starving hysterical naked, dragging themselves through the negro streets at dawn looking for an angry fix.')
    eq_(resp['showedUp'], True)
    eq_(resp['isHost'], False)
    eq_(resp['lounge']['href'], resp_lounge1['href'])

    # Adding a user lounge in conflict
    headers['Authorization-API-Key'] = User.query.get(2).key.key
    url = resp_user2['userLounges']['href']
    data = user_lounges[1]
    data['isHost'] = False
    data['lounge'] = {'href': resp_lounge1['href']}
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 409)

    # Changing a user lounge
    url = resp_user_lounge1['href']
    data = dict(user_lounges[1])
    data['lounge'] = {'href': resp_lounge2['href']}
    data['showedUp'] = False
    data['isHost'] = False
    headers['Authorization-API-Key'] = User.query.get(2).key.key
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 6)
    ok_('href' in resp)
    ok_('lounge' in resp)
    ok_('href' in resp['lounge'])
    eq_(resp['topic'], 'I saw the best minds of my generation destroyed by madness.')
    eq_(resp['summary'], 'Starving hysterical naked, dragging themselves through the negro streets at dawn looking for an angry fix.')
    eq_(resp['showedUp'], False)
    eq_(resp['isHost'], False)
    eq_(resp['lounge']['href'], resp_lounge2['href'])

@with_setup(setup_func, teardown_func)
def test_lounge_user():
    # Creating a picture
    url = '/api/pictures/'
    files = {
        'file': (BytesIO(pictures[0]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)
    files = {
        'file': (BytesIO(pictures[1]['bytes']), 'user.jpg')
    }
    rv = test_app.post(url, data = files)

    # Creating user
    url = '/api/users/'

    rv = test_app.post(url, data = json.dumps(users[0]), headers = headers)
    resp_user1 = json.loads(rv.data.decode('utf-8'))
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp_user2 = json.loads(rv.data.decode('utf-8'))
    rv = test_app.post(url, data = json.dumps(users[2]), headers = headers)
    resp_user3 = json.loads(rv.data.decode('utf-8'))

    for host in User.query.all():
        host.role = 'host'
    db.session.commit()

    # Creating a lounge
    url = '/api/lounges/'
    headers['Authorization-API-Key'] = User.query.get(1).key.key

    rv = test_app.post(url, data = json.dumps(lounges[0]), headers = headers)
    resp_lounge1 = json.loads(rv.data.decode('utf-8'))
    rv = test_app.post(url, data = json.dumps(lounges[1]), headers = headers)
    resp_lounge2 = json.loads(rv.data.decode('utf-8'))

    # Adding a lounge user
    url = resp_lounge1['loungeUsers']['href']
    data = dict(user_lounges[1])
    data['user'] = {'href': resp_user2['href']}
    data['isHost'] = False
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = resp_lounge_user1 = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 6)
    ok_('href' in resp)
    ok_('user' in resp)
    ok_('href' in resp['user'])
    eq_(resp['topic'], 'I saw the best minds of my generation destroyed by madness.')
    eq_(resp['summary'], 'Starving hysterical naked, dragging themselves through the negro streets at dawn looking for an angry fix.')
    eq_(resp['showedUp'], True)
    eq_(resp['isHost'], False)
    eq_(resp['user']['href'], resp_user2['href'])

    # Adding a user lounge in conflict
    url = resp_lounge1['loungeUsers']['href']
    data = user_lounges[1]
    data['user'] = {'href': resp_user1['href']}
    rv = test_app.post(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 409)

    # Changing a lounge user
    url = resp_lounge_user1['href']
    data = dict(user_lounges[1])
    data['user'] = {'href': resp_user3['href']}
    data['isHost'] = False
    data['showedUp'] = False
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 6)
    ok_('href' in resp)
    ok_('user' in resp)
    ok_('href' in resp['user'])
    eq_(resp['topic'], 'I saw the best minds of my generation destroyed by madness.')
    eq_(resp['summary'], 'Starving hysterical naked, dragging themselves through the negro streets at dawn looking for an angry fix.')
    eq_(resp['showedUp'], False)
    eq_(resp['isHost'], False)
    eq_(resp['user']['href'], resp_user3['href'])

@with_setup(setup_func, teardown_func)
def test_host_application():
    # Creating admin
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[1]), headers = headers)
    resp = json.loads(rv.data.decode('utf-8'))
    admin_href = resp['href']
    admin_key_href = resp['key']['href']
    # Hack because no admins exist yet; in practice one admin would be manually added to the database
    admin = User.query.get(1)
    admin.role = 'admin'
    db.session.commit()
    admin_key = admin.key.key

    # Creating user
    url = '/api/users/'
    rv = test_app.post(url, data = json.dumps(users[2]), headers = headers)
    resp_user1 = json.loads(rv.data.decode('utf-8'))

    # No user host applications
    url = resp_user1['hostApplications']['href']
    rv = test_app.get(url)
    check_content_type(rv.headers)
    eq_(rv.status_code, 200)
    resp = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 2)
    ok_('href' in resp)
    ok_('items' in resp)
    eq_(resp['href'], url)
    eq_(len(resp['items']), 0)

    # Need authentication to create a host application
    url = resp_user1['hostApplications']['href']
    rv = test_app.post(url, data = json.dumps(host_applications[0]))
    check_content_type(rv.headers)
    eq_(rv.status_code, 401)
    resp = json.loads(rv.data.decode('utf-8'))

    # Creating a host application
    url = resp_user1['hostApplications']['href']
    headers['Authorization-API-Key'] = User.query.get(2).key.key,
    rv = test_app.post(url, data = json.dumps(host_applications[0]), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 201)
    resp = resp_user_host_application1 = json.loads(rv.data.decode('utf-8'))
    eq_(len(resp), 3)
    ok_('href' in resp)
    eq_(resp['application'], 'Make me a host!')
    eq_(resp['isApproved'], None)

    # Changing the host application
    url = resp_user_host_application1['href']
    headers['Authorization-API-Key'] = User.query.get(1).key.key,
    data = dict(host_applications[0])
    data['isApproved'] = True
    rv = test_app.put(url, data = json.dumps(data), headers = headers)
    check_content_type(rv.headers)
    eq_(rv.status_code, 204)
