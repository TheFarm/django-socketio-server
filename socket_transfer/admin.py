# -*- coding: utf-8 -*-
from django.contrib import admin
from models import OnlineUsers

class AdminOnlineUsers(admin.ModelAdmin):
    model = OnlineUsers

admin.site.register(OnlineUsers, AdminOnlineUsers)
