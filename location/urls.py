from django.urls import path
from . import views

app_name = 'location'

urlpatterns = [
    path('',                                  views.liste,              name='liste'),
    path('api/geojson/',                      views.api_geojson,        name='api_geojson'),
    path('api/communes/',                     views.api_communes,       name='api_communes'),
    path('api/quartiers/',                    views.api_quartiers,      name='api_quartiers'),

    path('villes/creer/',                     views.ville_creer,        name='ville_creer'),
    path('villes/<int:pk>/modifier/',         views.ville_modifier,     name='ville_modifier'),
    path('villes/<int:pk>/supprimer/',        views.ville_supprimer,    name='ville_supprimer'),

    path('communes/creer/',                   views.commune_creer,      name='commune_creer'),
    path('communes/<int:pk>/modifier/',       views.commune_modifier,   name='commune_modifier'),
    path('communes/<int:pk>/supprimer/',      views.commune_supprimer,  name='commune_supprimer'),

    path('quartiers/creer/',                  views.quartier_creer,     name='quartier_creer'),
    path('quartiers/<int:pk>/modifier/',      views.quartier_modifier,  name='quartier_modifier'),
    path('quartiers/<int:pk>/supprimer/',     views.quartier_supprimer, name='quartier_supprimer'),
]
