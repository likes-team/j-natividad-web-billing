from bson.objectid import ObjectId
from app.admin.models import Admin
from app.auth.models import User
from app.core.models import BaseModel
from datetime import date, datetime
from decimal import Decimal
from app import mongo

class Billing(BaseModel, Admin):
    __tablename__ = 'bds_billings'
    __amname__ = 'billing'
    __amdescription__ = 'Billings'
    __amicon__ = 'pe-7s-cash'
    __view_url__ = 'bp_bds.billings'
    __collection__ = mongo.db.bds_billings

    billing_no: int
    full_billing_no: str
    name: str
    description: str
    # deliveries = db.relationship('Delivery', cascade='all,delete', backref="billing")
    date_from: datetime
    date_to: datetime


class Area(BaseModel, Admin):
    __tablename__ = 'bds_areas'
    __amname__ = 'area'
    __amdescription__ = 'Locations'
    __amicon__ = 'pe-7s-flag'
    __amfunctions__ = [
        ("Sub Areas", "bp_bds.sub_areas", 'sub_area'),
        ("Areas", "bp_bds.areas", 'area'),
        ("Municipalities", "bp_bds.municipalities", 'municipality'),
        ]
    __collection__ = mongo.db.bds_areas

    """ COLUMNS """
    name: str = None
    description: str = None
    municipality_id: ObjectId = None
    messengers: list = None

    @classmethod
    def find_all_by_municipality_id(cls, id):
        areas = list(cls.__collection__.aggregate([
            {"$match": {
                'municipality_id': ObjectId(id)
            }},
            {"$lookup": {"from": "bds_municipalities", "localField": "municipality_id",
                         "foreignField": "_id", 'as': "municipality"}}
        ]))

        data = []
        for area in areas:
            data.append(cls(data=area))
        return data

    @classmethod
    def find_one_by_name(cls, name):
        try:
            query = cls.__collection__.find_one({'name': name})
            return cls(data=query)
        except Exception:
            raise Exception("No area found from the name({}) given".format(name))


class SubArea(BaseModel, Admin):
    __tablename__ = 'bds_sub_areas'
    __amname__ = 'sub_area'
    __amdescription__ = 'Sub Areas'
    __amicon__ = 'pe-7s-flag'
    __parent_model__ = 'area'
    #__list_view_url__ = 'bp_bds.areas'
    __collection__ = mongo.db.bds_sub_areas

    """ COLUMNS """
    name: str
    description: str
    area_id: ObjectId

    @classmethod
    def find_all_by_area_id(cls, id):
        sub_areas = list(cls.__collection__.aggregate([
            {"$match": {
                "area_id": ObjectId(id)
            }},
            {"$lookup": {"from": "bds_areas", "localField": "area_id",
                         "foreignField": "_id", 'as': "area"}}
        ]))

        data = []
        for sub_area in sub_areas:
            data.append(cls(data=sub_area))
        return data


class Municipality(BaseModel, Admin):
    __tablename__ = 'bds_municipalities'
    __amname__ = 'municipality'
    __amdescription__ = 'Municipalities'
    __amicon__ = 'pe-7s-flag'
    __parent_model__ = 'area'
    __collection__ = mongo.db.bds_municipalities

    name: str
    description: str

    def __init__(self, data=None):
        super(Municipality, self).__init__(data=data)

        if data is not None:
            self.name = data.get('name', '')
            self.description = data.get('description', '')

    @classmethod
    def find_one_by_name(cls, name):
        try:
            query = cls.__collection__.find_one({'name': name})
            return cls(data=query)
        except Exception:
            raise Exception("No municipality found from the name({}) given".format(name))


class DeliveryMap(Admin):
    __amname__ = 'delivery_map'
    __amdescription__ = 'Delivery Map'
    __amicon__ = 'pe-7s-map-2'
    __view_url__ = 'bp_bds.delivery_map'


class Dashboard(Admin):
    __amname__ = 'dashboard'
    __amdescription__ = 'Dashboard'
    __amicon__ = 'pe-7s-map-2'
    __view_url__ = 'bp_bds.dashboard'


class Messenger(User):
    __tablename__ = 'auth_users'
    __amname__ = 'user'
    __amdescription__ = 'Messengers'
    __amicon__ = 'pe-7s-car'
    __view_url__ = 'bp_bds.messengers'

    areas: list = []

    def __init__(self, data=None):
        super(Messenger, self).__init__(data=data)
        
        if data is not None:
            self.areas = data.get('areas', [])

    
    @property
    def areas_obj(self):
        areas = []
        for area_id in self.areas:
            areas.append(Area.find_one_by_id(id=area_id))
        return areas

    def update(self):
        self.__collection__.update_one({
            '_id': self.id
        },
        {'$set': {
            'fname': self.fname,
            'lname': self.lname,
            'email': self.email,
            'username': self.username,
            'areas': self.areas
            }
        })


class Subscriber(User):
    __tablename__ = 'bds_subscribers'
    __amname__ = 'subscriber'
    __amdescription__ = 'Subscribers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'bp_bds.subscribers'
    __collection__ = mongo.db.auth_users

    """ COLUMNS """
    mname: str
    contract_no: str
    address: str
    mobile_no: str
    longitude: str
    latitude: str
    accuracy: str
    cycle: int
    establishment: str
    # deliveries = db.relationship('Delivery', cascade='all,delete', backref="subscriber",order_by="desc(Delivery.delivery_date)")
    sub_area_id: ObjectId
    _sub_area: SubArea
    sub_area_name: str

    def __init__(self, data=None):
        super(Subscriber, self).__init__(data=data)

        if data is not None:
            self.mname = data.get('mname', '')
            self.contract_no = data.get('contract_no', '')
            self.address = data.get('address', '')
            self.mobile_no = data.get('mobile_no')
            self.longitude = data.get('longitude', None)
            self.latitude = data.get('latitude', None)
            self.accuracy = data.get('accuracy', None)
            self.sub_area_name = data.get('sub_area_name', '')

            if 'sub_area' in data and len(data['sub_area']) > 0:
                self._sub_area = SubArea(data=data['sub_area'][0])

    @property
    def url(self):
        return "bp_bds.subscribers"

    @property
    def sub_area(self):
        return self._sub_area


class Delivery(BaseModel, Admin):
    __tablename__ = 'bds_deliveries'
    __amname__ = 'delivery'
    __amdescription__ = 'Deliveries'
    __amicon__ = 'pe-7s-paper-plane'
    __view_url__ = 'bp_bds.deliveries'
    __collection__ = mongo.db.bds_deliveries
    
    """ COLUMNS """
    billing_id: ObjectId = None
    subscriber_id: ObjectId = None
    _subscriber: Subscriber = None
    sub_area_id: ObjectId = None
    _sub_area: SubArea = None
    area_id: ObjectId = None
    _area: Area = None
    messenger_id: ObjectId = None
    _messenger: Messenger = None
    delivery_date: datetime = None
    date_delivered: datetime = None
    date_mobile_delivery: datetime = None
    status: str = None
    image_path: str = None
    accuracy: str = None
    delivery_longitude: Decimal = None
    delivery_latitude: Decimal = None

    def __init__(self, data=None):
        super(Delivery, self).__init__(data=data)

        if data is not None:
            self.status = data.get('status')

            if 'subscriber' in data:
                self._subscriber = Subscriber(data=data['subscriber'][0])
            if 'area' in data:
                self._area = Area(data=data['area'][0])
            if 'sub_area' in data:
                self._sub_area = SubArea(data=data['sub_area'][0])
            if 'messenger' in data:
                self._messenger = Messenger(data=data['messenger'][0])

    @property
    def subscriber(self):
        return self._subscriber

    @property
    def area(self):
        return self._area

    @property
    def sub_area(self):
        return self._sub_area

    @property
    def messenger(self):
        return self._messenger
