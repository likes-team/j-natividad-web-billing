from bson.objectid import ObjectId
from flask import current_app, redirect, render_template, request, flash, url_for
from flask_login import login_required
from app import mongo
from bds import bp_bds
from bds.globals import SUBSCRIBER_ROLE
from bds.models import Area, SubArea, Subscriber
import os, csv, platform



@bp_bds.route('/upload/subscribers/csv', methods=['POST'])
@login_required
def upload_subscribers_csv():
    uploaded_file = request.files['csv_file']
    if uploaded_file.filename != '':
        file_path = os.path.join(current_app.config['UPLOAD_CSV_FOLDER'], uploaded_file.filename)
        
        if os.path.exists(file_path):
            flash("File exists!, (Rename the file then upload again)", 'error')
            return redirect(url_for('bp_bds.subscribers'))

        uploaded_file.save(file_path)

        # try:
        with open(file_path, encoding = "ISO-8859-1") as f:
            csv_file = csv.reader(f)
            with mongo.cx.start_session() as session:
                with session.start_transaction():
                    for _id,row in enumerate(csv_file):
                        if not _id == 0:
                            cycle = row[0]
                            type = row[1]
                            municipality = row[2]
                            area_name = row[3]
                            sub_area_name = row[4]
                            contract_no = row[5]
                            fname = row[6]
                            lname = row[7]
                            full_name = row[8]
                            full_address = row[9]

                            print(contract_no, fname,lname)
                            area = mongo.db.bds_areas.find_one({'name': area_name}, session=session)
                            # area = Area.objects(name=area_name).first()
                            sub_area = mongo.db.bds_sub_areas.find_one({'name': sub_area_name}, session=session)
                            # sub_area = SubArea.objects(name=sub_area_name).first()

                            new_area_id = ObjectId()

                            if area is None:
                                mongo.db.bds_areas.insert_one({
                                    '_id': new_area_id,
                                    'name': area_name,
                                    'description': ''
                                },session=session)

                            new_sub_area_id = ObjectId()
                            if sub_area is None:
                                
                                sub_area_area_id = None
                                if area is None:
                                    sub_area_area_id = new_area_id
                                else:
                                    sub_area_area_id = area['_Id']
                                
                                mongo.db.bds_sub_areas.insert_one({
                                    '_id': new_sub_area_id,
                                    'name': sub_area_name,
                                    'description': '',
                                    'area_id': sub_area_area_id
                                },session=session)

                            new = Subscriber()
                            new.contract_no = contract_no
                            new.fname = fname
                            new.lname = lname
                            new.address = full_address
                            new.establishment = type
                            new.cycle = cycle

                            if sub_area is None:
                                new.sub_area_id = new_sub_area_id
                            else:
                                new.sub_area_id = sub_area

                            mongo.db.auth_users.insert_one({
                                "_id": ObjectId(),
                                "role_id": SUBSCRIBER_ROLE.id,
                                "role_name": SUBSCRIBER_ROLE.name,
                                "contract_no": new.contract_no,
                                "fname": new.fname,
                                "lname": new.lname,
                                "address": new.address,
                                "establishment": new.establishment,
                                "cycle": new.cycle,
                                "sub_area_id": new_sub_area_id if sub_area is None else sub_area['_id'],
                                "sub_area_name": sub_area_name if sub_area is None else sub_area['name']
                            },session=session)

            flash("Subscribers uploaded!", 'success')
    
        # except Exception as exc:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)

        #     flash(str(exc), 'error')
            
    return redirect(url_for('bp_bds.subscribers'))
