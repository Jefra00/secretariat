from django.urls import path
from . import views

app_name = 'marche'

urlpatterns = [
    # Marketplace publique
    path('',                          views.accueil_marche,    name='accueil_marche'),
    path('produit/<uuid:pk>/',        views.detail_produit,    name='detail_produit'),
    path('panier/',                   views.panier,            name='panier'),
    path('inscription/',              views.inscription_vendeur, name='inscription_vendeur'),

    # Gestion vendeurs
    path('vendeurs/',                 views.vendeur_liste,     name='vendeur_liste'),
    path('vendeurs/creer/',           views.vendeur_creer,     name='vendeur_creer'),
    path('vendeurs/<int:pk>/modifier/', views.vendeur_modifier, name='vendeur_modifier'),
    path('vendeurs/<int:pk>/supprimer/', views.vendeur_supprimer, name='vendeur_supprimer'),

    # API web
    path('api/users/',                views.api_users_search,  name='api_users_search'),

    # API mobile JSON
    path('api/categories/',           views.api_categories,         name='api_categories'),
    path('api/produits/',             views.api_produits,           name='api_produits'),
    path('api/produits/<uuid:pk>/',   views.api_produit_detail,     name='api_produit_detail'),
]
