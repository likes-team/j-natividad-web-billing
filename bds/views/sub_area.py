from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, jsonify
from flask_login import login_required
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
    # fields = [SubArea.id,SubArea.name, SubArea.description, SubArea.created_at, SubArea.updated_at]
    fields = ["id","name", "description", "created_at", "updated_at"]
    form = SubAreaForm()

    table_data = []

    query = SubArea.find_all()

    sub_area: SubArea
    for sub_area in query:
        table_data.append((
            str(sub_area.id),
            sub_area.name,
            sub_area.description,
            sub_area.created_at_local,
            sub_area.updated_at_local
        ))

    return admin_table(SubArea, fields=fields,form=form, create_modal=False, create_button=True,\
        edit_url="bp_bds.edit_sub_area", create_url="bp_bds.create_sub_area", table_data=table_data)


@bp_bds.route('/sub-areas/create', methods=['GET','POST'])
@login_required
def create_sub_area():
    form = SubAreaForm()

    if request.method == "GET":
        _subscribers = Subscriber.find_all_by_role_id(role_id=SUBSCRIBER_ROLE.id)
        _areas = Area.find_all()

        data = {
            'subscribers': _subscribers,
            'areas': _areas
        }

        return admin_render_template(SubArea, "bds/sub_area/bds_create_sub_area.html", 'bds', form=form,\
            data=data, modals=modals, title="Create sub area")

    # try:
    new = SubArea()
    new.name = form.name.data
    new.description = form.description.data
    new.area_id = form.area_id.data if form.area_id.data != '' else None
    with mongo.cx.start_session() as session:
        with session.start_transaction():
            subscribers_line = request.form.getlist('subscribers[]')
            print("subscribers_line: ",subscribers_line)
            if subscribers_line:
                for sub_id in subscribers_line:
                    mongo.db.auth_users.update_one({
                        "_id": ObjectId(sub_id)
                    },
                    {"$set": {
                        'sub_area_id': new.id,
                        'sub_area_name': new.name
                    }},session=session)

            new.save(session=session)

    flash("New sub area added successfully!", 'success')
    # except Exception as e:
    #     flash(str(e), 'error')

    return redirect(url_for('bp_bds.sub_areas'))


@bp_bds.route('/sub-areas/<string:oid>/edit', methods=['GET','POST'])
@login_required
def edit_sub_area(oid):
    ins = SubArea.query.get_or_404(oid)
    form = SubAreEditForm(obj=ins)

    if request.method == 'GET':

        return admin_edit(SubArea, form, 'bp_bds.edit_sub_area', oid, 'bp_bds.sub_areas', \
            modals=modals, scripts=scripts)

    try:
        ins.name = request.form.get('name')
        ins.description = request.form.get('description')
        ins.area_id = request.form.get('area_id') if not request.form.get('area_id') == '' else None
        
        subscribers_line = request.form.getlist('subscribers[]')
        ins.subscribers = []

        if subscribers_line:
            for sub_id in subscribers_line:
                subscriber = Subscriber.query.get_or_404(int(sub_id))
                ins.subscribers.append(subscriber)

        db.session.commit()
        flash("Sub area updated successfully!", 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    
    return redirect(url_for('bp_bds.sub_areas'))


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
