from django.conf.urls import patterns, url

from rule import views

urlpatterns = patterns('',
    url(r'^/getMap/$', views.getMap),
)
