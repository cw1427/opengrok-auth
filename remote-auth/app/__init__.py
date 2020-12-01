"""
AUTHAPP app init module.

Created on 2020-11-13.
author: sc.
"""
from gevent import monkey
monkey.patch_all()
import os
import sys
from flask import Flask, request, session, _request_ctx_stack
from flask_appbuilder import SQLA, AppBuilder
from flask_appbuilder.models.sqla import Base
from flask_login import LoginManager, current_user, login_user
from log import Logging
import logging
from logging.handlers import RotatingFileHandler
from . import security_manager
import base64
from app.models import SQLAlchemy
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.sql.expression import and_
from app.utils import create_app

"""
 Logging configuration
"""

app, appbuilder = create_app('config.config')
log = logging.getLogger(appbuilder.get_app.config['LOG_NAME'])

from . import views, models
if app.config.get('AUTO_UPDATE_PERM'):
    Base.metadata.create_all(appbuilder.get_session.get_bind(mapper=None, clause=None))
if app.config.get('SECURITY_CLEANUP'):
    log.info("SECURITY CLEANUP enabled, start sync security data into DB")
    appbuilder.security_cleanup()
    log.info("SECURITY CLEANUP enabled, end sync security data into DB")

if app.config['APP_MODE'] == 'DEV':
    try:
        from flask_cors import CORS
        CORS(app, resources=r'*', origins=r'http://localhost:8080', supports_credentials=True)

        @app.after_request
        def process_response(response):
            """process response function a Flask after request method."""
            if request.method == 'OPTIONS' and appbuilder.get_app.config['APP_MODE'] == 'DEV' and \
            response.status_code == 301:
                response.status_code = 200
                _request_ctx_stack.top.session.clear()
            return response
    except Exception as e:
        log.error('Load CORS module failed {0}'.format(e))


def load_user_from_request(request):
    """Flask login request customize loader function."""
    # first, try to do APIKEY authentication.
    api_key = request.headers.get('X-Moto-AUTHAPP-Api')
    if api_key:
        session['REST_SESSION'] = True
        user = appbuilder.get_session.query(MyUser).join(UserExtInfo, and_(MyUser.id == UserExtInfo.id, \
               UserExtInfo.api_key == api_key)).options(joinedload(MyUser.roles)).one_or_none()
        if user:
            login_user(user, remember=False)
        return user
    # Then try to login using the api_key url arg
    api_key = request.args.get('api_key')
    if api_key:
        session['REST_SESSION'] = True
        user = appbuilder.sm.auth_user_ldap(api_key.split(':')[0], api_key.split(':')[1], True)
        if user:
            login_user(user, remember=False)
        return user
    # Last, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    if api_key:
        session['REST_SESSION'] = True
        api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key)
            api_key = api_key.decode()
            user = appbuilder.sm.auth_user_ldap(api_key.split(':')[0], api_key.split(':')[1], True)
            if user:
                login_user(user, remember=False)
            return user
        except Exception as e:
            log.error('Basic authentication failed for authen={0}:{1}'.format(api_key, str(e)))
    # finally, return None if both methods did not login the user
    return None


@app.after_request
def per_request_callbacks(response):
    """Flask request callback hook function."""
    #----deal with REST API invoking remove the session save
    if session.get('REST_SESSION', False):
        _request_ctx_stack.top.session.clear()

    return response


appbuilder.sm.lm.request_loader(load_user_from_request)
