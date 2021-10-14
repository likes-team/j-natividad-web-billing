from datetime import datetime
from flask import redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from app import db, csrf
from app.admin.templating import admin_table, admin_edit
from bds import bp_bds
from bds.models import Subscriber, Delivery
from bds.forms import SubscriberForm, SubscriberEditForm
from decimal import Decimal


@bp_bds.route('/subscribers')
@login_required
def subscribers():
    # fields = [Subscriber.id, Subscriber.fname,Subscriber.lname,Subscriber.created_at, Subscriber.updated_by, Subscriber.updated_at]
    fields = ['id', 'First Name', 'Last Name', 'Created At', 'Updated By', 'Updated At']
    form = SubscriberForm()

    table_data = []

    subscribers = Subscriber.objects()

    subscriber : Subscriber 
    for subscriber in subscribers:
        table_data.append((
            str(subscriber.id),
            subscriber.fname,
            subscriber.lname,
            subscriber.created_at,
            subscriber.updated_at     ,
            subscriber.updated_by
        ))

    return admin_table(Subscriber, fields=fields, form=form, create_url="bp_bds.create_subscriber",\
        edit_url="bp_bds.edit_subscriber", modals=["bds/subscriber/bds_upload_subscribers_csv.html"],\
            action_template="bds/subscriber/bds_subscriber_action.html",\
                table_data=table_data, view_modal=False)


@bp_bds.route('/subscribers/create',methods=['POST'])
@login_required
def create_subscriber():
    form = SubscriberForm()
    
    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.subscribers'))
    
    # try:
    new = Subscriber()
    new.fname = form.fname.data
    new.lname = form.lname.data
    new.email = form.email.data if form.email.data != '' else None
    new.address = form.address.data
    new.sub_area_id = form.sub_area_id.data if form.sub_area_id.data != '' else None
    new.longitude = Decimal(form.longitude.data) if form.longitude.data != '' else None
    new.latitude = Decimal(form.latitude.data) if form.latitude.data != '' else None
    new.contract_no = form.contract_number.data

    new.save()
    flash('New subscriber added successfully!','success')
    # except Exception as e:
    #     flash(str(e), 'error')
    return redirect(url_for('bp_bds.subscribers'))


@bp_bds.route('/subscribers/<string:oid>/edit',methods=['GET','POST'])
@login_required
def edit_subscriber(oid):
    ins = Subscriber.query.get_or_404(oid)
    form = SubscriberEditForm(obj=ins)

    if request.method == "GET":
        form.deliveries_inline.data = ins.deliveries

        return admin_edit(Subscriber, form, 'bp_bds.edit_subscriber', oid, 'bp_bds.subscribers', scripts=[{'bp_bds.static': 'js/subscriber.js'}],\
            extra_modal_template='bds/delivery/bds_details_modal.html')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.subscribers'))

    try:
        ins.fname = form.fname.data
        ins.lname = form.lname.data
        ins.email = form.email.data if form.email.data != '' else None
        ins.address = form.address.data
        ins.sub_area_id = form.sub_area_id.data if form.sub_area_id.data != '' else None
        ins.longitude = form.longitude.data
        ins.latitude = form.latitude.data
        ins.contract_number = form.contract_number.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        db.session.commit()
        flash('Subscriber update Successfully!','success')

    except Exception as e:
        flash(str(e),'error')
    return redirect(url_for('bp_bds.subscribers'))


@bp_bds.route('/api/subscriber/deliveries/<int:delivery_id>', methods=['GET'])
@csrf.exempt
def get_subscriber_delivery(delivery_id):

    delivery = Delivery.query.get_or_404(delivery_id)
    print(delivery)
    if delivery is None:
        return jsonify({
            'id': False
        })

    accuracy = 0
    if delivery.accuracy:
        accuracy = round(float(delivery.accuracy), 2)

    # WE SERIALIZE AND RETURN LIST INSTEAD OF MODELS

    return jsonify({
        'id': delivery.id,
        'subscriber_id': delivery.subscriber.id,
        'subscriber_fname': delivery.subscriber.fname,
        'subscriber_lname': delivery.subscriber.lname,
        'subscriber_address': delivery.subscriber.address,
        'delivery_date': delivery.delivery_date,
        'status': delivery.status,
        'longitude': delivery.delivery_longitude,
        'latitude': delivery.delivery_latitude,
        'accuracy': accuracy,
        'date_mobile_delivery': delivery.date_mobile_delivery,
        'image_path': url_for('bp_bds.static', filename=delivery.image_path),
        'messenger_fname': delivery.messenger.fname,
        'messenger_lname': delivery.messenger.lname
    })