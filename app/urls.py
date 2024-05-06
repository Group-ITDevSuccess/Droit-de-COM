from django.urls import path

from . import views

app_name = 'app'
urlpatterns = [
    path('', views.index, name='index'),
    path('load-data/', views.load_data, name='load_data'),
]
