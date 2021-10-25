from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, render_template
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


modals = [
    "bds/area/bds_add_messenger_modal.html"
]


@bp_bds.route('/areas')
@login_required
def areas():
    models = [Area, Municipality]
    fields = ["id","name", "description", "munipacility", "created_at", "updated_at"]
    form = AreaForm()

    table_data = []

    query = Area.find_all()

    area: Area
    for area in query:
        table_data.append((
            str(area.id),
            area.name,
            area.description,
            "",
            area.created_at_local,
            area.updated_at_local
        ))

    return admin_table(*models, fields=fields,form=form, create_url='bp_bds.create_area',\
        create_button=True, edit_url="bp_bds.edit_area", create_modal=False, table_data=table_data)


@bp_bds.route('/areas/create', methods=["GET","POST"])
@login_required
def create_area():
    if request.method == "GET":
        messengers = User.find_all_by_role_id(role_id=MESSENGER_ROLE.id)
        # _municipalities = Municipality.query.all()

        data = {
            'messengers': messengers,
            'municipalities': []
        }

        return admin_render_template(Area, "bds/area/bds_create_area.html", 'bds', title="Create area",\
            data=data, modals=modals)

    # try:
    new = Area()
    new.name = request.form.get('name', '')
    new.description = request.form.get('description', '')
    new.municipality_id = request.form.get('municipality_id') if request.form.get('municipality_id') != '' else None

    messengers_line = request.form.getlist('messengers[]')

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            if messengers_line:
                for mes_id in messengers_line:
                    mongo.db.auth_users.update_one({
                        '_id': ObjectId(mes_id)
                    },
                    {"$push":{
                        'areas': new.toJson()
                    }
                    }, session=session)
            new.save(session=session)
    flash('New Area added successfully!','success')
    # except Exception as exc:
    #     flash(str(exc), 'error')

    return redirect(url_for('bp_bds.areas'))


@bp_bds.route('/areas/<string:oid>/edit', methods=['GET','POST'])
@login_required
def edit_area(oid):
    ins = Area.find_one_by_id(id=oid)
    form = AreaEditForm(obj=ins)
    if request.method == 'GET':
        area_messengers_query = list(mongo.db.auth_users.find({
            'areas._id': {'$in': [ins.id]}
        }))
        ins.messengers = [Messenger(data=data) for data in area_messengers_query]
        
        messengers_query = list(mongo.db.auth_users.find({
            'role_id' : MESSENGER_ROLE.id,
            'areas._id': {'$nin': [ins.id]}
        }))
        messengers = [Messenger(data=data) for data in messengers_query]
        print("messengers: ", messengers)
        
        # query = db.session.query(User.id).join(messenger_areas).filter_by(area_id=oid)
        # _messengers = db.session.query(User).filter(~User.id.in_(query)).filter_by(role_id=2).all()
        municipalities = Municipality.find_all()

        data = {
            'messengers': messengers,
            'municipalities': municipalities
        }

        return admin_render_template(Area, 'bds/area/bds_edit_area.html', 'bds', oid=oid, ins=ins,form=form,\
            title="Edit area", data=data, modals=modals)
        
    try:
        ins.name = request.form.get('name', '')
        ins.description = request.form.get('description', '')
        ins.municipality_id = ObjectId(request.form.get('municipality_id')) if request.form.get('municipality_id') != '' else None

        mongo.db.bds_areas.update_one({
            '_id': ins.id
        },{"$set":{
            'name': ins.name,
            'description': ins.description,
            'municipality_id': ins.municipality_id
        }})

        flash('Area updated Successfully!','success')
    except Exception as e:
        flash(str(e),'error')
    
    return redirect(url_for('bp_bds.areas'))
