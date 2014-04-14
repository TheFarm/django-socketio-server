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

    WEB_SOCKET_SERVER = "46.21.104.50"
    WEB_SOCKET_PORT = 8081
    WEB_SOCKET_URL = "%s:%d" % (WEB_SOCKET_SERVER, WEB_SOCKET_PORT)

3. Add a sockets.py (with a namespace) to the app that needs to be connected for realtime data.

4. Create a client script that talks through the socket (I rekomend using angular-socket-io https://github.com/btford/angular-socket-io)

5. Start socketserver for testing (not recomended in production environment): ./manage.py socket_runserver
