from re import sub
from bson.objectid import ObjectId
from bds.views.billing import billings
from flask import (json, url_for, request,jsonify, abort)
from flask_login import login_required
from flask_cors import cross_origin
from app.admin.templating import admin_render_template
from bds import bp_bds
from bds.models import Billing, Delivery, SubArea, Municipality, Subscriber, Area
from app import mongo



modals = [
    'bds/delivery/bds_details_modal.html',
    'bds/delivery/bds_search_billing_modal.html'
]


@bp_bds.route('/deliveries',methods=['GET'])
@login_required
def deliveries():
    
    return admin_render_template(Delivery, 'bds/delivery/bds_delivery.html', 'bds', title="Delivery",\
        modals=modals)


@bp_bds.route('/subscribers/<string:subscriber_id>/delivery', methods=['GET'])
@cross_origin()
def get_delivery(subscriber_id):
    billing_id = request.args.get('billing_id')

    deliveries_query = list(mongo.db.bds_deliveries.aggregate([
        {'$match': {
            'subscriber_id': ObjectId(subscriber_id), 
            'active': 1,
            'billing_id': ObjectId(billing_id)
        }},
        {'$lookup': {
            'from': "auth_users", 
            "localField": "subscriber_id", 
            "foreignField": "_id",
            'as': 'subscriber'
            }},
        {'$lookup': {
            'from': "bds_areas", 
            "localField": "area_id", 
            "foreignField": "_id",
            'as': 'area'
            }},
        {'$lookup': {
            'from': "bds_sub_areas", 
            "localField": "sub_area_id", 
            "foreignField": "_id",
            'as': 'sub_area'
            }},
        {'$lookup': {
            'from': "auth_users", 
            "localField": "messenger_id", 
            "foreignField": "_id",
            'as': 'messenger'
            }}
    ]))

    delivery = Delivery(data=deliveries_query[0])

    if delivery is None:
        return jsonify({
            'id': False
        })

    accuracy = 0
    if delivery.accuracy:
        accuracy = round(float(delivery.accuracy), 2)

    # WE SERIALIZE AND RETURN LIST INSTEAD OF MODELS

    print(delivery.image_path)
    return jsonify({
        'id': str(delivery.id),
        'subscriber_id': str(delivery.subscriber.id),
        'subscriber_fname': delivery.subscriber.fname,
        'subscriber_lname': delivery.subscriber.lname,
        'subscriber_address': delivery.subscriber.address,
        'delivery_date': delivery.delivery_date,
        'status': delivery.status,
        'longitude': delivery.delivery_longitude,
        'latitude': delivery.delivery_latitude,
        'accuracy': accuracy,
        'date_mobile_delivery': delivery.date_mobile_delivery,
        'image_path': url_for('bp_bds.static', filename=delivery.image_path),
        'messenger_fname': delivery.messenger.fname,
        'messenger_lname': delivery.messenger.lname
    })


@bp_bds.route('/api/delivery/<int:delivery_id>/confirm', methods=['POST'])
@cross_origin()
def confirm_delivery_id(delivery_id):

    delivery = Delivery.query.get_or_404(delivery_id)

    if delivery is None:
        abort(404)


    delivery.status = "DELIVERED"
    db.session.commit()

    return jsonify({
        'result':True, 
        'delivery': {'id': delivery.id,}
        })


@bp_bds.route('/api/subscriber/delivery/reset', methods=["POST"])
@cross_origin()
def reset():
    _subscriber_contract_no = request.json['subscriber_contract_no']
    _sub_area_name = request.json['sub_area_name']
    
    sub_area = SubArea.query.filter_by(name=_sub_area_name).first()

    delivery = Delivery.query.filter_by(active=1).join(Subscriber)\
        .filter_by(contract_number=_subscriber_contract_no,sub_area_id=sub_area.id).first()

    if delivery is None:
        return jsonify({'result':False})

    delivery.active = 0
    db.session.commit()
    
    return jsonify({'result':True})


@bp_bds.route('/api/subscribers/<string:subscriber_id>/deliveries/deliver', methods=['POST'])
@cross_origin()
def deliver(subscriber_id):
    billing_id = request.json['billing_id']

    subscriber = Subscriber.find_one_by_id(id=subscriber_id)
    sub_area = SubArea.find_one_by_id(id=subscriber.sub_area_id)
    delivery_query = mongo.db.bds_deliveries.find_one({
        'billing_id': ObjectId(billing_id),
        'subscriber_id': subscriber.id,
        'active': 1
    })

    if not delivery_query:
        new_delivery: Delivery = Delivery()
        new_delivery.billing_id = ObjectId(billing_id)
        new_delivery.subscriber_id = subscriber.id
        new_delivery.sub_area_id = subscriber.sub_area_id
        new_delivery.area_id = ObjectId(sub_area.area_id)
        new_delivery.status = "IN-PROGRESS"
        new_delivery.active = 1
        new_delivery.save()

    response = jsonify({'result':True})

    return response


@bp_bds.route('/api/deliveries/reset-all', methods=['POST'])
@cross_origin()
def reset_all():
    _sub_area_name = request.json['sub_area_name']
    sub_area = SubArea.query.filter_by(name=_sub_area_name).first()

    if sub_area is None:
        abort(404)
    
    for subscriber in sub_area.subscribers:
        delivery = Delivery.query.filter_by(subscriber_id=subscriber.id,active=1).first()

        if delivery:
            delivery.active = 0
            db.session.commit()
    
    return jsonify({'result':True})


@bp_bds.route('/api/deliveries/deliver-all', methods=['POST'])
@cross_origin()
def deliver_all():
    billing_id = request.json['billing_id']
    sub_area_name = request.json['sub_area_name']
    sub_area = SubArea.query.filter_by(name=sub_area_name).first()

    if not sub_area:
        abort(404)

    for subscriber in sub_area.subscribers:
        delivery = Delivery.query.filter_by(
            subscriber_id=subscriber.id, billing_id=billing_id, active=1
            ).first()
        
        if not delivery:
            new = Delivery(subscriber.id,"IN-PROGRESS")
            new.billing_id = billing_id

            db.session.add(new)
            db.session.commit()

    response = jsonify({'result': True})

    return response


@bp_bds.route('/api/get-municipality-areas', methods=["GET"])
@cross_origin()
def get_municipality_areas():
    municipality_name = request.args.get('municipality_name')
    municipality = Municipality.find_one_by_name(name=municipality_name)

    if municipality is None:
        return jsonify({'result': False})

    areas = Area.find_all_by_municipality_id(municipality.id)

    data = []
    for area in areas:
        data.append({
            'id': str(area.id),
            'name': area.name,
            'description': area.description
        })
    return jsonify({'result': data})


@bp_bds.route('/api/get-area-sub-areas', methods=["GET"])
@cross_origin()
def get_area_sub_areas():
    area_name = request.args.get('area_name')
    area = Area.find_one_by_name(name=area_name)

    if area is None:
        return jsonify(({'result': False}))
    
    data = []

    sub_areas = SubArea.find_all_by_area_id(id=area.id)
    sub_area: SubArea
    for sub_area in sub_areas:
        data.append({
            'id': str(sub_area.id),
            'name': sub_area.name,
            'description': sub_area.description
        })
    return jsonify({'result': data})


@bp_bds.route('/api/municipalities', methods=["GET"])
@cross_origin()
def get_municipalities():
    municipalities = Municipality.find_all()

    _data = []
    municipality: Municipality
    for municipality in municipalities:
        _data.append({
            'id': str(municipality.id),
            'name': municipality.name,
            'description': municipality.description
        })

    response = jsonify(_data)
    return response, 200


@bp_bds.route('/api/dtbl/billings', methods=['GET'])
@cross_origin()
def get_dtbl_billings():

    billings = Billing.find_all()

    _data = []

    billing: Billing
    for billing in billings:
        _data.append([
            str(billing.id),
            billing.active,
            billing.full_billing_no,
            billing.name,
            billing.date_from,
            billing.date_to,
        ])

    response = {
        'data': _data
        }

    print(response)

    return jsonify(response)
