"""
Created on 2018-2-12.

@author: sc
"""
import os
import version
from config import config_local
db_user = os.environ.get('AUTHAPP_DB_USER', 'root')
db_password = os.environ.get('AUTHAPP_DB_PWD', '****')
db_host = os.environ.get('AUTHAPP_DB_HOST', '127.0.0.1:3306')
db_name = os.environ.get('AUTHAPP_DB_NAME', 'ats')
APP_NAME = "AUTHAPP"
SQLALCHEMY_DATAAUTHAPPE_URI = 'mysql://{0}:{1}@{2}/{3}'.format(db_user, db_password, db_host, db_name)
TEMPLATES_AUTO_RELOAD = False

#---------------------------------------------------
# SQLAlchemy pool config setup for mysql
#---------------------------------------------------
SQLALCHEMY_POOL_SIZE = 100
SQLALCHEMY_POOL_RECYCLE = 1800
SQLALCHEMY_POOL_PRE_PING = True
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_ECHO = False
APP_MODE = 'TEST'
APP_VERSION = '%s:%s' % (APP_MODE, version.VERSION_STRING)
#---security cleanup  would auto sync security data from code to DB
SECURITY_CLEANUP = False
AUTO_UPDATE_PERM = os.environ.get('AUTO_UPDATE_PERM', False)
