import logging
from django.contrib.auth import get_user_model
from socketio.namespace import BaseNamespace
from django.core.cache import cache
from django.db import connection, transaction

logger = logging.getLogger(__name__)


class BaseEsNamespace(BaseNamespace):
    def process_packet(self, packet):
        with transaction.atomic():
            logger.info('Received packet %s', packet)
            self.connect_user(self.get_current_user())
            ret = super(BaseEsNamespace, self).process_packet(packet)
        try:
            connection.close()
        except:
            logger.error("Error closing connection after processing packet")
        return ret

    def on_manual_disconnect(self, data):
        logger.info('Manual disconnect from user %s in session %s', self.get_current_user(), self.socket.sessid)
        self.remove_user_by_session(self.socket.sessid)
        self.recv_disconnect()

    def send_to_users(self, users, event, args={}):
        packet = self.build_packet(event, args)

        logger.info('Sending packet %s to users %s', packet, users)

        if type(users) is list:
            for user in users:
                session = self.get_session_by_user(user)
                self.send_packet(session, packet)
        else:
            session = self.get_session_by_user(users)
            self.send_packet(session, packet)

    def send_to_namespace(self, event, args={}):
        packet = self.build_packet(event, args)

        logger.info('Sending packet %s to namespace %s', packet, self.ns_name)

        for user in self.get_users():
            self.send_packet(self.get_session_by_user(user), packet)

    def send_packet(self, session, packet):
        for sessid, socket in self.iterate_sockets():
                if sessid == session:
                    socket.send_packet(packet)

    def connect_user(self, user):
        users = self.get_users()

        if user and self.socket.sessid:
            for session_user in users:
                if session_user.pk == user.pk:
                    self.update_user_session(user, self.socket.sessid)

            if not self.get_user_by_session(self.socket.sessid):
                user.sessions = [self.socket.sessid]
                users.append(user)
                self.set_users(users)
                logger.info('Connected user %s to namespace %s with session %s', user, self.ns_name, self.socket.sessid)

    def set_users(self, users):
        cache.set(self.get_cache_name('users'), users)

    def get_users(self):
        users = cache.get(self.get_cache_name('users'), [])
        filtered_users = self.remove_offline_users(users)
        self.set_users(filtered_users)

        return filtered_users

    def remove_offline_users(self, users):
        sessions = self.get_sessions()

        for user in users:
            for session in user.sessions:
                if session not in sessions:
                    user.sessions.remove(session)
                    logger.info('Session %s from user %s is offline', session, user)

                    if len(user.sessions) < 1:
                        users.remove(user)
                        logger.info('All session for user %s are offline', user)

        return users

    def remove_user_by_session(self, sessid):
        users = self.get_users()

        for user in users:
            for session in user.sessions:
                if session == sessid:
                    user.sessions.remove(session)
                    logger.info('Removed session %s from user %s', session, user)

                    if len(user.sessions) < 1:
                        users.remove(user)
                        logger.info('Removed user %s by last session', user)

        self.set_users(users)

    def get_user_by_session(self, sessid):
        for user in self.get_users():
            for session in user.sessions:
                if session == sessid:
                    return user

        return False

    def get_session_by_user(self, user):
        try:
            return user.sessions[-1]
        except (AttributeError, IndexError):
            for cache_user in self.get_users():
                if cache_user.pk == user.pk:
                    if len(cache_user.sessions) > 0:
                        return cache_user.sessions[-1]
                    else:
                        logger.warning('User %s has no active sessions', cache_user)

    def update_user_session(self, user_add, session):
        users = self.get_users()

        for user in users:
            if user.pk == user_add.pk:
                if not user.sessions:
                    user.sessions = []
                if session not in user.sessions:
                    user.sessions.append(session)
                    logger.info('Updated user %s to session %s', user, session)

        self.set_users(users)

    def add_session_to_user(self, user_add, session):
        users = self.get_users()

        for user in users:
            if user.pk == user_add.pk:
                if session not in user.sessions:
                    user.sessions.append(session)
                    logger.info('Added session %s to user %s', session, user)

        self.set_users(users)

    def get_cache_name(self, name):
        return self.ns_name + '_' + name

    def get_sessions(self):
        sessions = []

        for sessid, socket in self.iterate_sockets():
            sessions.append(sessid)

        return sessions

    def iterate_sockets(self):
        return self.socket.server.sockets.iteritems()

    def recv_disconnect(self):
        user = self.get_current_user()

        try:
            connection.close()
        except:
            logger.error("Error closing connection after disconnect")

        self.disconnect(silent=True)

        if user:
            logger.info('User %s disconnected', user)

    def build_packet(self, event, args, namespace=None):
        if not namespace:
            namespace = self.ns_name

        pkt = dict(
            type='event',
            name=event,
            args=args,
            endpoint=namespace
        )

        return pkt

    def get_current_user(self):
        try:
            from django.conf import settings as django_settings
            from Cookie import SimpleCookie
            from django.contrib.auth import SESSION_KEY
            from django.contrib.auth.models import User
            from django.contrib.sessions.models import Session
            from django.core.exceptions import ObjectDoesNotExist

            cookie = SimpleCookie(self.environ.get("HTTP_COOKIE", ""))
            cookie_name = django_settings.SESSION_COOKIE_NAME
            session_key = cookie[cookie_name].value
            session = Session.objects.get(session_key=session_key)
            user_id = session.get_decoded().get(SESSION_KEY)
            user = get_user_model().objects.get(pk=user_id)

            return user
        except (ImportError, KeyError, ObjectDoesNotExist):
            return False