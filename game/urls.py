from django.conf.urls import patterns, url

from game import views

urlpatterns = patterns('',
    url(r'^create/$', views.create),
    url(r'^list/$', views.list),
    url(r'^delete/$', views.delete),
    #url(r'^registerToken/$', views.registerToken),
)
