from django.conf.urls import patterns, url

from game import views

urlpatterns = patterns('',
    url(r'^create/$', views.create),
    #url(r'^get/$', views.get),
    #url(r'^registerToken/$', views.registerToken),
)
