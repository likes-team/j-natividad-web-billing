from re import sub
from bson.objectid import ObjectId
from flask_login import login_required
from flask import jsonify
from app.admin.templating import admin_render_template
from bds import bp_bds
from bds.models import Area, Billing, Dashboard, Delivery, SubArea
from app import mongo



@bp_bds.route('/')
@bp_bds.route('/dashboard')
@login_required
def dashboard():
    areas = Area.find_all()
    billings = Billing.find_all()

    return admin_render_template(
        Dashboard, 
        'bds/dashboard.html', 
        'bds', 
        title="Dashboard",
        areas=areas,
        billings=billings
    )


# @bp_bds.route('/dashboard/areas/<string:area_id>/sub-areas')
# def get_dashboard_area_sub_areas(area_id):


@bp_bds.route('/dashboard/areas/<string:area_id>/billings/<string:billing_id>/data')
def get_dashboard_area_data(area_id, billing_id):
    sub_areas_query = SubArea.find_all_by_area_id(id=area_id)
    sub_areas = [sub_area for sub_area in sub_areas_query]
    sub_areas_names = [sub_area.name for sub_area in sub_areas_query]

    active_billing = Billing(data=mongo.db.bds_billings.find_one({'active': 1}))

    if active_billing is None:
        raise Exception("Likes Error: No active billing")

    deliveries_query = list(mongo.db.bds_deliveries.aggregate([
        {'$match': {
            'area_id': ObjectId(area_id),
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
            }}
    ]))

    datasets = [
        {
            'label': "Delivered",
            'data': [0 for _ in range(len(sub_areas))],
            'backgroundColor': 'rgb(75, 192, 192)'
        },
        {
            'label': "Pending",
            'data': [0 for _ in range(len(sub_areas))],
            'backgroundColor': 'rgb(255, 159, 64)'
        },
        {
            'label': "In-Progress",
            'data': [0 for _ in range(len(sub_areas))],
            'backgroundColor': 'rgb(255, 99, 132)'
        }
    ]

    for data in deliveries_query:
        delivery: Delivery = Delivery(data=data)

        try:
            sub_area_index = sub_areas_names.index(delivery.sub_area.name)

            print(delivery.status)
            if delivery.status == "DELIVERED":
                new_count = datasets[0]['data'][sub_area_index] + 1
                datasets[0]['data'][sub_area_index] = new_count
            elif delivery.status == "PENDING":
                new_count = datasets[1]['data'][sub_area_index] + 1
                datasets[1]['data'][sub_area_index] = new_count
            elif delivery.status == "IN-PROGRESS":
                new_count = datasets[2]['data'][sub_area_index] + 1
                datasets[2]['data'][sub_area_index] = new_count
                    
        except ValueError:
            print(delivery.sub_area.name)

            continue

    print(datasets)

    response = {
        'status': "success",
        'data': {
            'labels': sub_areas_names,
            'datasets': datasets
        },
        "message": ""
    }
    return jsonify(response), 200