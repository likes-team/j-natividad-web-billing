import pymongo
from datetime import datetime
from bson.objectid import ObjectId
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from flask_cors import cross_origin
from app import mongo
from app.core.models import CoreModel
from app.core.logging import create_log
from app.auth import bp_auth
from app.auth.models import Role, User, UserPermission
from app.auth.forms import UserForm, UserEditForm, UserPermissionForm
from app.auth import auth_urls
from app.auth.permissions import load_permissions, check_create
from app.admin.templating import admin_table, admin_edit
from bds.globals import ADMIN_ROLE



@bp_auth.route('/users')
@login_required
def users():
    roles = [
        ADMIN_ROLE
    ]
    
    return render_template("auth/adminty_user.html", roles=roles)


@bp_auth.route('/users/<string:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    try:
        user = User.find_one_by_id(id=user_id)

        response = {
            'status': 'success',
            'data': {
                'id': str(user.id),
                'fname': user.fname,
                'lname': user.lname,
                'username': user.username,
                'email': user.email,
                'role_id': str(user.role_id),
            },
        }
        
        return jsonify(response), 200
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500

@bp_auth.route('/users/dt', methods=['GET'])
def fetch_users_dt():
    draw = request.args.get('draw')
    start, length = int(request.args.get('start')), int(request.args.get('length'))
    search_value = request.args.get("search[value]")
    table_data = []

    if search_value != '':
        query = list(mongo.db.auth_users.aggregate([
            {"$match": {
                "role_id": ADMIN_ROLE.id,
                "lname": {"$regex": search_value}
            }},
            {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                         "foreignField": "_id", 'as': "role"}},
            {"$sort": {
                'created_at': pymongo.DESCENDING
            }}
        ]))
        total_records = len(query)
    else:
        query = list(mongo.db.auth_users.aggregate([
            {"$match": {
                "role_id": ADMIN_ROLE.id,
            }},
            {"$lookup": {"from": "auth_user_roles", "localField": "role_id",
                         "foreignField": "_id", 'as': "role"}},
            {"$skip": start},
            {"$limit": length},
            {"$sort": {
                'created_at': pymongo.DESCENDING
            }}
        ]))
        total_records = len(User.find_all_by_role_id(role_id=ADMIN_ROLE.id))

    filtered_records = len(query)

    print("START: ", start)
    print("DRAW: ", draw)
    print("LENGTH: ", length)
    print("filtered_records: ", filtered_records)
    print("total_records: ", total_records)

    for data in query:
        user: User = User(data=data)
        table_data.append((
            str(user.id),
            user.fname,
            user.lname,
            user.username,
            user.email,
            user.role.name if user.role is not None else '',
            user.created_at_local,
            ''
        ))
        
    response = {
        'draw': draw,
        'recordsTotal': filtered_records,
        'recordsFiltered': total_records,
        'data': table_data
    }
    return jsonify(response)


@bp_auth.route('/get-view-user-data', methods=['GET'])
@login_required
def get_view_user_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    _data = User.objects(id=_id).values_list(_column)

    response = jsonify(result=str(_data[0]),column=_column)

    if _column == "role":
        response = jsonify(result=str(_data[0].id),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_auth.route('/users/create', methods=['POST'])
@login_required
def create_user():
    form = request.form
 
    try:
        new = User()
        new.fname = form.get('fname', '')
        new.lname = form.get('lname', '')
        new.email = form.get('email', '')
        new.username = form.get('username', '')
        new.set_password("password")
        new.is_superuser = 0
        
        new.role_id = ObjectId(form.get('role')) if form.get('role') != '' else None
        
        role: Role = Role.find_one_by_id(id=new.role_id)
        new.role_name = role.name
        new.save()
        
        response = {
            'status': 'success',
            'data': new.toJson(),
            'message': "New user added successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        print(err)
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_auth.route('/users/<string:oid>/edit', methods=['POST'])
@login_required
@cross_origin()
def edit_user(oid):
    form = request.form
    
    try:
        mongo.db.auth_users.update_one({
            "_id": ObjectId(oid)
        }, {"$set": {
            "fname": form.get('fname'),
            'lname': form.get('lname'),
            'username': form.get('username'),
            'email': form.get('email'),
            'role_id': ObjectId(form.get('role')) if form.get('role') != '' else None
        }})
        
        response = {
            'status': 'success',
            'data': {},
            'message': "User updated Successfully!"
        }
        return jsonify(response), 201
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_auth.route('/permissions')
@login_required
def user_permission_index():
    fields = [UserPermission.id, User.username, User.fname, CoreModel.name, UserPermission.read, UserPermission.create,
              UserPermission.write, UserPermission.delete]
    model = [UserPermission, User,CoreModel]
    form = UserPermissionForm()
    return admin_table(*model, fields=fields, form=form, list_view_url=auth_urls['user_permission_index'], create_modal=False,
                       view_modal=False, active="Users")


@bp_auth.route('/username_check', methods=['POST'])
def username_check():
    if request.method == 'POST':
        username = request.json['username']
        user = User.query.filter_by(username=username).first()
        if user:
            resp = jsonify(result=0)
            resp.status_code = 200
            return resp
        else:
            resp = jsonify(result=1)
            resp.status_code = 200
            return resp


@bp_auth.route('/_email_check',methods=["POST"])
def email_check():
    if request.method == 'POST':
        email = request.json['email']
        user = User.query.filter_by(email=email).first()
        if user:
            resp = jsonify(result=0)
            resp.status_code = 200
            return resp
        else:
            resp = jsonify(result=1)
            resp.status_code = 200
            return resp


@bp_auth.route('/change_password/<int:oid>',methods=['POST'])
def change_password(oid):
    user = User.query.get_or_404(oid)
    user.set_password(request.form.get('password'))
    # db.session.commit()
    flash("Password change successfully!",'success')
    return redirect(request.referrer)


@bp_auth.route('/users/<int:oid1>/permissions/<int:oid2>/edit', methods=['POST'])
@cross_origin()
def edit_permission(oid1, oid2):

    permission_type = request.json['permission_type']
    value = request.json['value']

    permission = UserPermission.query.get_or_404(oid2)

    if not permission:
        resp = jsonify(0)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.status_code = 200
        
        return resp

    if permission_type == 'read':
        permission.read = value
    
    elif permission_type == 'create':
        permission.create = value

    elif permission_type == 'write':
        permission.write = value
    
    elif permission_type == "delete":
        permission.delete = value

    # db.session.commit()

    load_permissions(current_user.id)

    resp = jsonify(1)
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.status_code = 200

    return resp
