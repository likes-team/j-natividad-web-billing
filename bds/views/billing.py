from datetime import datetime
from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, jsonify
from flask.templating import render_template
from flask_login import  login_required, current_user
from flask_pymongo import DESCENDING
import pymongo
from app.admin.templating import admin_table, admin_edit
from bds import bp_bds
from bds.models import Billing
from bds.forms import BillingForm, BillingEditForm
from bds.functions import generate_number
from app import mongo



@bp_bds.route('/billings')
@login_required
def billings():
    fields = [
        "id", "active", "number", "name", "description", "date_from", 
        "date_to", "created_by", "created_at"]
    form = BillingForm()

    _billing_generated_number = ""

    # query = db.session.query(Billing).order_by(Billing.id.desc()).first()
    query_last_billing = list(mongo.db.bds_billings.find().sort('created_at', pymongo.DESCENDING).limit(1))

    if query_last_billing:
        _billing_generated_number = generate_number("BILL", query_last_billing[0]['billing_no'])
    else:
        _billing_generated_number = "BILL00000001"

    form.number.auto_generated = _billing_generated_number
    
    return render_template("bds/adminty_billing.html", billing_generated_number=_billing_generated_number)
    
    # return admin_table(Billing, fields=fields, form=form, create_url='bp_bds.create_billing',\
    #     edit_url="bp_bds.edit_billing", table_template="bds/adminty_billing.html",\
    #         view_modal_template="bds/bds_billing_view_modal.html", billing_generated_number=_billing_generated_number,
    #         table_data=[])


@bp_bds.route('/billings/new-generated-number', methods=['GET'])
def get_new_generated_number():
    try:
        generated_number = ""
        query_last_billing = list(mongo.db.bds_billings.find().sort('created_at', pymongo.DESCENDING).limit(1))

        if query_last_billing:
            generated_number = generate_number("BILL", query_last_billing[0]['billing_no'])
        else:
            generated_number = "BILL00000001"

        response = {
            'status': 'success',
            'data': {
                'new_generated_number': generated_number
            },
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 200


@bp_bds.route('/billings/dt', methods=['GET'])
def fetch_billings_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    table_data = []
    print("search_value", search_value)

    if search_value != '':
        query = Billing.search(
            search={"name": {"$regex": search_value}},
        )
        total_records = len(query)
    else:
        query = Billing.find_with_range(
            start=start,
            length=length
        )        
        total_records = len(Billing.find_all())

    filtered_records = len(query)

    print("START: ", start)
    print("DRAW: ", draw)
    print("LENGTH: ", length)
    print("filtered_records: ", filtered_records)
    print("total_records: ", total_records)

    billing: Billing
    for billing in query:
        table_data.append((
            str(billing.id),
            billing.active,
            billing.full_billing_no,
            billing.name,
            billing.description,
            billing.date_from,
            billing.date_to,
            billing.created_by,
            billing.created_at_local,
            ''
        ))
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)


@bp_bds.route('/billings/<string:billing_id>', methods=['GET'])
@login_required
def get_billing(billing_id):
    try:
        billing = Billing.find_one_by_id(id=billing_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(billing.id),
                'billing_no': billing.full_billing_no,
                'name': billing.name,
                'description': billing.description,
                'date_from': billing.date_from,
                'date_to': billing.date_to
            },
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 200


@bp_bds.route('/billings/create',methods=['POST'])
@login_required
def create_billing():
    form = request.form
    
    try:
        new = Billing()
        new.active = False
        new.full_billing_no = form.get('number')
        new.name = form.get('name')
        new.description = form.get('description')
        new.date_to = form.get('date_to')
        new.date_from = form.get('date_from')
        new.billing_no = new.count() + 1
        new.save()
        response = {
            'status': 'success',
            'data': new.toJson(),
            'message': "New billing added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/billings/<string:oid>/edit',methods=['POST'])
@login_required
def edit_billing(oid):
    form = request.form
    print(oid)
    try:
        mongo.db.bds_billings.update_one({
            "_id": ObjectId(oid)
        }, {"$set": {
            "name": form.get('name'),
            'description': form.get('description'),
            'date_from': form.get('date_from'),
            'date_to': form.get('date_to')
        }})
        
        response = {
            'status': 'success',
            'data': {},
            'message': "Billing updated Successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/billings/<string:billing_id>/set-active', methods=['POST'])
@login_required
def set_active(billing_id):
    status = request.json['status']
    try:
        with mongo.cx.start_session() as session:
            with session.start_transaction():
                mongo.db.bds_billings.update_many({
                    'active': True
                }, {"$set":{
                    'active': False
                }}, session=session)

                mongo.db.bds_billings.update_one({
                    '_id': ObjectId(billing_id)
                },{"$set":{
                    'active': status
                }}, session=session)
        response = jsonify({
            'result': True
        })
        return response
    except Exception:
        return jsonify({'result': False})
