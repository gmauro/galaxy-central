"""
The Galaxy web application.
"""

from framework import expose, json, json_pretty, require_login, require_admin, url_for, error, form, FormBuilder
from framework.base import httpexceptions

