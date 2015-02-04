# thought-lounge 
## Introduction
Thought Lounge is 'a formatted dialogue with strangers on the urgent topics of utmost interest to them, efficiently and in a "safe space."' This is the repository for http://www.thoughtlounge.org, which automates the process or signing up for and logging thought lounges.

## API
Thought Lounge uses a RESTful API to interface with the front-end.

### Endpoints
In general, GET/POST/PUT/DELETE matches with CRUD. <b>PUT is always idempotent</b>. All resources are HATEOAS linked to themselves and related resources. The notion of identity within the RESTful API is the resource hypertext link, and this will be used for all relations, not database ids.
```
Users
GET, POST /api/users/
GET, PUT /api/users/<int:user_id>/
GET, POST /api/users/
GET, PUT /api/users/<int:user_id>/
GET, POST /api/users/<int:user_id>/key/ 

Authentication
GET, POST /api/auth/sign_in/
POST /api/auth/sign_out/

Pictures
GET, POST /api/pictures/
GET /api/pictures/<int:picture_id>/
GET /api/pictures/cdn/<int:picture_id>/

Lounges
GET, POST /api/lounges/
GET, PUT, DELETE /api/lounges/<int:lounge_id>/
GET, POST /api/lounges/<int:lounge_id>/pictures/
GET, DELETE /api/lounges/<int:lounge_id>/pictures/<int:picture_id>/

UserLounges and LoungeUsers
GET, POST /api/users/<int:user_id>/lounges/ 
GET, PUT /api/users/<int:user_id>/lounges/<int:lounge_id>/
GET, POST /api/lounges/<int:lounge_id>/users/ 
GET, PUT /api/lounges/<int:lounge_id>/users/<int:user_id>/

HostApplications
GET, POST /api/users/<int:user_id>/host_applications/
GET, PUT /api/users/<int:user_id>/host_applications/<int:host_application_id>/
```
#### Users
##### Retrieving user information
###### Request
```
GET /api/users/ HTTP/1.1
```
###### Response
```
200 OK
{
    href: "/api/users/",
    items: [
        {
            bio: "I'm from San Diego.",
            email: "john@berkeley.edu",
            firstName: "John",
            href: "/api/users/1/",
            lastName: "Steinbeck",
            role: "lounger"
        },
        {
            bio: "I'm from Paris.",
            email: "luce@uleuven.edu",
            firstName: "Luce",
            href: "/api/users/2/",
            lastName: "Irigaray",
            role: "admin"
        }
    ]
}
```
###### Request
```
GET /api/users/2/ HTTP/1.1
```
###### Response
```
200 OK
{
    bio: "I'm from Paris.",
    email: "luce@uleuven.edu",
    firstName: "Luce",
    href: "/api/users/2/",
    lastName: "Irigaray",
    role: "admin"
}
```
##### Creating users
###### Request
```
POST /api/users/ HTTP/1.1
{
    email [required]: "ludwig@uvienna.edu",
    password [required]: "BeetleinaBox",
    firstName: "Ludwig",
    lastName: "Wittgenstein",
    bio: "I've solved philosophy!",
    role: "host" // "lounger" (default), "host", or "admin"
}
```
###### Response
```
201 Created
{
    "bio": "I've solved philosophy!",
    "email": "ludwig@uvienna.edu",
    "firstName": "Ludwig",
    "href": "/api/users/3/",
    "lastName": "Wittgenstein",
    "role": "host"
}
```
##### Signing in
###### Request
```
POST /api/auth/sign_in/ HTTP/1.1
{
    email [required]: "ludwig@uvienna.edu",
    password [required]: "BeetleinaBox"
}
```
###### Response
```
200 OK
{
    "bio": "I've solved philosophy!",
    "email": "ludwig@uvienna.edu",
    "firstName": "Ludwig",
    "href": "/api/users/3/",
    "lastName": "Wittgenstein",
    "role": "host"
}
```
##### Checking which user is signed in
###### Request
```
GET /api/auth/sign_in/ HTTP/1.1
```
###### Response (204 No Content if no user signed in)
```
200 OK
{
    bio: "I've solved philosophy!",
    email: "ludwig@uvienna.edu",
    firstName: "Ludwig",
    href: "/api/users/3/",
    lastName: "Wittgenstein",
    role: "host"
}
```
##### Signing out
###### Request
```
POST /api/auth/sign_out/ HTTP/1.1
{}
```
###### Response
```
204 No Content
```
