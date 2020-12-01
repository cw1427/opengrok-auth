"""
ATS common models  module.

Created on 2019-3-3.
author: sc.
"""
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import UserExtensionMixin
from flask_appbuilder.models.sqla import SQLA
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from flask_appbuilder.security.sqla.models import User
import json
from sqlalchemy.types import TypeDecorator
from sqlalchemy.sql.sqltypes import Text
import datetime

"""

You can use the extra Flask-AppBuilder fields and Mixin's

AuditMixin will add automatic timestamp of created and modified by who


"""


class SQLAlchemy(SQLA):
    """Customize SQLA class to overwrite the apply_pool_defualts to add pool_pre_ping parameter into SQLA."""

    def apply_pool_defaults(self, app, options):
        """overwrite apply_pool_defaults to customize pool_pre_ping parameter."""
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        app.config.setdefault('SQLALCHEMY_POOL_PRE_PING', False)
        options["pool_pre_ping"] = app.config['SQLALCHEMY_POOL_PRE_PING']


class JsonEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = Text

    def process_bind_param(self, value, dialect):
        """SQLALchemy TypeDecorator process_bind_param overwrite function."""
        if value is None:
            return '{}'
        else:
            return json.dumps(value, default=lambda o: {k: v for k, v in o.__dict__.items()} \
            if not isinstance(o, (datetime.date, datetime.datetime)) else o.strftime('%Y-%m-%d %H:%M:%S.%f'), sort_keys=True)

    def process_result_value(self, value, dialect):
        """SQLALchemy TypeDecorator process_result_value overwrite function."""
        if value is None:
            return {}
        else:
            return json.loads(value)


class UserExtInfo(Model, UserExtensionMixin):
    """Customize user extension entity class."""

    api_key = Column(String(256))
    user_type = Column(String(64))


class MyUser(User):
    """Customize user entity class to extends FAB user entity class."""

    extinfo = relationship('UserExtInfo', backref='user', uselist=False, cascade='all')
