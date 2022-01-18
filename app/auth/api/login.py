from flask import jsonify, abort, request
from flask_cors import cross_origin
from app.auth import bp_auth
from app.auth.models import User
from app import csrf



@bp_auth.route('/api/users/login',methods=['POST'])
@cross_origin()
@csrf.exempt
def api_login():
    username = request.json['username']
    password = request.json['password']

    try:
        user = User.find_one_by_username(username=username)

        if user is None or not user.check_password(password):
            response = {
                'status': 'error',
                'message': "Invalid username or password"
            }
            return jsonify(response), 401
            
        response = jsonify({
            'status': 'success',
            'data': user.toJson(),
            'message': 'Login successfully!'
            })
            
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        }), 500


@bp_auth.route('/api/users', methods=['GET'])
def get_users():
    user_list = []
    users = User.query.all

    for user in users:
        user_list.append({
            'id': user.id,
            'fname': user.fname,
            'lname': user.lname,
            'email': user.email,
        })

    return jsonify({'users':user_list})

@bp_auth.route('/api/user/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        abort(404)

    return jsonify({
        'id': user.id,
        'fname': user.fname,
        'lname': user.lname,
        'email': user.email,
    })
