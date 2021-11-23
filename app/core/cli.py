import platform
import os
from bson.objectid import ObjectId
import click
import csv
from shutil import copyfile
from bds.models import Delivery
from config import basedir
from app.core.models import CoreModel, CoreModule
from app import MODULES, mongo
from . import bp_core
from .models import CoreCity,CoreProvince
from app.auth.models import User, Role



def core_install():
    """
    Tatanggap to ng list ng modules tapos iinsert nya sa database yung mga models o tables nila, \
        para malaman ng system kung ano yung mga models(eg. Users,Customers)
    Parameters
    ----------
    modules
        Listahan ng mga modules na iinstall sa system
    """

    print("Installing...")

    # try:
    if platform.system() == "Windows":
        provinces_path = basedir + "\\app" + "\\core" + "\\csv" + "\\provinces.csv"
        cities_path = basedir + "\\app" + "\\core" + "\\csv" + "\\cities.csv"
    elif platform.system() == "Linux":
        provinces_path = basedir + "/app/core/csv/provinces.csv"
        cities_path = basedir + "/app/core/csv/cities.csv"
    else:
        raise Exception("Platform not supported yet.")
    
    module_count = 0

    homebest_module = None

    for module in MODULES:
        print(module)
        # TODO: Iimprove to kasi kapag nag error ang isa damay lahat dahil sa last_id
        homebest_module = CoreModule.find_one_by_name(name=module.module_name)
        # last_id = 0
        if not homebest_module:
            new_module = CoreModule()
            new_module.name = module.module_name
            new_module.short_description = module.short_description
            new_module.long_description = module.long_description
            new_module.status = 'installed'
            new_module.version = module.version
            new_module.save()

            homebest_module = new_module
                
            print("MODULE - {}: SUCCESS".format(new_module.name))
            # last_id = new_module.id

        model_count = 0

        for model in module.models:
            homebestmodel = CoreModel.find_one_by_name(name=model.__amname__)

            if not homebestmodel:
                new_model = CoreModel()
                new_model.name = model.__amname__
                new_model.module_id = homebest_module.id
                new_model.description=model.__amdescription__
                new_model.save()

                print("MODEL - {}: SUCCESS".format(new_model.name))

            model_count = model_count + 1

        if len(module.no_admin_models) > 0 :
            for xmodel in module.no_admin_models:
                homebestmodel = CoreModel.find_one_by_name(name=xmodel.__amname__)
                
                if not homebestmodel:
                    new_model = CoreModel()
                    new_model.name = model.__amname__
                    new_model.module_id = homebest_module.id
                    new_model.description=model.__amdescription__
                    new_model.admin_included = False
                    new_model.save()

                    print("MODEL - {}: SUCCESS".format(new_model.name))

        module_count = module_count + 1

    print("Inserting provinces to database...")
    if CoreProvince.count() < 88:
        with open(provinces_path) as f:
            csv_file = csv.reader(f)

            for id, row in enumerate(csv_file):
                if not id == 0:
                    CoreProvince(
                        name=row[2]
                    ).save()

        print("Provinces done!")

    else:
        print("Provinces exists!")
    print("")
    print("Inserting cities to database...")
    
    if CoreCity.count() < 1647:
        with open(cities_path) as f:
            csv_file = csv.reader(f)

            for id,row in enumerate(csv_file):
                if not id == 0:
                    
                    CoreCity(
                        name=row[2]
                    ).save()

        print("Cities done!")
    else:
        print("Cities exists!")

    print("Inserting system roles...")
    if Role.count() > 0:
        print("Role already inserted!")
    else:
        Role(
            name="Admin",
        ).save()
        
        print("Admin role inserted!")

    if not User.count() > 0:
        print("Creating a SuperUser/owner...")
        _create_superuser()

    # except Exception as exc:
    #     print(str(exc))
    #     return False

    return True


@bp_core.cli.command('create_superuser')
def create_superuser():
    _create_superuser()


@bp_core.cli.command("create_module")
@click.argument("module_name")
def create_module(module_name):
    try:

        if platform.system() == "Windows":
            module_path = basedir + "\\app" + "\\" + module_name
            templates_path = basedir + "\\app" + "\\" + module_name + "\\" + "templates" + "\\" + module_name 
            core_init_path = basedir + "\\app" + "\\core" + \
                "\\module_template" + "\\__init__.py"
            core_models_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\models.py"
            core_routes_path = basedir + "\\app" + \
                "\\core" + "\\module_template" + "\\routes.py"
        elif platform.system() == "Linux":
            module_path = basedir + "/app" + "/" + module_name
            templates_path = basedir + "/app" + "/" + module_name + "/templates" + "/" + module_name
            core_init_path = basedir + "/app" + "/core" + "/module_template" + "/__init__.py"
            core_models_path = basedir + "/app" + "/core" + "/module_template" + "/models.py"
            core_routes_path = basedir + "/app" + "/core" + "/module_template" + "/routes.py"
        else:
            raise Exception
        
        core_file_list = [core_init_path, core_models_path, core_routes_path]

        if not os.path.exists(module_path):
            os.mkdir(module_path)
            os.makedirs(templates_path)
            for file_path in core_file_list:
                file_name = os.path.basename(file_path)
                copyfile(file_path, os.path.join(module_path, file_name))
    except OSError as e:
        print("Creation of the directory failed")
        print(e)
    else:
        print("Successfully created the directory %s " % module_path)


@bp_core.cli.command("install")
def install():

    if core_install():
        print("Installation complete!")

    else:
        print("Installation failed!")


def _create_superuser():
    try:
        role = Role(data=mongo.db.auth_user_roles.find_one({'name': 'Admin'}))
        
        user = User()
        user.fname = "Administrator"
        user.lname = "Administrator"
        user.username = input("Enter Username: ")
        user.is_superuser = True
        user.role_id = role._id
        user.set_password(input("Enter password: "))
        user.save()

        print(user)

        print("SuperUser Created!")
    except Exception as exc:
        print(str(exc))



@bp_core.cli.command('automate_images')
def automate_images():
    deliveries_query = list(mongo.db.bds_deliveries.aggregate([
        {'$match': {
            "billing_id": ObjectId("618626a1adc256448a284fc4"), 
            "sub_area_id": ObjectId("618616b49790b927eb768469"), 
            'active': 1, 
            'status': {"$ne": 'IN-PROGRESS'},
            },
         },
        {'$lookup': {
            'from': "auth_users", 
            "localField": "subscriber_id", 
            "foreignField": "_id",
            'as': 'subscriber'
            }},
        {'$lookup': {
            'from': "bds_areas", 
            "localField": "area_id", 
            "foreignField": "_id",
            'as': 'area'
            }},
        {'$lookup': {
            'from': "bds_sub_areas", 
            "localField": "sub_area_id", 
            "foreignField": "_id",
            'as': 'sub_area'
            }}
    ]))
    
    count = 1
    for data in deliveries_query:
        try:
            delivery = Delivery(data=data)
            
            check_path = delivery.image_path[:12]
            
            if check_path != "img/uploads/":
                continue
            
            new_path = "https://likes-bucket.s3.ap-southeast-1.amazonaws.com/uploads/" + delivery.image_path[12:]
            
            mongo.db.bds_deliveries.update_one({
                "_id": delivery.id, 
            },{"$set": {
                'image_path': new_path
            }});
            
            print(str(count) + " " + "Success  " + str(delivery.id));
            count = count + 1
        except Exception:
            print(str(count) + " " + "Error")
            continue
    
    
    
# @bp_core.cli.command('automate_images')
# def automate_images():
#     deliveries_query = list(mongo.db.bds_deliveries.aggregate([
#         {'$match': {
#             "billing_id": ObjectId("618626a1adc256448a284fc4"), 
#             "area_id": ObjectId("618616b49790b927eb768468"),
#             'active': 1, 
#             'status': {"$ne": 'IN-PROGRESS'},
#             },
#          },
#         {'$lookup': {
#             'from': "auth_users", 
#             "localField": "subscriber_id", 
#             "foreignField": "_id",
#             'as': 'subscriber'
#             }},
#         {'$lookup': {
#             'from': "bds_areas", 
#             "localField": "area_id", 
#             "foreignField": "_id",
#             'as': 'area'
#             }},
#         {'$lookup': {
#             'from': "bds_sub_areas", 
#             "localField": "sub_area_id", 
#             "foreignField": "_id",
#             'as': 'sub_area'
#             }}
#     ]))
    
#     count = 1
#     for data in deliveries_query:
#         try:
#             delivery = Delivery(data=data)
#             path = delivery.image_path[12:]
#             print("\"" + path + "\",")
#             count = count + 1
#         except Exception:
#             continue
    
# @bp_core.cli.command("add_registration_date_field")
# def install():
#     registrations = Registration.objects()

#     for x in registrations:
#         registrations.registered_