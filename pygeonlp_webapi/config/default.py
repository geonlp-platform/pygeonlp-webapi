import logging
import os

import pygeonlp.api as geonlp_api


class BaseConfig(object):
    DEBUG = False
    TESTING = False

    GEONLP_DIR = geonlp_api.get_db_dir()
    JAGEOCODER_DIR = geonlp_api.get_jageocoder_db_dir()
    GEONLP_API_OPTIONS = {}

    LOGGING = {
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': logging.INFO,
            'handlers': ['wsgi']
        }
    }


class ProductionConfig(BaseConfig):
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True


config = DevelopmentConfig()
