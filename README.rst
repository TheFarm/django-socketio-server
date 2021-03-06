=====
Django Socket Transfer
=====

This is a simple implementation of gevent-socketIO for django usage.
https://github.com/abourget/gevent-socketio

Features
--------
* Database connection closes after call
* Imports namespaces from apps automatically

Quick start
-----------

1. Add "socket_transfer" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'socket_transfer',
    )

2. Add the settings for websocket ip and port in your settings.py, like this::

    WEB_SOCKET_SERVER = "127.0.0.1"
    WEB_SOCKET_PORT = 8081
    WEB_SOCKET_URL = "%s:%d" % (WEB_SOCKET_SERVER, WEB_SOCKET_PORT)

3. Add a sockets.py (with a namespace) to the app that needs to be connected for realtime data::

    @namespace("/user")
    class UserNamespace(BaseEsNamespace, RoomsMixin, BroadcastMixin):
        def recv_connect(self):
            user = get_user(self.environ)
	    # Code 


        def recv_disconnect(self, silent=False):
            user = get_user(self.environ)
	    # Code

        def on_join(self, data):
            self.join(str(data['room']))

        def on_leave(self, data):
            self.leave(str(data['room']))

        def on_update(self, data):
            self.emit_to_room(
                str(data['room']),
                'update',
                data['pk']
            )

4. Create a client script that talks through the socket (I recommend using angular-socket-io https://github.com/btford/angular-socket-io)

5. Start socketserver for testing (not recommend in production environment): ./manage.py socket_runserver
