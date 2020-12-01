"""
Created on 2018-2-22.

@author: sc
"""
from flask_appbuilder.filters import TemplateFilters, app_template_filter
import json
import logging

log = logging.getLogger(__name__)


def renderNone(v):
    return '' if not v else v


def autoSplit(v, s='|'):
    v = renderNone(v)
    result = ''
    if s in v:
        v_list = v.split(s)
        for i, item in enumerate(v_list):
            if i and i % 5 == 0:
                result = "{0}<br/>{1}".format(result, item)
            else:
                result = "{0}&nbsp{1}".format(result, item)
    else:
        result = v
    return result


class MyTemplateFilters(TemplateFilters):

    def __init__(self, app, security_manager):
        super(MyTemplateFilters, self).__init__(app, security_manager)

    @app_template_filter('render_none')
    def render_none(self, v):
        return renderNone(v)

    @app_template_filter('json_load')
    def json_load(self, v):
        try:
            s_json = json.loads(v)
            return s_json
        except Exception as e:
            return v


