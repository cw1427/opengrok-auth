"""
Created on 2020-11-13.

@author: sc
"""

import click
from . import appbuilder
import logging
from flask_appbuilder.console import cli_app
import datetime

log = logging.getLogger(appbuilder.get_app.config['LOG_NAME'])

@cli_app.command("ssehb")
def sse_heart_beat():
    """The heart beat command to check the invalid subscribe."""
    click.echo('{0}:start sse heart beat polling.'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    with appbuilder.get_app.app_context():
        pass
    click.echo('{0}:finish sse heart beat polling.'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
