from django.urls import path
from . import views

urlpatterns = [
    path("upload_image/", views.ImageUploadAPIView.as_view()),
    path("dishes/", views.DishCreateAPIView.as_view()),
    path("dishes/list/", views.DishListAPIView.as_view()),
    path("categories/", views.CategoryListAPIView.as_view(), name="category-list"),
    path('orders/', views.create_order, name='create_order'),
    path('commandes/', views.order_list, name='order_list'),
    path('<int:order_id>/status/', views.update_order_status, name='order_update_status'),
    path('<int:order_id>/ingredients/', views.order_ingredients, name='order_ingredients'),
    path('<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path('restaurants/', views.RestaurantListAPIView.as_view(), name='restaurants-list'),
    path('detail_restaurants/<int:pk>/', views.RestaurantDetailAPIView.as_view(), name='restaurant-detail'),
    path('restaurants/<int:pk>/toggle-ouvert/', views.toggle_restaurant_ouvert, name='restaurant-toggle-ouvert'),
    path('top-dishes/', views.TopDishesAPIView.as_view(), name='top-dishes'),
    path('dishes/<int:dish_id>/rate/', views.rate_dish, name='rate-dish'),
    path('chatbot/', views.chatbot, name='chatbot'),

    # ── Gestion commandes (web admin) ─────────────────────────────────────────
    path('gestion/', views.gestion_commandes, name='gestion_commandes'),
    path('gestion/<int:order_id>/avancer/', views.avancer_statut, name='avancer_statut'),

    # ── Inscription restaurant (admin web) ───────────────────────────────────
    path('inscription/', views.inscription_restaurant, name='inscription_restaurant'),

    # ── Système Livreur ──────────────────────────────────────────────────────
    path('livreur/commandes/', views.commandes_disponibles, name='commandes-disponibles'),
    path('livreur/commandes/<int:order_id>/reserver/', views.reserver_commande, name='reserver-commande'),
    path('livreur/valider-qr/', views.valider_qr, name='valider-qr'),
    path('livreur/position/', views.update_livreur_position, name='livreur-position'),
    path('commandes/<int:order_id>/livreur-position/', views.livreur_position_for_order, name='livreur-position-order'),
    path('livreur/mes-livraisons/', views.mes_livraisons, name='mes-livraisons'),
]
