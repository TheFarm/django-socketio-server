import logging
from django.conf import settings
from gevent.monkey import patch_all
from socketio.server import SocketIOServer

patch_all()
from gevent import spawn

from django.core.management.base import BaseCommand
from socket_transfer.socket_server import app

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        server = settings.SOCKET_SERVER_SETTINGS.get('SERVER', '127.0.0.1')
        port = settings.SOCKET_SERVER_SETTINGS.get('PORT', 1280)
        server = SocketIOServer(server, port, app)
        logger.info("Socket.io listeing on %s:%s", server, port)
        spawn(server.serve_forever).join()