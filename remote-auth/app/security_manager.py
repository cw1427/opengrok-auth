"""
AUTHAPP customize security manager  module.

Created on 2020-11-13.
author: sc.
"""
import logging
from flask_login import current_user
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.const import \
                    LOGMSG_ERR_SEC_AUTH_LDAP, \
                    LOGMSG_ERR_SEC_AUTH_LDAP_TLS, \
                    LOGMSG_WAR_SEC_NOLDAP_OBJ, \
                    LOGMSG_WAR_SEC_LOGIN_FAILED
from flask_appbuilder.security.views import UserDBModelView, AuthLDAPView
from flask_appbuilder.security.forms import LoginForm_db, LoginForm_oid, ResetPasswordForm, UserInfoEdit
from app.models import MyUser, UserExtInfo
from flask_login import login_required
from flask_appbuilder.baseviews import expose, BaseView
from flask import redirect, session, url_for, request, g, jsonify
from flask_appbuilder.actions import action
from flask_babel import lazy_gettext
from app.formats import MyTemplateFilters
from werkzeug.contrib.sessions import generate_key
from flask.helpers import make_response
from sqlalchemy.sql.functions import func
from functools import wraps
from flask.globals import current_app
import json
import config
from werkzeug.security import check_password_hash
from urllib import parse

log = logging.getLogger(__name__)


def login_required_api(func):
    """decorate for the function to request login and response the json code."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return make_response(jsonify({'msg': 'lost session, need to relogin', 'session': \
                                          request.cookies.get(config.config.SESSION_COOKIE_NAME)}), 302)
        return func(*args, **kwargs)
    return decorated_view


class UserApikeyView(BaseView):
    """UserApikeyView the APIkey page view class."""

    route_base = '/userapikey'
    list_template = "appbuilder/security/userapikey_list.html"

    @expose('/list', methods=['GET', 'POST'])
    @login_required
    def list(self):
        """Retrieve the current user API key RESTAPI method."""
        return self.render_template(self.list_template, data={'apikey': g.user.extinfo.api_key \
                                                               if g.user.extinfo is not None else None})

    @expose('/api/gen', methods=['GET', 'POST'])
    @login_required_api
    def apikeygen(self):
        """User apikey generation RESTAPI method."""
        pk = g.user.id
        apikey = generate_key()
        user_ext = UserExtInfo()
        user_ext.api_key = apikey
        user_ext.id = pk
        count = self.appbuilder.get_session.query(func.count('*')).select_from(UserExtInfo).filter_by(id=pk).scalar()
        if count:
            self.appbuilder.get_session.query(UserExtInfo).filter_by(id=pk).update({'api_key': apikey})
        else:
            self.appbuilder.get_session.add(user_ext)
        self.appbuilder.get_session.commit()
        return jsonify({'code': 200, 'msg': 'Success', "apikey": apikey})


class UserLDAPModelView(UserDBModelView):
    """UserLDAPModelView the UserDBModel customize extended class."""

    @expose('/userinfo/')
    @login_required
    def userinfo(self):
        """The current user basic info retrieve RESTAPI method."""
        actions = {}
        actions['resetmypassword'] = self.actions.get('resetmypassword')
        actions['userinfoedit'] = self.actions.get('userinfoedit')

        item = self.datamodel.get(g.user.id, self._base_filters)
        widgets = self._get_show_widget(g.user.id, item, actions=actions, show_fieldsets=self.user_show_fieldsets)
        self.update_redirect()
        return self.render_template(self.show_template,
                               title=self.user_info_title,
                               widgets=widgets,
                               appbuilder=self.appbuilder,
        )

    def post_add(self, item):
        """The user addition post method."""
        user_ext = UserExtInfo()
        user_ext.user_type = self.appbuilder.get_app.config['USER_TYPE_LOCAL']
        user_ext.id = item.id
        self.datamodel.session.add(user_ext)
        self.datamodel.session.commit()


class MyAuthLDAPView(AuthLDAPView):
    """
    overwrite the basic AuthLDAPView to do the remote auth
    """
    login_template = 'appbuilder/general/security/login_ldap.html'

    @expose('/login/', methods=['GET'])
    def login(self):
        if g.user is not None and g.user.is_authenticated:
            remote_from = request.cookies.get('remote_login')
            url_path = parse.urlparse(remote_from)
            remote_base_url = "{0}://{1}".format(url_path.scheme, url_path.netloc)
            return redirect(remote_base_url)
        form = LoginForm_db()
        return self.render_template(self.login_template,
                               title=self.title,
                               form=form,
                               appbuilder=self.appbuilder)


class IndexView(BaseView):
    """A index View to render the VUE template."""

    route_base = ''
    default_view = 'index'
    original_index_template = 'appbuilder/index.html'
    vue_index_template = 'vue/index.html'

    @expose('/')
    def index(self):
        """The default index page action method."""
        self.update_redirect()
        ui_type = session.get('ui', 'original')
        return self.render_template(getattr(self, '{0}_index_template'.format(ui_type)))

    def _json_load(self, v):
        try:
            s_json = json.loads(v)
            return s_json
        except Exception:
            return v


class SecurityManager(SecurityManager):
    """Security manager want to overwrite the basic manager's  auth_user_db and auth_user_ldap method."""

    userldapmodelview = UserLDAPModelView
    authldapview = MyAuthLDAPView
    user_model = MyUser
    userapikeyview = UserApikeyView

    def __init__(self, appbuilder):
        """The securityManager initial method."""
        super(SecurityManager, self).__init__(appbuilder)
        MyTemplateFilters(appbuilder.get_app, self)

    def auth_user_ldap(self, username, password, load_request=False):
        """overwrite it, first check if can use auth db."""
        if username is None or username == "":
            return None
        user = self.find_user(username=username)
        if user is not None and (not user.is_active):
            return None
        if user:
            if user.extinfo:
                if user.extinfo.user_type == self.appbuilder.get_app.config['USER_TYPE_LDAP']:
                    return self._auth_user_ldap(username, password, load_request, user)
                elif user.extinfo.user_type == self.appbuilder.get_app.config['USER_TYPE_LOCAL']:
                    return self.auth_user_db(username, password, user)
                else:
                    return None
            else:
                # no extinfo
                user.extinfo = UserExtInfo()
                user.extinfo.id = user.id
                user.extinfo.user_type = self.appbuilder.get_app.config['USER_TYPE_LDAP']
                res = self._auth_user_ldap(username, password, load_request, user)
                if not res:
                    user.extinfo.user_type = self.appbuilder.get_app.config['USER_TYPE_LOCAL']
                    return self.auth_user_db(username, password, user)
                return res
        else:
            # none local user try first LDAP login
            return self._auth_user_ldap(username, password, load_request)

    def auth_user_db(self, username, password, user=None):
        """
            Method for authenticating user, auth db style

            :param username:
                The username or registered email address
            :param password:
                The password, will be tested against hashed password on db
        """
        if username is None or username == "":
            return None
        if not user:
            user = self.find_user(username=username)
            if user is None:
                user = self.find_user(email=username)
        if user is None or (not user.is_active):
            log.info(LOGMSG_WAR_SEC_LOGIN_FAILED.format(username))
            return None
        elif check_password_hash(user.password, password):
            self.update_user_auth_stat(user, True)
            return user
        else:
            self.update_user_auth_stat(user, False)
            log.info(LOGMSG_WAR_SEC_LOGIN_FAILED.format(username))
            return None

    def _auth_user_ldap(self, username, password, load_request, user=None):
        """Method for authenticating user, auth LDAP style."""
        if username is None or username == "":
            return None
        if not user:
            user = self.find_user(username=username)
            if user is None:
                user = self.find_user(email=username)
        if user is not None and (not user.is_active):
            return None
        else:
            try:
                import ldap
            except:
                raise Exception("No ldap library for python.")
            try:
                if self.auth_ldap_allow_self_signed:
                    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
                con = ldap.initialize(self.auth_ldap_server)
                con.set_option(ldap.OPT_REFERRALS, 0)
                if self.auth_ldap_use_tls:
                    try:
                        con.start_tls_s()
                    except Exception:
                        log.info(LOGMSG_ERR_SEC_AUTH_LDAP_TLS.format(self.auth_ldap_server))
                        return None
                # Authenticate user
                if not self._bind_ldap(ldap, con, username, password):
                    if user:
                        self.update_user_auth_stat(user, False)
                    log.info(LOGMSG_WAR_SEC_LOGIN_FAILED.format(username))
                    return None
                # If user does not exist on the DB and not self user registration, go away
                if not user and not self.auth_user_registration:
                    return None
                # User does not exist, create one if self registration.
                elif not user and self.auth_user_registration:
                    new_user = self._search_ldap(ldap, con, username)
                    if not new_user:
                        log.warning(LOGMSG_WAR_SEC_NOLDAP_OBJ.format(username))
                        return None
                    ldap_user_info = new_user[0][1]
                    if self.auth_user_registration and user is None and not load_request:
                        user = self.add_user(
                            username=username,
                            first_name=self.ldap_extract(ldap_user_info, self.auth_ldap_firstname_field, username),
                            last_name=self.ldap_extract(ldap_user_info, self.auth_ldap_lastname_field, username),
                            email=self.ldap_extract(ldap_user_info, self.auth_ldap_email_field, username + '@email.notfound'),
                            role=self.find_role(self.auth_user_registration_role)
                        )
                        #----also add its userinfo view permission and the extension info
                        user_ext = UserExtInfo()
                        user_ext.user_type = self.appbuilder.get_app.config['USER_TYPE_LDAP']
                        user_ext.id = user.id
                        self.get_session.add(user_ext)
                        self.get_session.commit()
                        #----add the userinfo permission on it

                if user:
                    self.update_user_auth_stat(user)
                return user

            except ldap.LDAPError as e:
                if hasattr(e, 'message') and type(e.message) == dict and 'desc' in e.message:
                    log.error(LOGMSG_ERR_SEC_AUTH_LDAP.format(e.message['desc']))
                    return None
                else:
                    log.error(e)
                    return None

    def _bind_ldap(self, ldap, con, username, password):
        """ldap bind method."""
        try:
            indirect_user = self.auth_ldap_bind_user
            if indirect_user:
                indirect_password = self.auth_ldap_bind_password
                con.bind_s(indirect_user, indirect_password)
                user = self._search_ldap(ldap, con, username)
                if user:
                    log.debug("LDAP got User {0}".format(user))
                    # username = DN from search
                    username = user[0][0]
                else:
                    return False
            if self.auth_ldap_username_format:
                username = self.auth_ldap_username_format % username
            if self.auth_ldap_append_domain:
                username = username + '@' + self.auth_ldap_append_domain
            # user = self._search_ldap(ldap, con, username)
            if indirect_user:
                con.bind_s(username, password)
            else:
                con.bind_s("{0}={1},{2}".format(self.auth_ldap_uid_field, username, self.auth_ldap_search), password)
            log.debug("LDAP bind OK: {0}".format(username))
            return True
        except ldap.INVALID_CREDENTIALS:
            return False

    def register_views(self):
        """Overwrite the register views about FAB."""
        super(SecurityManager, self).register_views()
        self.appbuilder.add_view_no_menu(self.userapikeyview())
        self.lm.login_view = "{0}.{1}".format(self.auth_view.__class__.__name__, 'login')

    def has_access(self, permission_name, view_name):
        """Check if current user or public has access to view or menu."""
        if current_user.is_authenticated:
            #----special permission bypass
            if permission_name in self.appbuilder.get_app.config['COMMON_PERMISSIONS']:
                return True
            elif permission_name in self.appbuilder.get_app.config['COMMON_LOCAL_USER_PERMISSION'] and g.user.extinfo:
                return True if g.user.extinfo.user_type == self.appbuilder.get_app.config['USER_TYPE_LOCAL'] else False
            #----special view_name bypass
            elif view_name in self.appbuilder.get_app.config['COMMON_LOCAL_USER_VIEW'] and  g.user.extinfo:
                return True if g.user.extinfo.user_type == self.appbuilder.get_app.config['USER_TYPE_LOCAL'] else False
            else:
                return self._has_view_access(g.user, permission_name, view_name)
        else:
            return self.is_item_public(permission_name, view_name)
