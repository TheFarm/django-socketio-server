import logging
from django.conf import settings
from gevent.monkey import patch_all
from socketio.server import SocketIOServer

patch_all()
from gevent import spawn

from django.core.management.base import BaseCommand
from esportal.socket_transfer.socket_server import app

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        server = SocketIOServer((settings.WEB_SOCKET_SERVER, settings.WEB_SOCKET_PORT), app)
        logger.info("Socket.io listeing on %s:%s", settings.WEB_SOCKET_SERVER, settings.WEB_SOCKET_PORT)
        spawn(server.serve_forever).join()