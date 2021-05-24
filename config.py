import os
from dotenv import load_dotenv



basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    load_dotenv()

    SECRET_KEY = "72d3e92e06474a69bd44dd6733f59722"

    CORS_HEADERS = 'Content-Type' # Flask Cors

    # DEVELOPERS-NOTE: ADMIN PAGE CONFIGURATIONS HERE
    ADMIN = {
        'APPLICATION_NAME': 'Likes',
        'DATA_PER_PAGE': 25,
        'HOME_URL': 'bp_admin.dashboard',
        'DASHBOARD_URL': 'bp_admin.dashboard',
        'MODELS_SIDEBAR_HEADER': 'SYSTEM MODELS'
    }
    #                 -END-

    # DEVELOPERS-NOTE: AUTH CONFIGURATIONS HERE
    AUTH = {
        'LOGIN_REDIRECT_URL': 'bp_admin.dashboard',
    }
    #                 -END-

    # DEVELOPER-NOTE: -ADD YOUR CONFIGURATIONS HERE-
    UPLOAD_IMAGES_FOLDER = basedir + "/bds/static/img/uploads"
    UPLOAD_CSV_FOLDER = basedir + "/bds/static/csv/uploads"
    #                 -END-


def _get_database(server):
    load_dotenv()

    host = "localhost"
    user = "root"
    password = "db_password"
    database = "db_bds"
    if server == 'pythonanywhere':
        return "mysql://{}:{}@{}/{}".format(user,password,host,database)
    else:
        return "mysql+pymysql://{}:{}@{}/{}".format(user,password,host,database)


class DevelopmentConfig(Config):
    """
    Development configurations
    """

    SQLALCHEMY_DATABASE_URI = _get_database('localhost')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    # SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """
    Production configurations
    """
    SQLALCHEMY_DATABASE_URI = _get_database('pythonanywhere')
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class TestingConfig(Config):
    """
    Testing configurations
    """

    TESTING = True
    # SQLALCHEMY_ECHO = True


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
