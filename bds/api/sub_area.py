from bds.views.delivery import deliver
from flask import (jsonify, request, abort)
from flask_cors import cross_origin
from sqlalchemy import or_
from sqlalchemy.sql.expression import column
from app import csrf
from app.auth.models import User
from bds import bp_bds
from bds.models import Delivery, Subscriber, Area, SubArea



@bp_bds.route('/api/sub-areas/<int:oid>/subscribers')
@cross_origin()
def get_sub_area_subscribers(oid):
    client_side = request.args.get('client_side', False)
    sub_area = SubArea.query.get(oid)
    
    data = []

    if not client_side: # Serverside

        draw = request.args.get('draw')
        start, length = request.args.get('start'), request.args.get('length')
        search_value = "%" + request.args.get("search[value]") + "%"
        column_order = request.args.get('column_order')
        billing_id = request.args.get('billing_id')

        if not sub_area:
            return jsonify({'data':[],'recordsTotal':0,'recordsFiltered':0,'draw':draw})

        if search_value == "":
            query = Subscriber.query.filter_by(sub_area_id=sub_area.id)
        else:
            query = Subscriber.query.filter_by(sub_area_id=sub_area.id)\
                .filter(or_(Subscriber.lname.like(search_value),Subscriber.contract_no.like(search_value)))

        subscribers = query.limit(length).offset(start).all()

        total_records = query.count()

        for subscriber in subscribers:

            delivery = Delivery.query.filter_by(
                billing_id=billing_id,subscriber_id=subscriber.id,active=1
                ).first()

            _status = ""

            if delivery:
                _status = delivery.status
            else:
                _status = "NOT YET DELIVERED"

            if column_order == "inline":
                data.append([
                    subscriber.id,
                    subscriber.contract_number,
                    subscriber.fname,
                    subscriber.lname,
                    subscriber.sub_area.name if subscriber.sub_area else ''
                ])
            else:
                data.append([
                    subscriber.id,
                    subscriber.contract_number,
                    subscriber.fname + " " + subscriber.lname,
                    subscriber.address,
                    _status,
                    ""
                ])

        response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': total_records,
            'data': data
        }

        print(data)

        return jsonify(response)

    # Clientside
    for subscriber in sub_area.subscribers:
        data.append([
            subscriber.id,
            subscriber.contract_number,
            subscriber.fname,
            subscriber.lname,
            subscriber.sub_area.name if subscriber.sub_area else ''
        ])

    response = {
        'data': data
    }

    return jsonify(response)