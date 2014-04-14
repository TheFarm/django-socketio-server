import logging
from django.db import connection, transaction
from socketio.namespace import BaseNamespace

logger = logging.getLogger(__name__)


class BaseEsNamespace(BaseNamespace):
    def process_packet(self, packet):
        """If you override this, NONE of the functions in this class
        will be called.  It is responsible for dispatching to
        :meth:`process_event` (which in turn calls ``on_*()`` and
        ``recv_*()`` methods).

        If the packet arrived here, it is because it belongs to this endpoint.

        For each packet arriving, the only possible path of execution, that is,
        the only methods that *can* be called are the following:

        * recv_connect()
        * recv_message()
        * recv_json()
        * recv_error()
        * recv_disconnect()
        * on_*()
        """
        #connection.open()
        packet_type = packet['type']
        if packet_type == 'event':
            logger.debug("Event: %s", str(packet))
            ret = self.process_event(packet)
        elif packet_type == 'message':
            logger.debug("Message: %s", packet['data'])
            ret = self.call_method_with_acl('recv_message', packet,
                                             packet['data'])
        elif packet_type == 'json':
            logger.debug("json: %s", packet['data'])
            ret = self.call_method_with_acl('recv_json', packet,
                                             packet['data'])
        elif packet_type == 'connect':
            logger.debug("Connect: %s", str(packet))
            ret = self.call_method_with_acl('recv_connect', packet)
        elif packet_type == 'error':
            logger.debug("Error: %s", str(packet))
            ret = self.call_method_with_acl('recv_error', packet)
        elif packet_type == 'ack':
            logger.debug("Ack: %s", str(packet['ackId']))
            callback = self.socket._pop_ack_callback(packet['ackId'])
            if not callback:
                logger.error("No such callback for ackId %s", packet['ackId'])

            try:
                ret = callback(*(packet['args']))
            except TypeError, e:
                logger.error("Call to callback function failed %s", str(e.message))
        elif packet_type != 'disconnect':
            logger.warning("Unprocessed packet %s", str(packet))
        elif packet_type == 'disconnect':
            self.disconnect(silent=True)
            logger.debug("Disconnect: %s", str(packet))
            ret = self.call_method_with_acl('recv_disconnect', packet)
        try:
            connection.close()
        except:
            logger.error("CANT CLOSE DATABASE")
        return ret
