from django.urls import path
from . import views

urlpatterns = [
    path('',            views.calculate,    name='calculate'),
    path('<int:pk>/result/', views.result,  name='result'),
    path('<int:pk>/pdf/',    views.download_pdf, name='download_pdf'),
]