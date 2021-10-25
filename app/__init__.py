"""
app/__init__.py
====================================
Create our application
"""
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import app_config

# DEVELOPERS-NOTE: -INCLUDE YOUR IMPORTS HERE-

#                  -END-

mongo = PyMongo()
csrf = CSRFProtect()
login_manager = LoginManager()

# DEVELOPERS-NOTE: -INITIATE YOUR IMPORTS HERE-

#                   -END-


MODULES = []

CONTEXT = {
    'system_modules': []
}


def internal_server_error(e):
    from flask import render_template
    return render_template('admin/internal_server_error.html'), 500


def create_app(config_name):
    """
    Return the app at crenecreate nito ang application
    ----------
    config_name
        A string para kung ano ang gagamiting environment configuration(eg.develop,production,testing)
    """
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(app_config[config_name])
    app.register_error_handler(500, internal_server_error)

    mongo.init_app(app)
    login_manager.init_app(app)
    cors = CORS(app, resources={r"/*": {"origins": "*"}})
    csrf.init_app(app)

    # DEVELOPERS-NOTE: -INITIALIZE YOUR IMPORTS HERE-

    #                    -END-

    login_manager.login_view = 'bp_auth.login'
    login_manager.login_message = "You must be logged in to access this page."

    with app.app_context():

        # DEVELOPERS-NOTE: -IMPORT HERE THE SYSTEM MODULES-
        from app.core import bp_core
        from app.auth import bp_auth
        from app.admin import bp_admin
        from bds import bp_bds
        #                   -END-

        # DEVELOPERS-NOTE: -REGISTER HERE THE MODULE BLUEPRINTS-
        app.register_blueprint(bp_core, url_prefix='/')
        app.register_blueprint(bp_auth, url_prefix='/auth')
        app.register_blueprint(bp_admin, url_prefix='/admin')
        app.register_blueprint(bp_bds, url_prefix='/bds')
        #               -END-

        # DEVELOPERS-NOTE: -INCLUDE HERE YOUR MODULE Admin models FOR ADMIN TEMPLATE-
        from app.admin.admin import AdminModule
        from app.auth.auth import AuthModule
        from bds.bds import BDSModule
        #                  -END-
        
        # DEVELOPERS-NOTE: -APPEND YOUR MODULE HERE-
        MODULES.append(AdminModule)
        MODULES.append(AuthModule)
        MODULES.append(BDSModule)
        #                  -END-

        # Load CONTEXT data
        CONTEXT['header_color'] = 'header_color15' # Default color
        CONTEXT['sidebar_color'] = "sidebar_color15" # Default color

    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)

    return app
