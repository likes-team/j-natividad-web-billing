from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, render_template, jsonify
from flask_login import login_required
from sqlalchemy.sql.expression import table
from app.admin.templating import admin_render_template
from app.admin.templating import admin_table
from app.auth.models import User
from bds import bp_bds
from bds.globals import MESSENGER_ROLE
from bds.models import Area, Messenger, Municipality
from bds.forms import AreaEditForm, AreaForm
from app import mongo
from bds.views.municipality import municipalities


modals = [
    "bds/area/bds_add_messenger_modal.html"
]


@bp_bds.route('/areas')
@login_required
def areas():
    municipalities = Municipality.find_all()
    return render_template("bds/adminty_areas.html", municipalities=municipalities)


@bp_bds.route('/areas/<string:area_id>', methods=['GET'])
@login_required
def get_area(area_id):
    try:
        area = Area.find_one_by_id(id=area_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(area.id),
                'name': area.name,
                'description': area.description,
                'municipality_id': str(area.municipality_id)
            },
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        print(err)
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/areas/dt', methods=['GET'])
def fetch_areas_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    table_data = []

    if search_value != '':
        query = Area.search(
            search={"name": {"$regex": search_value}},
        )
        total_records = len(query)
    else:
        query = list(mongo.db.bds_areas.aggregate([
            {"$lookup": {"from": "bds_municipalities", "localField": "municipality_id",
                         "foreignField": "_id", 'as': "municipality"}},
            {"$skip": start},
            {"$limit": length}
        ]))
        total_records = len(Area.find_all())

    filtered_records = len(query)

    print("START: ", start)
    print("DRAW: ", draw)
    print("LENGTH: ", length)
    print("filtered_records: ", filtered_records)
    print("total_records: ", total_records)

    for data in query:
        area: Area = Area(data=data)
        table_data.append((
            str(area.id),
            area.name,
            area.description,
            area.municipality.name if area.municipality is not None else '',
            area.created_at_local,
            area.created_by,
            ''
        ))
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)


@bp_bds.route('/areas/create', methods=["GET","POST"])
@login_required
def create_area():
    form = request.form
 
    try:
        new = Area()
        new.name = form.get('name', '')
        new.description = form.get('description', '')
        new.municipality_id = ObjectId(form.get('municipality')) if form.get('municipality') != '' else None
        new.save()

        response = {
            'status': 'success',
            'data': new.toJson(),
            'message': "New area added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        print(err)
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/areas/<string:oid>/edit', methods=['GET','POST'])
@login_required
def edit_area(oid):
    form = request.form
    
    try:
        mongo.db.bds_areas.update_one({
            "_id": ObjectId(oid)
        }, {"$set": {
            "name": form.get('name'),
            'description': form.get('description'),
            'municipality_id': ObjectId(form.get('municipality')) if form.get('municipality') != '' else None
        }})
        
        response = {
            'status': 'success',
            'data': {},
            'message': "Area updated Successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500
