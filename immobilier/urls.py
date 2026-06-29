from django.urls import path
from . import views

app_name = 'immobilier'

urlpatterns = [
    # ── Pages web ──────────────────────────────────────────────────────────
    path('',                     views.accueil_immobilier, name='accueil'),
    path('bien/<int:pk>/',       views.detail_immobilier,  name='detail'),
    path('mes-visites/',         views.mes_visites,        name='mes_visites'),

    # ── API JSON (Flutter) ─────────────────────────────────────────────────
    path('api/biens/',                   views.api_biens,          name='api_biens'),
    path('api/biens/<int:pk>/',          views.api_bien_detail,    name='api_bien_detail'),
    path('api/visiter/<int:pk>/',        views.api_demande_visite, name='api_demande_visite'),
]
