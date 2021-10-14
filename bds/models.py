from app import db
from app.admin.models import Admin
from app.core.models import Base
from datetime import datetime


class Billing(Base, Admin):
    __tablename__ = 'bds_billings'
    __amname__ = 'billing'
    __amdescription__ = 'Billings'
    __amicon__ = 'pe-7s-cash'
    __view_url__ = 'bp_bds.billings'

    number = db.StringField()
    name = db.StringField()
    description = db.StringField()
    # deliveries = db.relationship('Delivery', cascade='all,delete', backref="billing")
    date_from = db.DateTimeField()
    date_to = db.DateTimeField()


class Subscriber(Base, Admin):
    meta = {
        'collection': 'bds_subscribers',
        'strict': False
    }
    
    __tablename__ = 'bds_subscribers'
    __amname__ = 'subscriber'
    __amdescription__ = 'Subscribers'
    __amicon__ = 'pe-7s-users'
    __view_url__ = 'bp_bds.subscribers'

    """ COLUMNS """
    fname = db.StringField()
    mname = db.StringField()
    lname = db.StringField()
    email = db.EmailField()
    contract_no = db.StringField()
    address = db.StringField()
    phone_number = db.StringField()
    longitude = db.DecimalField()
    latitude = db.DecimalField()
    # deliveries = db.relationship('Delivery', cascade='all,delete', backref="subscriber",order_by="desc(Delivery.delivery_date)")
    
    sub_area_id = db.ReferenceField('SubArea')

    @property
    def url(self):
        return "bp_bds.subscribers"


class Delivery(Base, Admin):
    __tablename__ = 'bds_delivery'
    __amname__ = 'delivery'
    __amdescription__ = 'Deliveries'
    __amicon__ = 'pe-7s-paper-plane'
    __view_url__ = 'bp_bds.deliveries'
    
    """ COLUMNS """
    billing_id = db.ReferenceField('Billing')
    subscriber_id = db.ReferenceField('Subscriber')
    messenger_id = db.ReferenceField("User")
    delivery_date = db.DateTimeField()
    date_delivered = db.DateTimeField()
    date_mobile_delivery = db.DateTimeField()
    status = db.StringField()
    image_path = db.StringField()
    accuracy = db.DecimalField()
    delivery_longitude = db.DecimalField()
    delivery_latitude = db.DecimalField()

    def __init__(self, subscriber_id, status):
        super(Delivery, self).__init__()
        self.subscriber_id = subscriber_id
        self.status = status


class Area(Base, Admin):
    meta = {
        'collection': 'bds_areas',
        'strict': False
    }
    __tablename__ = 'bds_areas'
    __amname__ = 'area'
    __amdescription__ = 'Locations'
    __amicon__ = 'pe-7s-flag'
    __amfunctions__ = [
        ("Sub Areas", "bp_bds.sub_areas", 'sub_area'),
        ("Areas", "bp_bds.areas", 'area'),
        ("Municipalities", "bp_bds.municipalities", 'municipality'),
        ]

    """ COLUMNS """
    name = db.StringField()
    description = db.StringField()
    municipality_id = db.ReferenceField('Municipality')


class SubArea(Base, Admin):
    meta = {
        'collection': 'bds_sub_areas',
        'strict': False
    }

    __tablename__ = 'bds_sub_areas'
    __amname__ = 'sub_area'
    __amdescription__ = 'Sub Areas'
    __amicon__ = 'pe-7s-flag'
    __parent_model__ = 'area'
    #__list_view_url__ = 'bp_bds.areas'

    """ COLUMNS """
    name = db.StringField()
    description = db.StringField()
    area_id = db.ReferenceField('Area')


class Messenger(db.Document, Admin):
    __abstract__ = True
    __tablename__ = 'auth_user'
    __amname__ = 'user'
    __amdescription__ = 'Messengers'
    __amicon__ = 'pe-7s-car'
    __view_url__ = 'bp_bds.messengers'


class Municipality(Base, Admin):
    __tablename__ = 'bds_municipality'
    __amname__ = 'municipality'
    __amdescription__ = 'Municipalities'
    __amicon__ = 'pe-7s-flag'
    __parent_model__ = 'area'

    name = db.StringField()
    description = db.StringField()


class DeliveryMap(Admin):
    __amname__ = 'delivery_map'
    __amdescription__ = 'Delivery Map'
    __amicon__ = 'pe-7s-map-2'
    __view_url__ = 'bp_bds.delivery_map'
