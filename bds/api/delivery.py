import os
from datetime import datetime
from math import pi, cos, sqrt
from flask_cors.decorator import cross_origin
from werkzeug.utils import secure_filename
from flask import (jsonify, request, current_app)
from app import csrf, mongo
from app.auth.models import User
from bds import bp_bds
from bds.models import Billing, Delivery, Messenger, Subscriber, Area, SubArea


@bp_bds.route('/api/confirm-deliver', methods=['POST'])
@csrf.exempt
def confirm_deliver():
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
@cross_origin()
def get_deliveries():
    query_by = request.args.get('query')

    deliveries_query = []

    # active_billing = Billing.query.filter_by(active=1).first()
    active_billing = Billing(data=mongo.db.bds_billings.find_one({'active': 1}))


    if active_billing is None:
        return jsonify({'deliveries': []})

    if not query_by == 'by_messenger':
        # deliveries = Delivery.query.filter_by(active=1).all()
        deliveries_query = list(mongo.db.bds_deliveries.find({'active': 1}))
    else:
        messenger_id = request.args.get('messenger_id')
        messenger: Messenger = Messenger.find_one_by_id(id=messenger_id)
        messenger_areas = [area['_id'] for area in messenger.areas]
        print("messenger_areas: ", messenger_areas)
        messenger_sub_areas_query = list(mongo.db.bds_sub_areas.find({'area_id': {'$in': messenger.areas}}))
        messenger_sub_areas = [sub_area['_id'] for sub_area in messenger_sub_areas_query]
        # query = db.session.query(Area.id).join(messenger_areas).filter_by(messenger_id=messenger.id)
        # _sub_areas_query = db.session.query(SubArea.id).join(Area).filter(SubArea.area_id.in_(query))

        deliveries_query = mongo.db.bds_deliveries.find({'sub_area_id'})
        # deliveries = db.session.query(Delivery).filter_by(
        #     active=1,
        #     billing_id=active_billing.id
        #     ).join(Subscriber).join(SubArea).filter(
        #         SubArea.id.in_(_sub_areas_query)
        #         ).all()

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
