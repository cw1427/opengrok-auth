"""
Created on 2020-01-14.

@author: sc
"""
from gevent import monkey
monkey.patch_all()
import os
from flask import Flask
from flask_appbuilder import AppBuilder
from flask_session import Session
from fab_addon_autodoc.autodoc import Autodoc

from log import Logging
from logging.handlers import RotatingFileHandler
from app.models import SQLAlchemy
from . import security_manager
import requests
from requests.auth import HTTPBasicAuth
from flask.globals import current_app
import logging

log = logging.getLogger(__name__)

def create_app(config):
    """AUTH app factory method."""
    app = Flask(__name__)
    app.config.from_object(config)
    app.config.from_envvar("CONFIG_ENV", silent=True)
    db = SQLAlchemy(app)
    Session(app)
    Autodoc(app)
    handler = RotatingFileHandler(app.config.get('FLASK_LOG_PATH', "{0}/{1}". \
            format(os.path.abspath(os.path.dirname(__file__)), "authapp.log")), maxBytes=1024 * 1024 * 10, backupCount=13)
    app.config.setdefault('LOG_NAME', 'authapp')
    Logging(app, handler)
    return app, AppBuilder(app, db.session, security_manager_class=security_manager.SecurityManager, \
                            update_perms=app.config['AUTO_UPDATE_PERM'], indexview=security_manager.IndexView)

def _fetch_sse_auth_conf(app_server, app_proj):
        """get the sse project config from BSM conf center."""
        rest_api = "{0}/conf/api/getconfig/sse_{1}/{2}".format(current_app.config['BSM_URL'],
                    app_server, app_proj)
        try:
            res = requests.get(rest_api, verify=False, headers={'content-type': 'application/json;charset=utf8', \
                'X-Bsm-Api': current_app.config['BSMLIB_BSM_APIKEY']}, timeout=300)
            if res.status_code == 200:
                data = res.json()
                log.debug('fetch sse auth conf success')
                return data['data']
            else:
                log.debug('fetch sse auth conf failed {0}'.format(res.content))
                return None
        except Exception as e:
            log.error(' fetch sse auth conf error occurred {0}'.format(e))
            return None

def sse_auth_by_type(app_server, app_proj, user, auth_type):
    """
    Auth sse by type
    """
    if auth_type == 'bsm_conf':
        auth_conf = _fetch_sse_auth_conf(app_server, app_proj)
        if auth_conf:
            if user in auth_conf:
                return True
        return False
    elif auth_type == 'bypass':
        return True
    else:
        return False
