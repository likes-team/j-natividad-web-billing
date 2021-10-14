""" CORE MODELS """
from mongoengine.document import Document
from app.admin.models import Admin
from datetime import datetime

from app import db
import enum
from config import TIMEZONE
from dateutil.tz import tzutc, tzlocal
import pytz


class Base(db.Document):
    meta = {
        'abstract': True
    }

    active = db.BooleanField(default=True)
    is_deleted = db.BooleanField(default=False)
    is_archived = db.BooleanField(default=False)
    created_at = db.DateTimeField()
    # TODO: updated_at = db.DateTimeField(default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = db.DateTimeField()

    # TODO: I relate na to sa users table 
    # Sa ngayon i store nalang muna yung names kasi andaming error kapag foreign key
    created_by = db.StringField()
    updated_by = db.StringField()
    created_at_string = db.StringField()

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


    def set_created_at(self):
        date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
        naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        local_dt = TIMEZONE.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        self.created_at = utc_dt
        self.created_at_string = date_string

    def set_updated_at(self):
        date_string = str(datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))
        naive = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        local_dt = TIMEZONE.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        self.updated_at = utc_dt


class CoreModel(Base):
    meta = {
        'collection': 'core_models'
    }

    name = db.StringField()
    module = db.ReferenceField('CoreModule', required=True)
    description = db.StringField()
    admin_included = db.BooleanField(default=True)


class ModuleStatus(enum.Enum):
    installed = "Installed"
    uninstalled = "Not Installed"


class CoreModule(Base):
    meta = {
        'collection': 'core_modules'
    }

    name = db.StringField()
    short_description = db.StringField()
    long_description = db.StringField()
    status = db.StringField()
    version = db.StringField()
    models = db.ListField(db.ReferenceField('CoreModel'))


class CoreCustomer(Base):
    meta = {
        'collection': 'core_customers'
    }

    fname = db.StringField()
    lname = db.StringField()
    phone = db.StringField()
    email = db.EmailField()
    zip = db.IntField()
    street = db.StringField()


class CoreCity(Base):
    meta = {
        'collection': 'core_cities'
    }

    name = db.StringField()
    province = db.ReferenceField('CoreProvince')


class CoreProvince(Base):
    meta = {
        'collection': 'core_provinces'
    }

    name = db.StringField()


class CoreLog(db.Document):
    meta = {
        'abstract': True
    }

    date = db.DateTimeField(default=datetime.utcnow)
    description = db.StringField()
    data = db.StringField()
