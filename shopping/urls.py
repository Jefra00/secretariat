from django.urls import path
from . import views

app_name = 'shopping'

urlpatterns = [
    path('',              views.shopping_accueil,              name='shopping_accueil'),
    path('produit/<int:pk>/', views.detail_produit_shopping,   name='detail_produit_shopping'),

    # API mobile JSON
    path('api/categories/',        views.api_categories_shopping,      name='api_categories'),
    path('api/produits/',          views.api_produits_shopping,        name='api_produits'),
    path('api/produits/<int:pk>/', views.api_produit_detail_shopping,  name='api_produit_detail'),
]
