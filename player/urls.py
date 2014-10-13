from django.conf.urls import patterns, url

from player import views

urlpatterns = patterns('',
    url(r'^create/$', views.create),
    url(r'^get/$', views.get),
)
