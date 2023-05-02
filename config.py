import os


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    DATABASE_HOST = os.environ.get("SECRET_HOST")
    DATABASE_PORT = os.environ.get("DATABASE_PORT")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
    DATABASE_USER = os.environ.get("DATABASE_USER")


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
