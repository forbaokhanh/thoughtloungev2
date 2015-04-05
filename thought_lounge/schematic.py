from thought_lounge import app, api, ma, db

def validate_role(role):
    if role not in ['lounger', 'host', 'admin']:
        raise ValidationError('role attribute must be either \'lounger\', \'host\', or \'admin\'.')

class UserPictureSchema(ma.Schema):
    href = ma.URLFor('picture_ep', picture_id = '<id>')
    id = ma.String('picture_ep', picture_id = '<id>')
    image = ma.URLFor('picture_image_ep', picture_id = '<id>')

class UserHostApplicationSchema(ma.Schema):
    application = ma.String(required = True)
    isApproved = ma.Boolean(attribute = 'is_approved')

class LinkedUserHostApplicationSchema(UserHostApplicationSchema):
    href = ma.URLFor('user_host_application_ep', host_application_id = '<id>', user_id = '<user.id>')

class UserHostApplicationListSchema(ma.Schema):
    items = ma.Nested(LinkedUserHostApplicationSchema, many = True, attribute = 'user_host_applications')
    href = ma.URLFor('user_host_applications_ep', user_id = '<user_id>')


class UserSignInSchema(ma.Schema):
    email = ma.String(required = True)
    password = ma.String(required = True)

class KeySchema(ma.Schema):
    key = ma.String(required = True)
    href = ma.URLFor('key_ep', user_id = '<user.id>')

class PictureSchema(ma.Schema):
    href = ma.URLFor('picture_ep', picture_id = '<id>')
    image = ma.URLFor('picture_image_ep', picture_id = '<id>')
    #image = ma.String('picture_image_ep', picture_id='<id>')

class PictureListSchema(ma.Schema):
    items = ma.Nested(PictureSchema, many = True, attribute = 'pictures')
    href = ma.URLFor('pictures_ep')

class LoungePictureSchema(ma.Schema):
    picture = ma.Nested(PictureSchema, allow_null = True, default = dict(), required = True)

class LinkedLoungePictureSchema(LoungePictureSchema):
    href = ma.URLFor('lounge_picture_ep', picture_id = '<id>', lounge_id = '<lounge_id>')

class LoungePictureListSchema(ma.Schema):
    items = ma.Nested(LinkedLoungePictureSchema, many = True, attribute = 'lounge_pictures')
    href = ma.URLFor('lounge_pictures_ep', lounge_id = '<lounge_id>')

class LoungeSchema(ma.Schema):
    dateTime = ma.DateTime(attribute = 'date_time', required = True)
    location = ma.String()
    community = ma.String()
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

class LoungeUserSchema(UserLoungeBaseSchema):
    user = ma.Hyperlinks({
        'href': ma.URLFor('user_ep', user_id = '<user_id>')
    }, required = True)

class LinkedLoungeUserSchema(LoungeUserSchema):
    href = ma.URLFor('lounge_user_ep', user_id = '<user_id>', lounge_id = '<lounge_id>')

class LoungeUserListSchema(ma.Schema):
    items = ma.Nested(LinkedLoungeUserSchema, many = True, attribute = 'lounge_users')
    href = ma.URLFor('lounge_users_ep', lounge_id = '<lounge_id>')

### Expanded Schemas ###
# (sometimes reference later schemas)
# How to expand a list?
class LinkedLoungeUserSchemaExpanded(LinkedLoungeUserSchema):
    pass

class LoungeUserListSchemaExpanded(LoungeUserListSchema):
    items = ma.Nested(LinkedLoungeUserSchemaExpanded, many = True, attribute = 'lounge_users')

class UserSchema(ma.Schema):
    email = ma.Email(required = True)
    firstName = ma.String(attribute = 'first_name', required = True)
    lastName = ma.String(attribute = 'last_name')
    bio = ma.String()
    notifications = ma.Integer(required = True)
    picture = ma.Nested(UserPictureSchema, default = dict())
    role = ma.String()
    hostApplications = ma.Nested(UserHostApplicationSchema, default = dict())
    userLounges = ma.Nested(LinkedLoungeSchema, default=dict())


LoungeSchema.loungeUsers = ma.Nested(LoungeUserSchema, default = dict())

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
    # class Meta:
    #     fields = ('bio', 'email', 'firstName', 'lastName', 'role', 'notifications', 'picture')

LinkedLoungeUserSchema.user = ma.Nested(LinkedUserSchema, default=dict())


class UserListSchema(ma.Schema):
    items = ma.Nested(UserSchema, many = True, attribute = 'users')
    href = ma.URLFor('users_ep')
