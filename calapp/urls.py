from django.urls import path
from . import views

urlpatterns = [
        path('', views.index, name="index"),
        path("<int:month>/<int:year>/<int:forward>", views.month, name="month"),
        ]
