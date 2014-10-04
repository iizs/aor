from django.conf.urls import patterns, url

from ui import views

urlpatterns = patterns('',
    url(r'^map/$', views.showMap),
)
