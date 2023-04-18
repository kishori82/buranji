from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os
from extensions import db


def create_app():

    app = Flask(__name__)

    db_file_path = os.path.join(Path(__file__).parent.absolute(), 'buranji.db')

    # Set the configuration for the app's SQLAlchemy connection for dev
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_file_path)

    # Set the configuration for the app's SQLAlchemy connection for prod
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    db.init_app(app)

    return app
