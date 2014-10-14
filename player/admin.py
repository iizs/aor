from django.contrib import admin

from player.models import Player, AccessToken

admin.site.register(Player)
admin.site.register(AccessToken)
