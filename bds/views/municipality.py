from datetime import datetime
from flask import redirect, url_for, request, current_app, flash
from flask_login import current_user, login_required
from app.admin.templating import admin_table, admin_edit
from bds import bp_bds
from bds.models import Municipality
from bds.forms import MunicipalityForm, MunicipalityEditForm



@bp_bds.route('/municipalities')
@login_required
def municipalities():
    fields = ["id", "name", "description", "created_at", "updated_at"]
    form = MunicipalityForm()

    table_data = []

    query = Municipality.find_all()

    municipality: Municipality
    for municipality in query:
        table_data.append((
            str(municipality.id),
            municipality.name,
            municipality.description,
            municipality.created_at_local,
            municipality.updated_at_local
        ))

    return admin_table(Municipality, fields=fields,form=form, table_data=table_data,\
        create_url='bp_bds.create_municipality', edit_url='bp_bds.edit_municipality')


@bp_bds.route('/municipalities/create', methods=['POST'])
@login_required
def create_municipality():
    form = MunicipalityForm()

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.municipalities'))

    try:
        new = Municipality()
        new.name = form.name.data
        new.description = form.description.data
        new.save()

        flash('New municipality added successfully!')
    except Exception as exc:
        flash(str(exc), 'error')
    
    return redirect(url_for('bp_bds.municipalities'))


@bp_bds.route('/municipalities/<string:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_municipality(oid):
    ins = Municipality.query.get_or_404(oid)
    form = MunicipalityEditForm(obj=ins)

    if request.method == "GET":
        return admin_edit(Municipality, form,'bp_bds.edit_municipality', oid, 'bp_bds.municipalities')

    if not form.validate_on_submit():
        for key, value in form.errors.items():
            flash(str(key) + str(value), 'error')
        return redirect(url_for('bp_bds.municipalities'))

    try:
        ins.name = form.name.data
        ins.description = form.description.data
        ins.updated_at = datetime.now()
        ins.updated_by = "{} {}".format(current_user.fname,current_user.lname)
        db.session.commit()

        flash('Municipality update Successfully!','success')
    except Exception as exc:
        flash(str(exc),'error')

    return redirect(url_for('bp_bds.municipalities'))
