__author__ = 'yuchen'
__date__ = '2018/9/1 00:25'


import os
from datetime import timedelta

class Config(object):
    pass

class ProdConfig(Config):
    pass

CMS_USER_ID='wnsgdsb'
FRONT_USER_ID='higirl'

class DevConfig(Config):
    DEBUG= True
    USERNAME = 'root'
    PASSWORD = 'angie'
    HOSTNAME = '127.0.0.1'
    PORT = '3306'
    DATABASE = 'movie'
    DB_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=USERNAME,
                                                                                            password=PASSWORD,
                                                                                            host=HOSTNAME, port=PORT,
                                                                                            db=DATABASE)
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'yawenxiaojiejie'

    DEBUG = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    PAGE_SET = 2
    UP_DIR = os.path.join(os.path.dirname(__file__), 'static/movie_files/')

    AUTH_SWITCH= True
