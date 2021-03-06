from datetime import datetime
import pymongo
import decimal
from bson.objectid import ObjectId
from flask import (jsonify, request, abort)
from app import csrf, mongo
from app.auth.models import User
from bds import bp_bds
from bds.globals import SUBSCRIBER_ROLE
from bds.models import Delivery, Messenger, Subscriber, Area, SubArea


@bp_bds.route('/api/subscribers', methods=['GET'])
@csrf.exempt
def get_subscribers():
    from app.auth.models import messenger_areas

    query = request.args.get('query','all')
    _list = []

    subscribers: Subscriber

    if query == "by_messenger":
        _messenger_id = request.args.get('messenger_id')
        messenger = User.query.get_or_404(_messenger_id)
        query = db.session.query(Area.id).join(messenger_areas).filter_by(messenger_id=messenger.id)
        _sub_areas_query = db.session.query(SubArea.id).join(Area).filter(SubArea.area_id.in_(query))
        subscribers = db.session.query(Subscriber).join(SubArea).filter(SubArea.id.in_(_sub_areas_query)).all()
    else:
        subscribers = Subscriber.query.all()

    for subscriber in subscribers:
        _delivery = Delivery.query.filter_by(subscriber_id=subscriber.id).first()
        _status = ""
        if _delivery:
            _status = _delivery.status

        _list.append({
            'id': subscriber.id,
            'fname': subscriber.fname,
            'lname': subscriber.lname,
            'address': subscriber.address,
            'latitude': subscriber.latitude,
            'longitude': subscriber.longitude,
            'status': _status
        })
        
    return jsonify({'subscribers': _list})


@bp_bds.route('/api/subscriber/update-location',methods=["POST"])
@csrf.exempt
def update_location():
    longitude = request.json['longitude']
    latitude = request.json['latitude']
    accuracy = request.json['accuracy']
    messenger_id = request.json['messenger_id']
    subscriber_id = request.json['subscriber_id']

    subscriber = Subscriber.find_one_by_id(id=subscriber_id)
    messenger = Messenger.find_one_by_id(id=messenger_id)

    subscriber.latitude = latitude
    subscriber.longitude = longitude
    subscriber.accuracy = accuracy
    subscriber.updated_by = messenger.fname + " " + messenger.lname

    mongo.db.auth_users.update_one({
        '_id': subscriber.id
    }, {'$set': {
        'latitude': subscriber.latitude,
        'longitude': subscriber.longitude,
        'accuracy': subscriber.accuracy,
        'updated_by': subscriber.updated_by,
        'updated_at': datetime.utcnow()
    }})

    return jsonify({'result': True})


@bp_bds.route('/api/subscribers/<string:subscriber_id>', methods=['GET'])
@csrf.exempt
def get_subscriber(subscriber_id):
    query = list(mongo.db.auth_users.aggregate([
        {"$match": {
            "_id": ObjectId(subscriber_id)
        }},
        {"$lookup": {"from": "bds_sub_areas", "localField": "sub_area_id",
                        "foreignField": "_id", 'as': "sub_area"}},
        {"$limit": 1}
    ]))
    
    if len(query) < 1:
        abort(404)

    # delivery = Delivery.query.filter_by(subscriber_id=subscriber.id,active=1).first()

    # _status = ""

    # if delivery:
    #     _status = delivery.status

    subscriber: Subscriber = Subscriber(data=query[0])

    data = {
        'id': str(subscriber.id),
        'fname': subscriber.fname,
        'lname': subscriber.lname,
        'address': subscriber.address,
        'latitude': subscriber.latitude,
        'longitude': subscriber.longitude,
        'email': subscriber.email,
        'status': "",
        'contract_no': subscriber.contract_no,
        'sub_area': subscriber.sub_area.name,
    }
    
    response = {
        'status': 'success',
        'data': data,
    }
    
    return jsonify(response)
