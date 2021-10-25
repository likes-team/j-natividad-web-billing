from flask import flash, redirect, url_for, request, jsonify
from flask_cors import cross_origin
from flask_login import current_user, login_required
from app.auth import bp_auth
from app import mongo
from app.auth.models import Role, RolePermission
from app.auth.forms import RoleCreateForm, RoleEditForm
from app.core.models import CoreModel
from app.admin.templating import admin_table, admin_edit
from app.auth.permissions import load_permissions



@bp_auth.route('/roles')
@login_required
def roles(**options):
    fields = ['id', 'name', 'created_at', 'updated_at']
    form = RoleCreateForm()
    form.inline.data = CoreModel.find_all()

    _roles = Role.find_all()

    _table_data = []

    for role in _roles:
        _table_data.append((
            role.id,
            role.name,
            role.created_at_local,
            role.updated_at_local
        ))

    return admin_table(Role, fields=fields, form=form, create_modal_template="auth/role_create_modal.html", \
        create_url='bp_auth.create_role',edit_url='bp_auth.edit_role', \
            view_modal_template="auth/role_view_modal.html", table_data=_table_data,\
                view_modal_url='/auth/get-view-role-data' ,**options)


@bp_auth.route('/get-view-role-data', methods=['GET'])
@login_required
def get_view_role_data():
    _column, _id = request.args.get('column'), request.args.get('id')

    data = Role.objects(id=_id).values_list(_column)

    response = jsonify(result=str(data[0]),column=_column)

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


@bp_auth.route('/roles/create',methods=['GET','POST'])
@login_required
def create_role():
    form = RoleCreateForm()

    if form.validate_on_submit():
        form_data = request.form

        permissions = []

        models = CoreModel.find_all()

        for model in models:
            read,create,write,delete = 0,0,0,0

            read_string = 'read_{}'.format(model.name)
            create_string = 'create_{}'.format(model.name)
            write_string = 'write_{}'.format(model.name)
            delete_string = 'chk_delete_{}'.format(model.name)

            if form_data.get(read_string) == 'on': read, has_model = 1,True
            if form_data.get(create_string) == 'on': create,has_model = 1,True
            if form_data.get(write_string) == 'on': write,has_model = 1, True
            if form_data.get(delete_string) == 'on': delete,has_model = 1,True

            permissions.append({
                'model_name': model.name,
                'read': read,
                'write': write,
                'delete': delete,
                'create': create
            })

        mongo.db.auth_user_roles.insert_one(
            {
                'name': form.name.data,
                'permissions': permissions
            }
        )

        flash('Role added successfully!','success')
        return redirect(url_for('bp_auth.roles'))


@bp_auth.route('/roles/<string:oid>/edit',methods=['GET','POST'])
@login_required
def edit_role(oid,**options):
    role = Role.find_one_by_id(oid)
    form = RoleEditForm(obj=role)

    if request.method == "GET":
        form.permission_inline.data = role.permissions
        
        _scripts = [
            {'bp_admin.static': 'js/admin_edit.js'}
        ]

        return admin_edit(Role, form, "bp_auth.edit_role", oid, 'bp_auth.roles', scripts=_scripts, \
            **options)

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_auth.roles'))

    form_data = request.form
    permissions = []

    models = CoreModel.find_all()

    for model in models:

        read,create,write,delete = 0,0,0,0

        read_string = 'read_{}'.format(model.name)
        create_string = 'create_{}'.format(model.name)
        write_string = 'write_{}'.format(model.name)
        delete_string = 'delete_{}'.format(model.name)

        if read_string in request.form : read = True
        if create_string in request.form : create = True
        if write_string in request.form : write =  True
        if delete_string in request.form : delete = True

        permissions.append({
            'model_name': model.name,
            'read': read,
            'write': write,
            'delete': delete,
            'create': create
        })
    
    try:
        role.name = form.name.data
        role.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        role.set_updated_at()

        role.permissions = permissions
        role.save()

        flash('Role update Successfully!','success')
    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('bp_auth.roles'))


@bp_auth.route('/roles/<int:oid1>/permissions/<int:oid2>/edit', methods=['POST'])
@cross_origin()
def role_edit_permission(oid1, oid2):
    
    permission_type = request.json['permission_type']
    value = request.json['value']

    permission = RolePermission.query.get_or_404(oid2)

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

    db.session.commit()
    
    load_permissions(current_user.id)

    resp = jsonify(1)
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.status_code = 200

    return resp
