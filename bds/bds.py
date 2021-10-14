from app.core import CoreModule
from .models import (Billing, Delivery, Area, Subscriber, Messenger, SubArea, Municipality,\
    DeliveryMap)



class BDSModule(CoreModule):
    module_name = 'bds'
    module_icon = 'fa-map'
    module_link = 'bp_bds.subscribers'
    module_short_description = 'BDS'
    module_long_description = "Billing Delivery System"
    models = [
        Billing, Delivery, Area, Subscriber, Messenger, DeliveryMap
        ]
    no_admin_models =[SubArea, Municipality]
    version = '1.0'
    sidebar = {
        'Maps':[
            DeliveryMap
        ],
        'Transactions': [
            Billing,
            Delivery,
            Area,
            Subscriber,
            Messenger
        ]
    }