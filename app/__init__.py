__author__ = 'yuchen'
__date__ = '2018/9/1 01:59'

#coding:utf8

from flask import Flask,render_template
from app.admin import bp as admin_blueprint
from app.home import bp as home_blueprint
from app.config import DevConfig
from app.exts import db
from flask_wtf import CSRFProtect


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevConfig)
    db.init_app(app)
    app.register_blueprint(home_blueprint)
    app.register_blueprint(admin_blueprint)
    CSRFProtect(app)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('home/404.html'), 404

    return app