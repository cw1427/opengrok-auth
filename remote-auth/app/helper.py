"""
Created on 2019-12-24

@author: sc
"""

import ldap
from app import appbuilder
import logging

log = logging.getLogger(appbuilder.get_app.config['LOG_NAME'])
from flask_appbuilder.const import LOGMSG_ERR_SEC_AUTH_LDAP_TLS

def ldap_check(core_id):
    """check core id in ids"""
    con = ldap.initialize(appbuilder.sm.auth_ldap_server)
    con.set_option(ldap.OPT_REFERRALS, 0)
    if appbuilder.sm.auth_ldap_use_tls:
        try:
            con.start_tls_s()
        except Exception:
            log.info(LOGMSG_ERR_SEC_AUTH_LDAP_TLS.format(appbuilder.sm.auth_ldap_server))
            return None
    filter_str = "({0}={1})".format(appbuilder.sm.auth_ldap_uid_field, core_id.strip())
    filter_str = "(|{0})".format(filter_str)
    users = con.search_s(appbuilder.sm.auth_ldap_search,
            ldap.SCOPE_SUBTREE,
            filter_str,
            [appbuilder.sm.auth_ldap_uid_field,
             appbuilder.sm.auth_ldap_firstname_field,
             appbuilder.sm.auth_ldap_lastname_field,
             appbuilder.sm.auth_ldap_email_field
            ])
    if users and len(users) > 0:
        return users[0]
    else:
        return None

def is_admin(roles):
    """help function to check if is admin role"""
    for role in roles:
        if appbuilder.get_app.config['AUTH_ROLE_ADMIN'] == role.name:
            return True
    return False
