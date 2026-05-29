from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import Dish, Ingredient, DishIngredient, Category,Order,OrderItem,OrderItemIngredientChoice
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from .services.sms_service import send_order_status_sms
from twilio.rest import Client
from .models import Restaurant
from .serializers import RestaurantDetailSerializer
import qrcode
import base64
from io import BytesIO
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
import os
from django.conf import settings

 

def order_list(request):
    orders = Order.objects.prefetch_related(
        'items__ingredient_choices',
        'items__dish'
    ).order_by('-created_at')

    return render(request, 'orders/order_list.html', {'orders': orders})


def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)

    qr = qrcode.make(order.qr_code)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "orders/order_detail.html", {
        "order": order,
        "items": order.items.all(),
        "qr_code": qr_base64
    })

TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_NUMBER = settings.TWILIO_WHATSAPP_NUMBER

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    statuses = Order.STATUS_CHOICES

    if request.method == "POST":
        new_status = request.POST.get("status")
        order.status = new_status
        order.save()

        # 🔥 Construire message complet
        if order.phone_number:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            # Récupérer les items de la commande
            items = OrderItem.objects.filter(order=order)

            # Construire la liste des plats
            items_text = ""
            for item in items:
                items_text += f"- {item.dish.title} × {item.quantity} → {item.line_price} FCFA\n"

            # Message WhatsApp
            message_body = (
                f"Bonjour ! Votre commande est maintenant : {order.get_status_display()}.\n\n"
                f"📍 Adresse : {order.delivery_address}\n"
                f"📞 Téléphone : {order.phone_number}\n\n"
                f"🛒 Détails :\n"
                f"{items_text}\n"
                f"💰 Sous-total : {order.subtotal} FCFA\n"
                f"🚚 Livraison : {order.delivery_fee} FCFA\n"
                f"💳 Total : {order.total} FCFA"
            )

            # Envoi WhatsApp
            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{order.phone_number}",
                body=message_body,
            )

        messages.success(request, "Statut mis à jour et notification envoyée.")
        return redirect("order_detail", order_id=order.id)

    return render(request, "orders/order_update_status.html", {
        "order": order,
        "statuses": statuses,
    })

def order_ingredients(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__ingredient_choices__ingredient',
            'items__dish__ingredients'
        ),
        id=order_id
    )

    return render(request, "orders/order_ingredients.html", {
        "order": order,
    })

def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Commande supprimée avec succès.")
        return redirect("order_list")

    return render(request, "orders/order_delete_confirm.html", {'order': order})



class ImageUploadAPIView(APIView):
    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response({"error": "No image provided"}, status=400)

        filename = default_storage.save(f"dishes/{image.name}", ContentFile(image.read()))
        relative_url = default_storage.url(filename)

        base_url = "https://8c392e16748b.ngrok-free.app"
        full_url = f"{base_url}{relative_url}"

        return Response({"image_url": full_url}, status=200)


class DishCreateAPIView(APIView):
    def post(self, request):
        data = request.data

        category = None
        if data.get("category_id"):
            category = Category.objects.get(pk=data["category_id"])

        dish = Dish.objects.create(
            title=data.get("title"),
            slug=data.get("slug") or slugify(data.get("title")),
            short_description=data.get("short_description", ""),
            description=data.get("description", ""),
            base_price=data.get("base_price", 0),
            base_time_minutes=data.get("base_time_minutes", 0),
            category=category,
            image=data.get("image_url")   # 🔥 ici on stocke l’URL
        )

        ingredients = data.get("ingredients", [])
        for item in ingredients:
            ingredient, _ = Ingredient.objects.get_or_create(
                name=item["name"],
                defaults={
                    "price_delta": item.get("price_delta", 0),
                    "time_minutes_delta": item.get("time_minutes_delta", 0),
                }
            )
            DishIngredient.objects.create(
                dish=dish,
                ingredient=ingredient,
                default_included=item.get("default_included", False)
            )

        return Response({"success": True, "dish_id": dish.id}, status=201)


class DishListAPIView(APIView):
    def get(self, request):
        dishes = Dish.objects.select_related("restaurant").all()
        data = []

        for d in dishes:
            data.append({
                "id": d.id,
                "title": d.title,
                "short_description": d.short_description,
                "description": d.description,
                "price": float(d.base_price),
                "time_minutes": d.base_time_minutes,
                "image": d.image,
                "category_id": d.category.id if d.category else None,

                # 🔥 RESTAURANT (NOUVEAU)
                "restaurant": {
                    "id": d.restaurant.id,
                    "name": d.restaurant.nom,
                    "image": d.restaurant.photo_principale,
                } if d.restaurant else None,

                "ingredients": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "price_delta": float(i.price_delta),
                        "time_delta": i.time_minutes_delta,
                        "is_allergen": i.is_allergen,
                    }
                    for i in d.ingredients.filter(active=True)
                ]
            })

        return Response(data, status=200)



class CategoryListAPIView(APIView):
    def get(self, request):
        categories = Category.objects.filter(active=True).order_by("order")
        return Response([
            {
                "id": c.id,
                "name": c.name,
                "image": c.image
            }
            for c in categories
        ])

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    data = request.data

    # 🔥 TOUJOURS UTILISER USER CONNECTÉ
    user = request.user

    if not user.is_authenticated:
        return Response({"error": "Not authenticated"}, status=401)

    if user.role != "client":
        return Response({"error": "Only clients can order"}, status=403)

    order = Order.objects.create(
        user=user,
        delivery_address=data.get("adresse", ""),
        phone_number=data.get("phone", ""),
        subtotal=data.get("subtotal", 0),
        delivery_fee=data.get("delivery_cost", 0),
        total=data.get("total", 0),
    )

    for item in data.get("items", []):
        dish = Dish.objects.get(id=item["dish_id"])

        order_item = OrderItem.objects.create(
            order=order,
            dish=dish,
            quantity=item.get("quantity", 1),
            line_price=item.get("total_price", 0),
        )

        for ing in item.get("ingredients", []):
            OrderItemIngredientChoice.objects.create(
                order_item=order_item,
                ingredient_id=ing["id"],
                choice_type=ing.get("type", "remove")
            )

        order_item.recalc_line()

    return Response({
        "message": "Order created",
        "order_id": order.id
    }, status=201)

class RestaurantListAPIView(APIView):
    def get(self, request):
        restaurants = Restaurant.objects.prefetch_related('images').all()
        data = []

        for r in restaurants:
            # Cherche la photo principale (type_image='banner' ou 'gallery')
            main_image = r.images.filter(type_image='banner').first()
            if not main_image:
                main_image = r.images.first()

            data.append({
                "id": r.id,
                "name": r.nom,
                "description": r.description,
                "image": main_image.image if main_image else None,
            })

        return Response(data, status=200)


class RestaurantDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            restaurant = Restaurant.objects.prefetch_related(
                "dishes__ingredients"
            ).get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant non trouvé"}, status=404)

        # 🔥 BANNERS (img est déjà string)
        banners = [
            img for img in restaurant.images.filter(type_image="banner").values_list('image', flat=True) if img
        ]

        # 🔥 DISHES COMPLETS
        dishes_data = []
        for d in restaurant.dishes.all():
            dishes_data.append({
                "id": d.id,
                "title": d.title,
                "short_description": d.short_description,
                "description": d.description,
                "price": float(d.base_price),
                "time_minutes": d.base_time_minutes,
                "image": d.image if d.image else None,  # ✅ corrigé

                # 🔥 RESTAURANT (IMPORTANT POUR FLUTTER)
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.nom,
                    "image": restaurant.photo_principale if restaurant.photo_principale else None,  # string direct
                },

                # 🔥 INGREDIENTS
                "ingredients": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "price_delta": float(i.price_delta),
                        "time_delta": i.time_minutes_delta,
                        "is_allergen": i.is_allergen,
                    }
                    for i in d.ingredients.filter(active=True)
                ]
            })

        data = {
            "id": restaurant.id,
            "nom": restaurant.nom,
            "description": restaurant.description,
            "type_cuisine": restaurant.type_cuisine,
            "adresse": restaurant.adresse,
            "ville": restaurant.ville,
            "code_postal": restaurant.code_postal,
            "pays": restaurant.pays,
            "latitude": str(restaurant.latitude) if restaurant.latitude else None,
            "longitude": str(restaurant.longitude) if restaurant.longitude else None,
            "telephone": restaurant.telephone,
            "email": restaurant.email,
            "site_web": restaurant.site_web,
            "photo_principale": restaurant.photo_principale if restaurant.photo_principale else None,  # string
            "banners": banners,
            "dishes": dishes_data,
        }

        return Response(data, status=200)