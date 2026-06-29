from django.urls import path
from . import views

app_name = 'quicaillerie'

urlpatterns = [
    path('', views.accueil_quicaillerie, name='accueil'),
    path('produit/<int:pk>/', views.detail_quicaillerie, name='detail'),
    path('panier/', views.panier_quicaillerie, name='panier'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/produits/', views.api_produits, name='api_produits'),
    path('api/produits/<int:pk>/', views.api_produit_detail, name='api_produit_detail'),
]
