from flask import (jsonify, abort)
from flask_cors import cross_origin
from bds import bp_bds
from bds.models import Billing



@bp_bds.route('/api/billings/<string:billing_id>', methods=['GET'])
@cross_origin()
def get_billing(billing_id):
    billing = Billing.find_one_by_id(id=billing_id)

    if billing is None:
        abort(404)

    response = jsonify({
        'id': str(billing.id),
        'number': billing.full_billing_no,
        'name': billing.name,
        'description': billing.description,
        'date_from': billing.date_from,
        'date_to': billing.date_to,
    })

    return response, 200
