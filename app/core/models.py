""" CORE MODELS """
from datetime import datetime
import enum
from flask_login import current_user
from bson.objectid import ObjectId
import pytz
from app import mongo
from config import TIMEZONE


class BaseModel(object):
    _id: ObjectId
    active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    def __init__(self, data=None):
        self._id = ObjectId()
        
        if data is not None:
            self.__dict__.update(data)
            self._id = data.get('_id', None)
            self.active = data.get('active', True)
            self.created_at = data.get('created_at', None)
            self.updated_at = data.get('updated_at', None)
            self.created_by = data.get('created_by', None)
            self.updated_by = data.get('updated_by', None)
            return None

    def __repr__(self):
        return str(self.__dict__)

    @property
    def id(self):
        return self._id

    def save(self, session=None):
        self.created_at = datetime.utcnow()
        self.created_by = current_user.full_name if current_user is None else 'System'

        if session:
            self.__collection__.insert_one(self.__dict__, session=session)
        else:        
            self.__collection__.insert_one(self.__dict__)

    def update(self):
        pass
        # self.__collection__.update_one(
        #     {'_id': self._id},
        #     {'$set': self.__dict__})


    def delete(self):
        pass

    def toJson(self):
        return self.__dict__

    @classmethod
    def find_one_by_id(cls, id):
        try:
            query = cls.__collection__.find_one({'_id': ObjectId(id)})

            return cls(data=query)
        except Exception:
            return None

    @classmethod
    def count(cls):
        try:
            return cls.__collection__.find().count()
        except AttributeError:
            raise AttributeError("{model_name} Collection is not implemented".format(model_name=cls().__class__.__name__))

    @classmethod
    def find_all(cls):
        try:
            models = list(cls.__collection__.find())
            
            data = []

            for model in models:
                data.append(cls(data=model))

            return data
        except AttributeError:
            raise AttributeError("{model_name} Collection is not implemented".format(model_name=cls().__class__.__name__))

    @property
    def created_at_local(self):
        local_datetime = ''
        if self.created_at is not None:
            local_datetime = self.created_at.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            return local_datetime.strftime("%B %d, %Y %I:%M %p")
            
        return local_datetime

    @property
    def updated_at_local(self):
        local_datetime = ''
        if self.updated_at is not None:
            local_datetime = self.updated_at.replace(tzinfo=pytz.utc).astimezone(TIMEZONE)
            return local_datetime.strftime("%B %d, %Y %I:%M %p")
            
        return local_datetime

    # active = db.BooleanField(default=True)
    # is_deleted = db.BooleanField(default=False)
    # is_archived = db.BooleanField(default=False)
    # created_at = db.DateTimeField()
    # # TODO: updated_at = db.DateTimeField(default=datetime.utcnow, onupdate=datetime.utcnow)
    # updated_at = db.DateTimeField()

    # # TODO: I relate na to sa users table 
    # # Sa ngayon i store nalang muna yung names kasi andaming error kapag foreign key
    # created_by = db.StringField()
    # updated_by = db.StringField()
    # created_at_string = db.StringField()


    # def set_created_at(self):
    #     date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
    #     naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    #     local_dt = TIMEZONE.localize(naive, is_dst=None)
    #     utc_dt = local_dt.astimezone(pytz.utc)
    #     self.created_at = utc_dt
    #     self.created_at_string = date_string

    # def set_updated_at(self):
    #     date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
    #     naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    #     local_dt = TIMEZONE.localize(naive, is_dst=None)
    #     utc_dt = local_dt.astimezone(pytz.utc)
    #     self.updated_at = utc_dt


class ModuleStatus(enum.Enum):
    installed = "Installed"
    uninstalled = "Not Installed"


class CoreModule(BaseModel):
    __collection__ = mongo.db.core_modules

    name: str
    short_description: str
    long_description: str
    status: str
    version: str
    models: list

    def __init__(self, data=None):
        super(CoreModule, self).__init__(data=data)
        self.name = data.get('name', '')
        self.short_description = data.get('short_description', '')
        self.long_description = data.get('long_description', '')
        self.status = data.get('status', '')
        self.version = data.get('version', '')
        self.models = data.get('models', [])

    @classmethod
    def find_by_id(cls, id):
        return cls(data=cls.__collection__.find_one({'_id': ObjectId(id)}))


class CoreModel(BaseModel):
    __collection__ = mongo.db.core_models

    name: str
    module_id: CoreModule
    description: str
    admin_included: bool
    _module: CoreModule

    def __init__(self, data=None):
        super(CoreModel, self).__init__(data=data)
        self.name = data.get('name', '')
        self.description = data.get('description', '')
        self.admin_included = data.get('admin_included', True)
        self._module = CoreModule(data=data['module'][0]) if 'module' in data else None

    @property
    def module(self):
        return self._module

    @classmethod
    def find_one_by_name(cls, name):
        query = cls.__collection__.aggregate([
            {"$match": {"name": name}},
            {"$lookup": {"from": "core_modules", "localField": "module_id",
                         "foreignField": "_id", 'as': "module"}}
        ])

        return cls(data=list(query)[0])


class CoreCity(BaseModel):
    name: str
    province: str


class CoreProvince(BaseModel):
    name: str


class CoreLog(BaseModel):
    date: datetime
    description: str
    data: str
