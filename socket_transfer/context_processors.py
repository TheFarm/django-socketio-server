from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static


def socket_settings(request):
    return {
        'WEB_SOCKET_URL': getattr(settings, 'WEB_SOCKET_URL', ''),
        'WEB_SOCKET_SWF_LOCATION': request.build_absolute_uri(static('WebSocketMain.swf')),
    }

