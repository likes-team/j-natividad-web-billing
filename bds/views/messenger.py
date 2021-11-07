from datetime import datetime
from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash
from flask.json import jsonify
from flask_login import current_user, login_required
from app import mongo
from app.admin.templating import admin_render_template, admin_table, admin_edit
from app.auth.models import Role, User
from bds import bp_bds
from bds.globals import MESSENGER_ROLE
from bds.models import Area, Messenger
from bds.forms import MessengerForm, MessengerEditForm




modals = [
    "bds/messenger/bds_add_area_modal.html"
]


@bp_bds.route('/messengers',methods=['GET'])
@login_required
def messengers():
    form = MessengerForm()
    # fields = [User.id, User.username, User.fname, User.lname, User.email, User.created_at, User.updated_at]
    fields = ['id', 'username', 'first name', 'last name', ' email', 'created_at', 'updated_at']
    table_data = []

    query = Messenger.find_all_by_role_id(role_id=MESSENGER_ROLE.id)

    messenger: User
    for messenger in query:
        table_data.append((
            str(messenger.id),
            messenger.username,
            messenger.fname,
            messenger.lname,
            messenger.email,
            messenger.created_at_local,
            messenger.updated_at_local
        ))

    return admin_table(User, fields=fields, form=form, create_url='bp_bds.create_messenger', \
        edit_url="bp_bds.edit_messenger", module_name='bds', table_data=table_data, \
            create_button=True, create_modal=False, table_template="bds/messenger/messenger_table.html")


@bp_bds.route('/messengers/<string:messenger_id>')
@login_required
def get_messenger_details(messenger_id):
    try:
        messenger = User.find_one_by_id(id=messenger_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(messenger.id),
                'fname': messenger.fname,
                'lname': messenger.lname,
                'username': messenger.username,
                'email': messenger.email,
            }
        }
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 200



@bp_bds.route('/messengers/create', methods=["GET",'POST'])
@login_required
def create_messenger():
    if request.method == "GET":
        areas = Area.find_all()

        data = {
            'areas': areas,
        }

        return admin_render_template(Messenger, "bds/messenger/bds_create_messenger.html", 'bds', title="Create messenger",\
            data=data, modals=modals)

    # try:
    new = Messenger()
    new.fname = request.form.get('fname', '')
    new.lname = request.form.get('lname', '')
    new.email = request.form.get('email', None)
    new.username = request.form.get('username', '')
    new.role_id = MESSENGER_ROLE.id
    new.role_name = MESSENGER_ROLE.name
    new.is_admin = 1 if request.form.get('is_admin') == 'on' else 0
    new.set_password("password")
    new.is_superuser = 0

    areas_line = request.form.getlist('areas[]')
    if areas_line:
        new.areas = [ObjectId(id) for id in areas_line]

    new.save()

    flash('New messenger added successfully!','success')
    # except Exception as exc:
    #     flash(str(exc), 'error')
    return redirect(url_for('bp_bds.messengers'))


@bp_bds.route('/messengers/<string:oid>/edit',methods=['GET','POST'])
@login_required
def edit_messenger(oid):
    ins: Messenger = Messenger.find_one_by_id(id=oid)
    form = MessengerEditForm(obj=ins)

    print("ins.areas: ", ins.areas)
    if request.method == 'GET':
        areas_query = list(mongo.db.bds_areas.find({
            '_id': {'$nin': ins.areas}
        }))
        available_areas = [Area(data=data) for data in areas_query]
        data = {
            'areas': available_areas,
        }
        return admin_render_template(Messenger, 'bds/messenger/bds_edit_messenger.html', 'bds', oid=oid, ins=ins,form=form,\
            title="Edit Messenger", data=data, modals=modals)

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.messengers'))

    # try:
    ins.fname = form.fname.data
    ins.lname = form.lname.data
    ins.email = form.email.data if form.email.data != '' else None
    ins.username = form.username.data

    areas_line = request.form.getlist('areas[]')
    ins.areas = []
    if areas_line:
        ins.areas = [ObjectId(id) for id in areas_line]
    ins.update()

    flash('Messenger update Successfully!','success')
    # except Exception as exc:
    #     flash(str(exc),'error')

    return redirect(url_for('bp_bds.messengers'))
