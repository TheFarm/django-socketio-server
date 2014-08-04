from django.conf import settings
from django.db import models

class OnlineUsers(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.user.username