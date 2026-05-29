# commandes/urls.py
from django.urls import path
from . import views

app_name = "commandes"

urlpatterns = [
    path("creer/<int:service_id>/", views.creer_commande, name="creer_commande"),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('modifier/<str:code_commande>/', views.modifier_commande, name='modifier_commande'),
    path("creer-pack/<int:texte_id>/", views.creer_commande_pack, name="creer_commande_pack"),  # ✅ Nouveau
    path("texte/<int:texte_id>/", views.creer_commande_texte, name="creer_commande_texte"),
    path("resultats/<str:code_commande>/", views.resultats_commande, name="resultats_commande"),
    
]
