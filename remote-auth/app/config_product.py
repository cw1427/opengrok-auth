"""
Created on 2020-12-12.

@author: sc
"""
import os, sys
import version

if os.environ.get('DB_PWD') and os.path.exists(os.environ.get('DB_PWD')):
    with open(pwd_path, 'r') as f:
        db_password = f.read().strip("\n")
    db_user = os.environ.get('DB_USER')
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
    SQLALCHEMY_DATABASE_URI = 'mysql://{0}:{1}@{2}/{3}'.format(db_user, db_password, db_host, db_name)
    #---------------------------------------------------
    # SQLAlchemy pool config setup for mysql
    #---------------------------------------------------
    SQLALCHEMY_POOL_SIZE = 100
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_POOL_PRE_PING = True
    SQLALCHEMY_MAX_OVERFLOW = 10
TEMPLATES_AUTO_RELOAD = False
SQLALCHEMY_ECHO = False
APP_MODE = 'PRO'
APP_VERSION = '%s:%s' % (APP_MODE, version.VERSION_STRING)
#---security cleanup  would auto sync security data from code to DB
SECURITY_CLEANUP = os.environ.get('SECURITY_CLEANUP', False)
AUTO_UPDATE_PERM = os.environ.get('AUTO_UPDATE_PERM', False)
