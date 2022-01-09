from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, jsonify, render_template
from flask_login import login_required
import pymongo
from sqlalchemy.sql.expression import table
from app.admin.templating import admin_edit, admin_render_template
from app.admin.templating import admin_table
from bds import bp_bds
from bds.globals import SUBSCRIBER_ROLE
from bds.models import SubArea, Subscriber, Area
from bds.forms import SubAreEditForm, SubAreaForm
from app import mongo



modals = [
    "bds/sub_area/bds_add_subscriber_modal.html",
]


@bp_bds.route('/sub-areas')
@login_required
def sub_areas():
    areas = Area.find_all()
    return render_template("bds/adminty_sub_areas.html", areas=areas)


@bp_bds.route('/sub-areas/<string:sub_area_id>', methods=['GET'])
@login_required
def get_sub_area(sub_area_id):
    try:
        sub_area = SubArea.find_one_by_id(id=sub_area_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(sub_area.id),
                'name': sub_area.name,
                'description': sub_area.description,
                'area_id': str(sub_area.area_id)
            },
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/sub-areas/dt', methods=['GET'])
def fetch_sub_areas_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    table_data = []

    if search_value != '':
        query = SubArea.search(
            search={"name": {"$regex": search_value}},
        )
        total_records = len(query)
    else:
        query = list(mongo.db.bds_sub_areas.aggregate([
            {"$lookup": {"from": "bds_areas", "localField": "area_id",
                         "foreignField": "_id", 'as': "area"}},
            {"$skip": start},
            {"$limit": length},
            {"$sort": {
                'created_at': pymongo.DESCENDING
            }}
        ]))
        total_records = len(SubArea.find_all())

    filtered_records = len(query)

    print("START: ", start)
    print("DRAW: ", draw)
    print("LENGTH: ", length)
    print("filtered_records: ", filtered_records)
    print("total_records: ", total_records)

    for data in query:
        sub_area: SubArea = SubArea(data=data)
        table_data.append((
            str(sub_area.id),
            sub_area.name,
            sub_area.description,
            sub_area.area.name if sub_area.area is not None else '',
            sub_area.created_at_local,
            sub_area.created_by,
            ''
        ))
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)


@bp_bds.route('/sub-areas/create', methods=['GET','POST'])
@login_required
def create_sub_area():
    form = request.form
 
    try:
        new = SubArea()
        new.name = form.get('name', '')
        new.description = form.get('description', '')
        new.area_id = ObjectId(form.get('area')) if form.get('area') != '' else None
        new.save()

        response = {
            'status': 'success',
            'data': new.toJson(),
            'message': "New sub area added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        print(err)
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500    


@bp_bds.route('/sub-areas/<string:oid>/edit', methods=['GET','POST'])
@login_required
def edit_sub_area(oid):
    form = request.form
    
    try:
        mongo.db.bds_sub_areas.update_one({
            "_id": ObjectId(oid)
        }, {"$set": {
            "name": form.get('name'),
            'description': form.get('description'),
            'area_id': ObjectId(form.get('area')) if form.get('area') != '' else None
        }})
        
        response = {
            'status': 'success',
            'data': {},
            'message': "Sub Area updated Successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/api/dtbl/subscribers')
def get_dtbl_subscribers():
    sub_area_id = request.args.get('sub_area_id')
    # query0 = db.session.query(Subscriber.id).filter_by(sub_area_id=_sub_area_id)
    
    # subscribers = db.session.query(Subscriber).filter(~Subscriber.id.in_(query0)).all()

    query = list(mongo.db.auth_users.aggregate([
        {"$match": {"role_id": SUBSCRIBER_ROLE.id}},
        {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                        "foreignField": "_id", 'as': "role"}},
        {"$lookup": {"from": "bds_sub_areas", "localField": "sub_area_id",
                        "foreignField": "_id", 'as': "sub_area"}}
    ]))

    table_data = []

    for data in query:
        subscriber: Subscriber = Subscriber(data=data)

        table_data.append([
            str(subscriber.id),
            subscriber.contract_no,
            subscriber.fname,
            subscriber.lname,
            subscriber.sub_area_name
        ])

    print("table_data: ", table_data)
    
    response = {
        'data': table_data
    }

    return jsonify(response)
