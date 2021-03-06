from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'aor.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/v1/rule/', include('rule.urls', namespace="rule")),
    url(r'^api/v1/player/', include('player.urls', namespace="player")),
    url(r'^api/v1/game/', include('game.urls', namespace="game")),
    url(r'^ui/', include('ui.urls', namespace="ui")),
)
