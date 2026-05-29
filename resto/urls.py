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

]
