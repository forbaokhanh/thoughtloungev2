from thought_lounge import app, db
from thought_lounge.models import *
from tests.samples import *
import os, requests, datetime, json

print('Resetting database...starting...')

db.drop_all()
db.create_all()

prefix = 'http://localhost:5000'

# So we don't send emails
app.config['TESTING'] = True

headers = {
    'Content-Type': 'application/json'
}

admin = User(email = 'admin@thoughtlounge.org', password = 'password', first_name = 'Admin', last_name = 'Istrator', bio = 'I\'m from the land of Adminia.')
db.session.add(admin)
admin.role = 'admin'
db.session.commit()
admin_key = admin.key.key

picture_reps = []
for picture_data in pictures:
    rv = requests.get(picture_data['href'])
    resp = rv.json()
    picture_href = resp['results'][0]['user']['picture']['medium']
    rv = requests.get(picture_href)
    resp = rv.content
    rv = requests.post(prefix + '/api/pictures/', files = {'file': ('picture.jpg', resp)})
    resp = rv.json()
    picture_reps.append(resp)
print(picture_reps)

user_reps = []
for index, user_data in enumerate(users):
    user_data['picture'] = {
        'href': picture_reps[index]['href']
    }
    rv = requests.post(prefix + '/api/users/', data = json.dumps(user_data), headers = headers)
    print(json.dumps(user_data))
    user_reps.append(rv.json())
print(user_reps)

admin_headers = dict(headers)
admin_headers['Authorization-API-Key'] = admin_key
user_reps[0]['role'] = 'host'
user_reps[1]['role'] = 'host'
requests.put(prefix + user_reps[0]['href'], data = json.dumps(user_reps[0]), headers = admin_headers)
requests.put(prefix + user_reps[1]['href'], data = json.dumps(user_reps[1]), headers = admin_headers)

lounge_reps = []
for index, lounge_data in enumerate(lounges):
    host_rep = user_reps[index % 2]
    host_key_rv = requests.get(prefix + host_rep['key']['href'], headers = admin_headers)
    host_key_resp = host_key_rv.json()
    host_key = host_key_resp['key']
    headers['Authorization-API-Key'] = host_key
    rv = requests.post(prefix + '/api/lounges/', data = json.dumps(lounge_data), headers = headers)
    lounge_reps.append(rv.json())
print(lounge_reps)

# Only lounge_reps that have passed get user_lounges
for index, lounge_rep in enumerate(lounge_reps[-4:]):
    host_user_lounge_rv = requests.get(prefix + lounge_rep['loungeUsers']['href'], params = {'type': 'host'})
    host_user_lounge_rep = host_user_lounge_rv.json()
    host_rv = requests.get(prefix + host_user_lounge_rep['items'][0]['user']['href'])
    host_rep = host_rv.json()
    host_key_rv = requests.get(prefix + host_rep['key']['href'], headers = admin_headers)
    host_key_resp = host_key_rv.json()
    host_key = host_key_resp['key']
    headers['Authorization-API-Key'] = host_key

    user_lounge = user_lounges[index]
    user_lounge['user'] = {
        'href': host_rep['href']
    }

    requests.put(prefix + host_user_lounge_rep['items'][0]['href'], data = json.dumps(user_lounge), headers = headers)

    user_lounge = user_lounges[index + 4]
    user_lounge['user'] = {
        'href': user_reps[(index % 2) + 2]['href']
    }
    requests.post(prefix + lounge_rep['loungeUsers']['href'], data = json.dumps(user_lounge), headers = headers)

# So we don't send emails
app.config['TESTING'] = False

print('Resetting database...completed.')
