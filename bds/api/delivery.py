import os
import json
from datetime import datetime
from math import pi, cos, sqrt
from werkzeug.utils import secure_filename
from flask import (jsonify, request, current_app)
# from flask_cors import cross_origin
from app import db, csrf
from app.auth.models import User
from bds import bp_bds
from bds.models import Billing, Delivery, Subscriber, Area, SubArea


@bp_bds.route('/api/confirm-deliver', methods=['POST'])
@csrf.exempt
def confirm_deliver():

    # FETCH DATA
    # data = json.loads(request.form['data'])
    # print(data)
    print(request.form)

    longitude = request.form['longitude']
    latitude = request.form['latitude']
    accuracy = request.form['accuracy']
    messenger_id = request.form['messenger_id']
    subscriber_id = request.form['subscriber_id']
    date_mobile_delivery = request.form['date_mobile_delivery']

    active_billing = Billing.query.filter_by(active=1).first()

    delivery = Delivery.query.filter_by(
        subscriber_id=subscriber_id,
        status="IN-PROGRESS",
        active=1,
        billing_id=active_billing.id
        ).first()
    
    print(date_mobile_delivery)

    date = datetime.strptime(str(date_mobile_delivery), '%Y-%m-%d %H:%M:%S')

    if delivery is None:
        return jsonify({'result': True})
    
    if delivery.subscriber.latitude is not None:
        if _isCoordsNear(longitude, latitude, delivery.subscriber, .1):
            delivery.status = "DELIVERED"
            print("DELIVERED", delivery.id)
        else:
            delivery.status = "PENDING"
            print("PENDING", delivery.id)
    else:
        subscriber = Subscriber.query.get_or_404(subscriber_id)
        messenger = User.query.get(messenger_id)

        subscriber.latitude = latitude
        subscriber.longitude = longitude
        subscriber.accuracy = accuracy
        subscriber.updated_by = messenger.fname + " " + messenger.lname
        subscriber.updated_at = datetime.now()

        delivery.status = "DELIVERED"
        print("DELIVERED", delivery.id)

    img_file = request.files['file']
    
    if img_file is None:
        print("Image file is none!")
        return jsonify({'result': False})

    filename = secure_filename(img_file.filename)

    _img_path = os.path.join(current_app.config['UPLOAD_IMAGES_FOLDER'], filename)
    
    img_file.save(_img_path)
    print("IMAGE SAVED", subscriber_id)
    delivery.image_path = "img/uploads/" + filename
            
    delivery.messenger_id = messenger_id
    delivery.delivery_longitude = longitude
    delivery.delivery_latitude = latitude
    delivery.accuracy = accuracy
    delivery.date_mobile_delivery = date
    delivery.date_delivered = datetime.now()
    db.session.commit()
    print("Database updated", delivery.id)

    return jsonify({
        'result':True, 
        'delivery': {
            'id': delivery.id,
            'status': delivery.status
            }
        })


@bp_bds.route('/api/deliveries', methods=['GET'])
@csrf.exempt
def get_deliveries():
    from app.auth.models import messenger_areas

    _query = request.args.get('query')

    deliveries: Delivery

    active_billing = Billing.query.filter_by(active=1).first()

    if active_billing is None:
        return jsonify({'deliveries': []})

    if not _query == 'by_messenger':
        deliveries = Delivery.query.filter_by(active=1).all()
        
    else:
        _messenger_id = request.args.get('messenger_id')
        messenger = User.query.get_or_404(_messenger_id)

        query = db.session.query(Area.id).join(messenger_areas).filter_by(messenger_id=messenger.id)
        
        _sub_areas_query = db.session.query(SubArea.id).join(Area).filter(SubArea.area_id.in_(query))
        
        deliveries = db.session.query(Delivery).filter_by(
            active=1,
            billing_id=active_billing.id
            ).join(Subscriber).join(SubArea).filter(
                SubArea.id.in_(_sub_areas_query)
                ).all()

    data = []
    for delivery in deliveries:

        data.append({
            'id': delivery.id,
            'subscriber_id': delivery.subscriber.id,
            'subscriber_fname': delivery.subscriber.fname,
            'subscriber_lname': delivery.subscriber.lname,
            'subscriber_address': delivery.subscriber.address,
            'subscriber_email': delivery.subscriber.email,
            'delivery_date': delivery.delivery_date,
            'status': delivery.status,
            'longitude': delivery.subscriber.longitude,
            'latitude': delivery.subscriber.latitude,
            'area_id': delivery.subscriber.sub_area.area.id,
            'area_name': delivery.subscriber.sub_area.area.name,
            'sub_area_id': delivery.subscriber.sub_area.id,
            'sub_area_name': delivery.subscriber.sub_area.name,
        })
    # WE SERIALIZE AND RETURN LIST INSTEAD OF MODELS 
    return jsonify({'deliveries': data})


def _isCoordsNear(checkPointLng, checkPointLat, centerPoint, km):
    if checkPointLat is None or checkPointLng is None:
        return False
    
    if centerPoint.latitude in ["", None] or centerPoint.longitude in ["", None]:
        return False

    ky = 40000 / 360
    kx = cos(pi * float(centerPoint.latitude) / 180.0) * ky
    dx = abs(float(centerPoint.longitude) - float(checkPointLng)) * kx
    dy = abs(float(centerPoint.latitude) - float(checkPointLat)) * ky
    print("_isCoordsNear Result:", sqrt(dx * dx + dy * dy) <= km)
    return sqrt(dx * dx + dy * dy) <= km
