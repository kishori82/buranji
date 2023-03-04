from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
from .extensions import db


def create_app():

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    db.init_app(app)

    return app
