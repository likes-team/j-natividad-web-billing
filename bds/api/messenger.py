from flask import (jsonify, request, abort)
from app import csrf
from app.auth.models import User
from bds import bp_bds
from bds.models import Delivery, Subscriber, Area, SubArea



@bp_bds.route('/api/messengers/<int:messenger_id>/areas', methods=['GET'])
@csrf.exempt
def get_messenger_areas(messenger_id):
    messenger = User.query.get(messenger_id)

    _data = []
    for area in messenger.areas:
        _sub_area_list = []
        for sub_area in area.sub_areas:
            _sub_area_list.append(
                {
                "sub_area_id": sub_area.id,
                "sub_area_name": sub_area.name,
                "sub_area_description": sub_area.description,
                }
            )
        _data.append({
            "area_id": area.id,
            "area_name": area.name,
            "area_description": area.description,
            "sub_areas": _sub_area_list
        })

    print(_data)
    response = jsonify(_data)

    return response, 200



