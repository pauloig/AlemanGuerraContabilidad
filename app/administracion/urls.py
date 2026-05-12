from turtle import home
from django.contrib import admin
from django.urls import path, include
from . import views
from administracion import views

urlpatterns = [
     
     # URLs para Periodos
    path('periodos/', views.periodo_list, name='periodo_list'),
    path('periodos/crear/', views.periodo_create, name='periodo_create'),
    path('periodos/editar/<int:pk>/', views.periodo_edit, name='periodo_edit'),
    path('periodos/eliminar/<int:pk>/', views.periodo_delete, name='periodo_delete'),
    
    
    ]