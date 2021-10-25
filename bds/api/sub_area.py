from bson.objectid import ObjectId
from bds.globals import SUBSCRIBER_ROLE
from bds.views.delivery import deliver
from flask import (jsonify, request, abort)
from flask_cors import cross_origin
from sqlalchemy import or_
from sqlalchemy.sql.expression import column
from app import csrf, mongo
from app.auth.models import User
from bds import bp_bds
from bds.models import Delivery, Subscriber, Area, SubArea



@bp_bds.route('/api/sub-areas/<string:oid>/subscribers')
@cross_origin()
def get_sub_area_subscribers(oid):
    print("sub_area_id: ", oid)
    client_side = request.args.get('client_side', False)
    sub_area = SubArea.find_one_by_id(id=oid)

    if not sub_area:
        response = {
            'data': []
        }
        return jsonify(response)
    
    table_data = []

    if not client_side: # Serverside
        draw = request.args.get('draw')
        start, length = int(request.args.get('start')), int(request.args.get('length'))
        search_value = "%" + request.args.get("search[value]") + "%"
        column_order = request.args.get('column_order')
        billing_id = request.args.get('billing_id')

        if not sub_area:
            return jsonify({'data':[],'recordsTotal':0,'recordsFiltered':0,'draw':draw})

        # if search_value == "":
        #     query = Subscriber.query.filter_by(sub_area_id=sub_area.id)
        # else:
        #     query = Subscriber.query.filter_by(sub_area_id=sub_area.id)\
        #         .filter(or_(Subscriber.lname.like(search_value),Subscriber.contract_no.like(search_value)))
        print("START: ", start)
        print("LENGTH: ", length)

        print("SUBAREA: ", sub_area)
        query = list(mongo.db.auth_users.find({
            'role_id': SUBSCRIBER_ROLE.id,
            'sub_area_id': sub_area.id
        }).skip(start).limit(length))

        print("query: ",query)

        total_records = len(query)

        for data in query:
            subscriber = Subscriber(data=data)
            # delivery_query = Delivery.query.filter_by(
            #     billing_id=billing_id,subscriber_id=subscriber.id,active=1
            #     ).first()
            delivery: Delivery = Delivery(data=mongo.db.bds_deliveries.find_one({
                'billing_id': ObjectId(billing_id),
                'subscriber_id': subscriber.id,
                'active': 1
            }))

            status = ""
            print("delivery.status: ", delivery.status)
            if delivery.status is not None and delivery.status != '':
                status = delivery.status
            else:
                status = "NOT YET DELIVERED"

            if column_order == "inline":
                table_data.append([
                    str(subscriber.id),
                    subscriber.contract_no,
                    subscriber.fname,
                    subscriber.lname,
                    subscriber.sub_area.name if subscriber.sub_area else ''
                ])
            else:
                table_data.append([
                    str(subscriber.id),
                    subscriber.contract_no,
                    subscriber.fname + " " + subscriber.lname,
                    subscriber.address,
                    status,
                    ""
                ])

        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': table_data
        }

        print(table_data)

        return jsonify(response)

    # Clientside
    for subscriber in sub_area.subscribers:
        table_data.append([
            subscriber.id,
            subscriber.contract_number,
            subscriber.fname,
            subscriber.lname,
            subscriber.sub_area.name if subscriber.sub_area else ''
        ])

    response = {
        'data': table_data
    }

    return jsonify(response)