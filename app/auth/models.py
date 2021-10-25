""" MODULE: AUTH.MODELS """
""" FLASK IMPORTS """

"""--------------END--------------"""

""" PYTHON IMPORTS """

"""--------------END--------------"""

""" APP IMPORTS  """
"""--------------END--------------"""


# messenger_areas = db.Table('bds_messenger_areas',
#     db.Column('area_id', db.Integer, db.ForeignKey('bds_area.id', ondelete='CASCADE'), primary_key=True),
#     db.Column('messenger_id', db.Integer, db.ForeignKey('auth_user.id', ondelete='CASCADE'), primary_key=True)
# )




from bson.objectid import ObjectId
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager, mongo
from app.admin.models import Admin
from app.core.models import BaseModel, CoreModel



class RolePermission(object):
    model_name: str
    read: bool
    create: bool
    write: bool
    delete: bool

    def __init__(self, data=None):
        if data is not None:
            self.model_name = data.get('model_name', '')
            self.read = data.get('read', False)
            self.create = data.get('create', False)
            self.write = data.get('write', False)
            self.delete = data.get('delete', False)

    @classmethod
    def load(cls, data: list):
        permissions = []

        for dict in data:
            permissions.append(
                cls(data=dict)
            )

        return permissions


class Role(BaseModel, Admin):
    __tablename__ = 'auth_user_roles'
    __amname__ = 'role'
    __amicon__ = 'pe-7s-id'
    __amdescription__ = "Roles"
    __view_url__ = 'bp_auth.roles'
    __collection__ = mongo.db.auth_user_roles

    """ COLUMNS """
    name: str
    permissions: list

    def __init__(self, data=None):
        super(Role, self).__init__(data=data)

        if data is not None:
            self.permissions = RolePermission.load(data=data.get('permissions', []))

    @classmethod
    def find_one_by_name(cls, name):
        try:
            query = cls.__collection__.find_one({'name': name})
            return cls(data=query)
        except Exception:
            raise Exception("No role found from the name({}) given".format(name))


class User(UserMixin, BaseModel, Admin):
    __tablename__ = 'auth_user'
    __amname__ = 'user'
    __amicon__ = 'pe-7s-users'
    __amdescription__ = "Users"
    __view_url__ = 'bp_auth.users'

    __collection__ = mongo.db.auth_users

    username: str
    fname: str
    lname: str
    email: str
    password_hash: str
    image_path: str
    permissions: list
    is_superuser: bool
    role_id: ObjectId
    role_name: str
    is_admin: bool
    _role: Role

    def __init__(self, data=None):
        super(User, self).__init__(data=data)
        
        if data is not None:
            self.username = data.get('username', '')
            self.fname = data.get('fname', '')
            self.lname = data.get('lname', '')
            self.email = data.get('email', '')
            self.password_hash = data.get('password_hash', '')
            self.image_path = data.get("image_path", 'img/user_default_image.png')
            self.permissions = data.get("permissions", [])
            self.is_superuser = data.get('is_superuser', False)
            self.is_admin = data.get('is_admin', False)

            if 'role' in data:
                self._role = Role(data=data['role'][0])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def name(self):
        return self.fname + self.lname

    @property
    def full_name(self):
        return self.fname + " " + self.lname

    @property
    def role(self) -> Role:
        return self._role

    @classmethod
    def find_one_by_username(cls, username):
        query = mongo.db.auth_users.aggregate([
            {"$match": {"username": username}},
            {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                         "foreignField": "_id", 'as': "role"}}
        ])

        return cls(data=list(query)[0])

    @classmethod
    def find_one_by_id(cls, id, session=None):
        if session:
            query = cls.__collection__.aggregate([
                {"$match": {"_id": ObjectId(id)}},
                {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                            "foreignField": "_id", 'as': "role"}},
            ],session=session)
        else:
            query = cls.__collection__.aggregate([
                {"$match": {"_id": ObjectId(id)}},
                {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                            "foreignField": "_id", 'as': "role"}},
            ])

        return cls(data=list(query)[0])

    @classmethod
    def find_all(cls):
        users = list(cls.__collection__.aggregate([
            {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                         "foreignField": "_id", 'as': "role"}}
        ]))
        
        data = []
        for user in users:
            data.append(cls(data=user))

        return data

    @classmethod
    def find_all_by_role_id(cls, role_id):
        users = list(cls.__collection__.aggregate([
            {"$match": {"role_id": ObjectId(role_id)}},
            {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                         "foreignField": "_id", 'as': "role"}}
        ]))
        
        data = []
        for user in users:
            data.append(cls(data=user))
            
        return data


class UserPermission(BaseModel):
    meta = {
        'collection': 'auth_user_permissions'
    }

    model: CoreModel
    read: bool
    create: bool
    write: bool
    doc_delete: bool

    def __init__(self):
        self.read = True
        self.create = False
        self.write = False
        self.doc_delete = False


@login_manager.user_loader
def load_user(user_id):
    user = User.find_one_by_id(user_id)
    return user
