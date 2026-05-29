from django.urls import path
from . import views

app_name = "paiements"

urlpatterns = [
    path('initier/', views.paiement_initier, name='paiement_initier'),
]
