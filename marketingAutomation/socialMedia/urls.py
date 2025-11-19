from django.urls import path
from . import views 

urlpatterns = [
    path('', views.socialMedia, name='socialMedia'),
]
