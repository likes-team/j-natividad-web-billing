from datetime import datetime
from flask import redirect, url_for, request, current_app, flash
from flask.json import jsonify
from flask.templating import render_template
from flask_login import current_user, login_required
from app.admin.templating import admin_table, admin_edit
from bds import bp_bds
from bds.models import Area, Municipality
from bds.forms import MunicipalityForm, MunicipalityEditForm
from app import mongo
from bson.objectid import ObjectId



@bp_bds.route('/municipalities')
@login_required
def municipalities():
    return render_template("bds/adminty_municipalities.html")


@bp_bds.route('/municipalities/<string:municipality_id>', methods=['GET'])
@login_required
def get_municipality(municipality_id):
    try:
        muncipality = Municipality.find_one_by_id(id=municipality_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(muncipality.id),
                'name': muncipality.name,
                'description': muncipality.description,
            },
            'message': ""
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/municipalities/dt', methods=['GET'])
def fetch_municipalities_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    table_data = []
    print("search_value", search_value)

    if search_value != '':
        query = Municipality.search(
            search={"name": {"$regex": search_value}},
        )
        total_records = len(query)
    else:
        query = Municipality.find_with_range(
            start=start,
            length=length
        )        
        total_records = len(Municipality.find_all())

    filtered_records = len(query)

    print("START: ", start)
    print("DRAW: ", draw)
    print("LENGTH: ", length)
    print("filtered_records: ", filtered_records)
    print("total_records: ", total_records)

    municipality: Municipality
    for municipality in query:
        table_data.append((
            str(municipality.id),
            municipality.name,
            municipality.description,
            municipality.created_at_local,
            municipality.created_by,
            ''
        ))
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)


@bp_bds.route('/municipalities/create', methods=['POST'])
@login_required
def create_municipality():
    form = request.form
 
    try:
        new = Municipality()
        new.name = form.get('name')
        new.description = form.get('description')
        new.save()
        response = {
            'status': 'success',
            'data': new.toJson(),
            'message': "New municipality added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_bds.route('/municipalities/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_municipality(oid):
    form = request.form
    
    try:
        print(form)
        mongo.db.bds_municipalities.update_one({
            "_id": ObjectId(oid)
        }, {"$set": {
            "name": form.get('name'),
            'description': form.get('description'),
        }})
        
        response = {
            'status': 'success',
            'data': {},
            'message': "Municipality updated Successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 200
