from django.urls import path
from . import views

app_name = 'perruque'

urlpatterns = [
    path('',               views.perruque_accueil, name='perruque_accueil'),
    path('produit/<int:pk>/', views.detail_perruque, name='detail_perruque'),

    # API mobile JSON
    path('api/categories/',        views.api_categories_perruque,     name='api_categories'),
    path('api/produits/',          views.api_produits_perruque,       name='api_produits'),
    path('api/produits/<int:pk>/', views.api_produit_detail_perruque, name='api_produit_detail'),
]
