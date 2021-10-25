from datetime import datetime
from bson.objectid import ObjectId
from flask import redirect, url_for, request, flash, jsonify
from flask_login import  login_required, current_user
from app.admin.templating import admin_table, admin_edit
from bds import bp_bds
from bds.models import Billing
from bds.forms import BillingForm, BillingEditForm
from bds.functions import generate_number
from app import mongo



@bp_bds.route('/billings')
@login_required
def billings():
    fields = [
        "id", "active", "number", "name", "description", "date_from", 
        "date_to", "created_by", "created_at"]
    form = BillingForm()

    _billing_generated_number = ""

    # query = db.session.query(Billing).order_by(Billing.id.desc()).first()
    query_last_billing = list(mongo.db.bds_billings.find().sort('created_at').limit(1))

    if query_last_billing:
        _billing_generated_number = generate_number("BILL", query_last_billing[0]['billing_no'])
    else:
        _billing_generated_number = "BILL00000001"

    form.number.auto_generated = _billing_generated_number
    
    table_data = []

    query_billings = Billing.find_all()

    billing: Billing
    for billing in query_billings:
        table_data.append((
            str(billing.id),
            billing.active,
            billing.full_billing_no,
            billing.name,
            billing.description,
            billing.date_from,
            billing.date_to,
            billing.created_by,
            billing.created_at_local,
        ))

    return admin_table(Billing, fields=fields, form=form, create_url='bp_bds.create_billing',\
        edit_url="bp_bds.edit_billing", table_template="bds/bds_billing_table.html",\
            view_modal_template="bds/bds_billing_view_modal.html",
            table_data=table_data)


@bp_bds.route('/billings/create',methods=['POST'])
@login_required
def create_billing():
    form = BillingForm()
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.billings'))
    
    try:
        new = Billing()
        new.active = False
        new.full_billing_no = form.number.data
        new.name = form.name.data
        new.description = form.description.data
        new.date_to = form.date_to.data
        new.date_from = form.date_from.data
        new.billing_no = new.count() + 1
        new.save()

        flash('New billing added successfully!','success')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('bp_bds.billings'))


@bp_bds.route('/billings/<string:oid>/edit',methods=['GET','POST'])
@login_required
def edit_billing(oid):
    ins = Billing.query.get_or_404(oid)
    form = BillingEditForm(obj=ins)

    if request.method == "GET":
        return admin_edit(Billing, form, 'bp_bds.edit_billing', oid, 'bp_bds.subscribers')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.billings'))

    try:
        ins.name = form.name.data
        ins.description = form.description.data
        ins.date_to = form.date_to.data
        ins.date_from = form.date_from.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)

        db.session.commit()
        flash('Billing update Successfully!','success')

    except Exception as e:
        flash(str(e),'error')

    return redirect(url_for('bp_bds.billings'))


@bp_bds.route('/billings/<string:billing_id>/set-active', methods=['POST'])
@login_required
def set_active(billing_id):
    status = request.json['status']

    # try:

    with mongo.cx.start_session() as session:
        with session.start_transaction():
            mongo.db.bds_billings.update_many({
                'active': 1
            }, {"$set":{
                'active': 0
            }}, session=session)

            mongo.db.bds_billings.update_one({
                '_id': ObjectId(billing_id)
            },{"$set":{
                'active': status
            }}, session=session)

    # except Exception:
    #     return jsonify({'result': False})
    response = jsonify({
        'result': True
    })

    return response
    
