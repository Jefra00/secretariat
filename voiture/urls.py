from django.urls import path
from . import views

app_name = 'voiture'

urlpatterns = [
    path('',                        views.voiture_accueil,      name='voiture_accueil'),
    path('modele/<int:pk>/',        views.detail_voiture,       name='detail_voiture'),
    path('mes-reservations/',       views.mes_reservations,     name='mes_reservations'),
    path('annuler/<int:pk>/',       views.annuler_reservation,  name='annuler_reservation'),

    # API mobile JSON
    path('api/categories/',         views.api_categories_voiture, name='api_categories'),
    path('api/voitures/',           views.api_voitures,           name='api_voitures'),
    path('api/voitures/<int:pk>/',  views.api_voiture_detail,     name='api_voiture_detail'),
    path('api/reserver/<int:pk>/',  views.api_reserver_voiture,   name='api_reserver'),
]
