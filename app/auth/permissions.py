from bson.objectid import ObjectId
from flask import session
from flask_login import current_user
from app import CONTEXT, mongo
from app.core.models import CoreModel



def load_permissions(user_id):
    from app.auth.models import User, Role
    user = User.find_one_by_id(user_id)

    if not user and not current_user.is_authenticated:
        CONTEXT['system_modules'].pop('admin',None)
        return True

    session.pop('permissions', None)
    if "permissions" not in session:
        session['permissions'] = {}

    if user.is_superuser or user.role.name == "Admin":
        all_permissions = CoreModel.find_all()

        permission: CoreModel
        for permission in all_permissions:
            session['permissions'][permission.name] = {"read": True, "create": True, \
                "write": True, "delete": True}  

    else:
        role_permissions = Role.objects(id=user.role.id).get().permissions
        for role_permission in role_permissions:
            session['permissions'][role_permission['model_name']] = {"read": role_permission['read'], "create": role_permission['create'], \
                "write": role_permission['write'], "delete": role_permission['delete']}
    return True


def check_create(model_name):
    from app.auth.models import User

    if current_user.is_superuser:
        return True
        
    user = User.objects(id=current_user.id)
    
    for perm in user.permissions:
    
        if model_name == perm.model.name:
    
            if perm.create:
                return True
            else:
                return False

    return False


def check_read(model_name):
    from app.auth.models import User, Role

    if current_user.is_superuser:
        return True
    
    role = Role.objects(id=current_user.role.id).get()
    
    for permission in role.permissions:
        
        if model_name == permission['model_name']:
        
            if permission['read']:
                return True
            else:
                return False

    return False