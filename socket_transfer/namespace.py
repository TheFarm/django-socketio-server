import logging
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from socketio.namespace import BaseNamespace
from django.core.cache import cache
from django.db import connection, transaction
from socket_transfer.models import OnlineUsers

logger = logging.getLogger(__name__)


class BaseEsNamespace(BaseNamespace):
    def process_packet(self, packet):
        with transaction.atomic():
            self.connect_user(self.get_current_user())
            ret = super(BaseEsNamespace, self).process_packet(packet)
        try:
            connection.close()
        except:
            logger.error("CANT CLOSE DATABASE")
        return ret

    def on_manual_disconnect(self, data):
        self.remove_user_by_session(self.socket.sessid)
        self.recv_disconnect()

    def send_to_namespace(self, event, args):
        args['event'] = event
        packet = self.build_packet(args)

        for sessid, socket in self.iterate_sockets():
            socket.send_packet(packet)

    def connect_user(self, user):
        users = self.get_users()

        if user:
            for session_user in users:
                if session_user.pk == user.pk:
                    print "session user detected %s" % session_user
                    self.update_session_for_user(user, self.socket.sessid)

            if not self.get_user_by_session(self.socket.sessid):
                user.sessions = [self.socket.sessid]
                users.append(user)
                self.set_users(users)

    def set_users(self, users):
        cache.set(self.get_cache_name('users'), users)

    def get_users(self):
        users = cache.get(self.get_cache_name('users'), [])
        filtered_users = self.filter_offline_users(users)
        self.set_users(filtered_users)

        return filtered_users

    def filter_offline_users(self, users):
        sessions = self.get_sessions()

        for user in users:
            for session in user.sessions:
                if session not in sessions:
                    print "removed session %s from user %s" % (session, user)
                    user.sessions.remove(session)

                    if len(user.sessions) < 1:
                        print "removed user by last session %s" % user
                        users.remove(user)

        return users

    def remove_user_by_session(self, sessid, force=False):
        users = self.get_users()

        for user in users:
            for session in user.sessions:
                if session == sessid:
                    print "removed session %s from user %s" % (session, user)
                    user.sessions.remove(session)

                    if len(user.sessions) < 1 or force:
                        print "removed user by last session %s" % user
                        users.remove(user)
                        o_user = OnlineUsers.objects.filter(user=user)
                        for user in o_user:
                            user.delete()

        self.set_users(users)

    def get_user_by_session(self, sessid):
        for user in self.get_users():
            for session in user.sessions:
                if session == sessid:
                    return user

        return False

    def update_session_for_user(self, user_add, session):
        users = self.get_users()

        for user in users:
            if user.pk == user_add.pk:
                print user.sessions
                user.sessions = [session]
                OnlineUsers.objects.get_or_create(user=user_add)

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
        try:
            connection.close()
        except:
            logger.error('cant close db')

        self.disconnect(silent=True)


    def build_packet(self, args):
        pkt = dict(
            type='event',
            name='receive',
            args=args,
            endpoint=self.ns_name
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