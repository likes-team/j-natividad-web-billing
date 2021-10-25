from datetime import datetime
from flask import (jsonify, request, abort)
from app import csrf
from app.auth.models import User
from bds import bp_bds
from bds.models import Delivery, Subscriber, Area, SubArea


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

    subscriber = Subscriber.query.get_or_404(subscriber_id)
    messenger = User.query.get(messenger_id)

    subscriber.latitude = latitude
    subscriber.longitude = longitude
    subscriber.accuracy = accuracy
    subscriber.updated_by = messenger.fname + " " + messenger.lname
    subscriber.updated_at = datetime.now()
    db.session.commit()

    return jsonify({'result': True})


@bp_bds.route('/api/subscribers/<int:subscriber_id>', methods=['GET'])
@csrf.exempt
def get_subscriber(subscriber_id):
    subscriber = Subscriber.query.get_or_404(subscriber_id)

    if subscriber is None:
        abort(404)

    delivery = Delivery.query.filter_by(subscriber_id=subscriber.id,active=1).first()

    _status = ""

    if delivery:
        _status = delivery.status

    res = {
        'id': subscriber.id,
        'fname': subscriber.fname,
        'lname': subscriber.lname,
        'address': subscriber.address,
        'latitude': subscriber.latitude,
        'longitude': subscriber.longitude,
        'email': subscriber.email,
        'status': _status
    }

    return jsonify(res)
