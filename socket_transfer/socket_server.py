from Cookie import SimpleCookie
from importlib import import_module
import logging
from django.contrib.auth import get_user_model

from socketio import socketio_manage

SOCKETIO_NS = {}

LOADING_SOCKETIO = False

logger = logging.getLogger(__name__)


def autodiscover():
    """
Auto-discover INSTALLED_APPS sockets.py modules and fail silently when
not present. NOTE: socketio_autodiscover was inspired/copied from
django.contrib.admin autodiscover
"""
    global LOADING_SOCKETIO
    if LOADING_SOCKETIO:
        return
    LOADING_SOCKETIO = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:

        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('sockets', app_path)
        except ImportError:
            continue

        import_module("%s.sockets" % app)

    LOADING_SOCKETIO = False


class namespace(object):
    def __init__(self, name=''):
        self.name = name

    def __call__(self, handler):
        SOCKETIO_NS[self.name] = handler
        logger.info("Handler: %s", self.name)
        return handler


def get_user(environ):
    try:
        from django.conf import settings as django_settings
        from django.contrib.auth import SESSION_KEY
        from django.contrib.auth.models import User
        from django.contrib.sessions.models import Session
        from django.core.exceptions import ObjectDoesNotExist

        cookie = SimpleCookie(environ.get("HTTP_COOKIE", ""))
        cookie_name = django_settings.SESSION_COOKIE_NAME
        session_key = cookie[cookie_name].value
        session = Session.objects.get(session_key=session_key)
        user_id = session.get_decoded().get(SESSION_KEY)
        logger.debug("FETCHING USER %s", user_id)
        user = get_user_model().objects.get(pk=user_id)
        return user
    except (ImportError, KeyError, ObjectDoesNotExist):
        return False


def authorized(environ):
    return True if get_user(environ) else False


class Application(object):
    def __init__(self):
        self.buffer = []
        # Dummy request object to maintain state between Namespace
        # initialization.
        self.request = {
            'nicknames': [],
        }

    def __call__(self, environ, start_response):
        autodiscover()
        try:
            socketio_manage(environ, SOCKETIO_NS, self.request)
        except KeyError, e:
            logger.error("GOT KEYERROR!", e.message)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


app = Application()
