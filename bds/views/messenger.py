from datetime import datetime
from flask import redirect, url_for, request, flash
from flask_login import current_user, login_required
from app import mongo
from app.admin.templating import admin_table, admin_edit
from app.auth.models import Role, User
from bds import bp_bds
from bds.globals import MESSENGER_ROLE
from bds.models import Messenger
from bds.forms import MessengerForm, MessengerEditForm



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
        edit_url="bp_bds.edit_messenger", module_name='bds', table_data=table_data)


@bp_bds.route('/messengers/create', methods=['POST'])
@login_required
def create_messenger():
    form = MessengerForm()
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.messengers'))

    # try:
    new = Messenger()
    new.fname = form.fname.data
    new.lname = form.lname.data
    new.email = form.email.data
    new.username = form.username.data
    new.role_id = MESSENGER_ROLE.id
    new.role_name = MESSENGER_ROLE.name
    new.is_admin = 1 if form.is_admin.data == 'on' else 0
    new.set_password("password")
    new.is_superuser = 0
    new.save()

    flash('New messenger added successfully!','success')
    # except Exception as exc:
    #     flash(str(exc), 'error')

    return redirect(url_for('bp_bds.messengers'))


@bp_bds.route('/messengers/<string:oid>/edit',methods=['GET','POST'])
@login_required
def edit_messenger(oid):
    ins = User.query.get_or_404(oid)
    form = MessengerEditForm(obj=ins)

    if request.method == "GET":

        form.areas_inline.data = ins.areas

        return admin_edit(Messenger, form,'bp_bds.edit_messenger',oid, 'bp_bds.messengers',\
            module_name='bds')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.messengers'))

    try:
        ins.fname = form.fname.data
        ins.lname = form.lname.data
        ins.email = form.email.data if form.email.data != '' else None
        ins.username = form.username.data
        ins.is_admin = 1 if form.is_admin.data == 'on' else 0
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        db.session.commit()

        flash('Messenger update Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('bp_bds.messengers'))
