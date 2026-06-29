from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import Dish, Ingredient, DishIngredient, Category, Order, OrderItem, OrderItemIngredientChoice, DishRating, LivreurProfile
from django.db.models import Count, Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import os
import qrcode
import base64
from io import BytesIO
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST as require_post_method
from twilio.rest import Client
from .models import Restaurant
from .serializers import RestaurantDetailSerializer
from .services.sms_service import send_order_status_sms
from .services.fcm_service import send_push_notification


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.role in ('admin', 'employe'))


@login_required
def order_list(request):
    if not _is_staff(request.user):
        return redirect('connexion_client')
    orders = Order.objects.prefetch_related(
        'items__ingredient_choices',
        'items__dish'
    ).order_by('-created_at')

    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    if not _is_staff(request.user):
        return redirect('connexion_client')
    order = get_object_or_404(Order.objects.prefetch_related('items__dish'), id=order_id)

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

@login_required
def update_order_status(request, order_id):
    if not _is_staff(request.user):
        return redirect('connexion_client')
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

        # 🔔 Notification push FCM
        if order.user and order.user.fcm_token:
            status_labels = {
                'pending': 'En attente',
                'accepted': 'Acceptée',
                'in_progress': 'En préparation',
                'done': 'Livrée',
                'cancelled': 'Annulée',
            }
            label = status_labels.get(new_status, new_status)
            send_push_notification(
                fcm_token=order.user.fcm_token,
                title="Urban Eat — Commande mise à jour",
                body=f"Votre commande #{order.id} est maintenant : {label}",
                data={"order_id": str(order.id), "status": new_status},
            )

        messages.success(request, "Statut mis à jour et notification envoyée.")
        return redirect("order_detail", order_id=order.id)

    return render(request, "orders/order_update_status.html", {
        "order": order,
        "statuses": statuses,
    })

@login_required
def order_ingredients(request, order_id):
    if not _is_staff(request.user):
        return redirect('connexion_client')
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

@login_required
def order_delete(request, order_id):
    if not _is_staff(request.user):
        return redirect('connexion_client')
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

        full_url = request.build_absolute_uri(relative_url)

        return Response({"image_url": full_url}, status=200)


class DishCreateAPIView(APIView):
    def post(self, request):
        data = request.data

        category = None
        if data.get("category_id"):
            category = get_object_or_404(Category, pk=data["category_id"])

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
    permission_classes = [AllowAny]

    def get(self, request):
        dishes = (
            Dish.objects
            .select_related("restaurant")
            .prefetch_related("ingredients")
            .annotate(
                order_count=Count('orderitem', distinct=True),
                avg_rating=Avg('ratings__rating'),
            )
            .all()
        )
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

                "restaurant": {
                    "id": d.restaurant.id,
                    "name": d.restaurant.nom,
                    "image": d.restaurant.photo_principale,
                    "ville": d.restaurant.ville or "",
                    "latitude": float(d.restaurant.latitude) if d.restaurant.latitude else None,
                    "longitude": float(d.restaurant.longitude) if d.restaurant.longitude else None,
                } if d.restaurant else None,

                "order_count": d.order_count,
                "avg_rating": round(float(d.avg_rating), 1) if d.avg_rating else None,
                "is_top": d.order_count >= 50,
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
    permission_classes = [AllowAny]

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

    items = data.get("items", [])
    if not items:
        return Response({"error": "Le panier est vide."}, status=400)

    # Pré-charger tous les plats en une seule requête
    dish_ids = [item["dish_id"] for item in items]
    dishes_map = {d.id: d for d in Dish.objects.filter(id__in=dish_ids).select_related('restaurant')}

    missing = [iid for iid in dish_ids if iid not in dishes_map]
    if missing:
        return Response({"error": f"Plats introuvables : {missing}"}, status=400)

    # Valider que tous les plats sont de la même ville
    villes = {d.restaurant.ville for d in dishes_map.values() if d.restaurant}
    if len(villes) > 1:
        return Response(
            {"error": f"Impossible de mélanger des plats de villes différentes : {', '.join(villes)}."},
            status=400,
        )

    order = Order.objects.create(
        user=user,
        delivery_address=data.get("adresse", ""),
        phone_number=data.get("phone", ""),
        subtotal=data.get("subtotal", 0),
        delivery_fee=data.get("delivery_cost", 0),
        total=data.get("total", 0),
        delivery_lat=data.get("delivery_lat"),
        delivery_lng=data.get("delivery_lng"),
    )

    for item in items:
        dish = dishes_map[item["dish_id"]]

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

    # 🔔 Notifier tous les livreurs disponibles
    livreurs_dispo = (
        LivreurProfile.objects
        .filter(disponible=True, user__role='livreur')
        .exclude(user__fcm_token__isnull=True)
        .exclude(user__fcm_token='')
        .select_related('user')
    )
    items_summary = ", ".join([
        f"{item.dish.title} ×{item.quantity}"
        for item in OrderItem.objects.filter(order=order).select_related('dish')
    ])
    for lp in livreurs_dispo:
        send_push_notification(
            fcm_token=lp.user.fcm_token,
            title="🛵 Nouvelle commande disponible !",
            body=f"Commande #{order.id} — {order.delivery_address} — {float(order.total):.0f} FCFA\n{items_summary}",
            data={"order_id": str(order.id), "type": "new_order"},
        )

    return Response({
        "message": "Order created",
        "order_id": order.id,
        "qr_code": order.qr_code,
    }, status=201)

class RestaurantListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance
        from django.contrib.gis.measure import D

        try:
            lat = float(request.GET.get('lat', ''))
            lng = float(request.GET.get('lng', ''))
            user_point = Point(lng, lat, srid=4326)
            radius = int(request.GET.get('radius', 8000))
            has_location = True
        except (TypeError, ValueError):
            user_point = None
            has_location = False

        qs = Restaurant.objects.prefetch_related('images')

        if has_location:
            # Restaurants avec PointField: filtrer par rayon + annoter distance
            qs_geo = (
                qs.filter(location__isnull=False)
                .filter(location__distance_lte=(user_point, D(m=radius)))
                .annotate(distance_m=Distance('location', user_point))
                .order_by('distance_m')
            )
            # Fallback: restaurants sans PointField mais même ville via User.last_location
            qs_fallback = qs.filter(location__isnull=True)
            restaurants = list(qs_geo) + list(qs_fallback)
        else:
            restaurants = list(qs.all())

        data = []
        for r in restaurants:
            main_image = r.images.filter(type_image='banner').first() or r.images.first()
            entry = {
                "id": r.id,
                "name": r.nom,
                "description": r.description,
                "image": main_image.image if main_image else None,
                "ville": r.ville,
                "est_ouvert": r.est_ouvert,
                "latitude": float(r.latitude) if r.latitude else None,
                "longitude": float(r.longitude) if r.longitude else None,
            }
            if has_location and hasattr(r, 'distance_m') and r.distance_m is not None:
                entry["distance_m"] = round(r.distance_m.m)
            data.append(entry)

        return Response(data, status=200)


# ──────────────────────────────────────────────────────────────────────────────
# TOP PLATS
# ──────────────────────────────────────────────────────────────────────────────
class TopDishesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        dishes = (
            Dish.objects
            .filter(active=True)
            .prefetch_related("ingredients")
            .select_related("restaurant")
            .annotate(
                order_count=Count('orderitem', distinct=True),
                avg_rating=Avg('ratings__rating'),
            )
            .order_by('-order_count')[:12]
        )
        data = []
        for d in dishes:
            data.append({
                "id": d.id,
                "title": d.title,
                "short_description": d.short_description,
                "image": d.image,
                "price": float(d.base_price),
                "time_minutes": d.base_time_minutes,
                "order_count": d.order_count,
                "avg_rating": round(float(d.avg_rating), 1) if d.avg_rating else None,
                "is_top": d.order_count >= 50,
                "description": d.description,
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
                ],
            })
        return Response(data)


# ──────────────────────────────────────────────────────────────────────────────
# NOTATION PLAT
# ──────────────────────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_dish(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    try:
        rating_value = int(request.data.get("rating", 0))
    except (ValueError, TypeError):
        return Response({"error": "Note invalide"}, status=400)

    if not (1 <= rating_value <= 5):
        return Response({"error": "La note doit être entre 1 et 5"}, status=400)

    comment = request.data.get("comment", "")

    has_ordered = OrderItem.objects.filter(
        order__user=request.user,
        order__status="done",
        dish=dish,
    ).exists()

    if not has_ordered:
        return Response(
            {"error": "Vous devez avoir commandé et reçu ce plat pour le noter."},
            status=403,
        )

    rating, created = DishRating.objects.update_or_create(
        dish=dish,
        user=request.user,
        defaults={"rating": rating_value, "comment": comment},
    )
    return Response({"ok": True, "created": created})


# ──────────────────────────────────────────────────────────────────────────────
# CHATBOT MISTRAL
# ──────────────────────────────────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def chatbot(request):
    import requests as req_lib
    from django.utils import timezone

    message = request.data.get("message", "").strip()
    history = request.data.get("history", [])

    if not message:
        return Response({"error": "Message vide"}, status=400)

    # Contexte : top plats depuis la DB
    top = (
        Dish.objects
        .filter(active=True)
        .annotate(order_count=Count('orderitem', distinct=True))
        .order_by('-order_count')[:10]
    )
    dishes_ctx = "\n".join([
        f"- {d.title} : {int(d.base_price)} FCFA, {d.base_time_minutes} min"
        f"{', commandé ' + str(d.order_count) + ' fois' if d.order_count else ''}"
        for d in top
    ])

    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day = day_names[timezone.now().weekday()]

    system_prompt = (
        "Tu es ChefBot, l'assistant IA d'Urban Eat, une application de food delivery "
        "à Brazzaville (Congo). Tu parles en français, tu es chaleureux et enthousiaste.\n"
        f"Aujourd'hui nous sommes {day}.\n\n"
        "Plats disponibles sur la plateforme (triés par popularité) :\n"
        f"{dishes_ctx}\n\n"
        "Tes missions :\n"
        "- Suggérer les meilleurs plats selon le jour, l'heure, l'occasion ou les goûts\n"
        "- Répondre aux questions sur les plats, prix, ingrédients\n"
        "- Mettre en avant les best-sellers quand on demande les plats du jour/semaine/mois\n"
        "- Rester concis (3-4 phrases max par réponse)\n"
        "- Ne jamais inventer de plats ou de prix absents de la liste ci-dessus"
    )

    messages_to_send = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant"):
            messages_to_send.append({"role": h["role"], "content": h["content"]})
    messages_to_send.append({"role": "user", "content": message})

    api_key = settings.MISTRAL_API_KEY
    if not api_key:
        return Response({
            "reply": "ChefBot n'est pas encore activé. Configurez MISTRAL_API_KEY pour commencer !"
        })

    try:
        res = req_lib.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistral-small-latest",
                "messages": messages_to_send,
                "max_tokens": 350,
                "temperature": 0.75,
            },
            timeout=15,
        )
        reply = res.json()["choices"][0]["message"]["content"]
    except Exception:
        reply = "Désolé, je suis momentanément indisponible. Réessayez dans quelques instants !"

    return Response({"reply": reply})


class RestaurantDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        restaurant = get_object_or_404(
            Restaurant.objects.prefetch_related(
                "images",
                "dishes__ingredients",
                "types_cuisine",
            ),
            pk=pk,
        )

        # 🔥 BANNERS (img est déjà string)
        banners = [
            img for img in restaurant.images.filter(type_image="banner").values_list('image', flat=True) if img
        ]

        # Dishes — vides si le restaurant est fermé
        dishes_data = []
        if restaurant.est_ouvert:
            for d in restaurant.dishes.filter(active=True):
                dishes_data.append({
                    "id": d.id,
                    "title": d.title,
                    "short_description": d.short_description,
                    "description": d.description,
                    "price": float(d.base_price),
                    "time_minutes": d.base_time_minutes,
                    "image": d.image if d.image else None,
                    "restaurant": {
                        "id": restaurant.id,
                        "name": restaurant.nom,
                        "image": restaurant.photo_principale if restaurant.photo_principale else None,
                    },
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

        # URL d'itinéraire Google Maps — destination = restaurant, origine = position GPS utilisateur
        itineraire_url = None
        if restaurant.latitude and restaurant.longitude:
            itineraire_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&destination={restaurant.latitude},{restaurant.longitude}"
                f"&travelmode=driving"
            )

        adresse_complete = ", ".join(filter(None, [
            restaurant.adresse,
            restaurant.ville,
            restaurant.code_postal,
            restaurant.pays,
        ]))

        data = {
            "id": restaurant.id,
            "nom": restaurant.nom,
            "description": restaurant.description,
            "est_ouvert": restaurant.est_ouvert,
            "type_cuisine": restaurant.type_cuisine,
            "types_cuisine": [tc.nom for tc in restaurant.types_cuisine.all()],
            "adresse": restaurant.adresse,
            "adresse_complete": adresse_complete,
            "ville": restaurant.ville,
            "code_postal": restaurant.code_postal,
            "pays": restaurant.pays,
            "latitude": float(restaurant.latitude) if restaurant.latitude else None,
            "longitude": float(restaurant.longitude) if restaurant.longitude else None,
            "itineraire_url": itineraire_url,
            "email": restaurant.email,
            "site_web": restaurant.site_web,
            "photo_principale": restaurant.photo_principale if restaurant.photo_principale else None,
            "banners": banners,
            "dishes": dishes_data,
        }

        return Response(data, status=200)


# ──────────────────────────────────────────────────────────────────────────────
# TOGGLE OUVERT/FERMÉ
# ──────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_restaurant_ouvert(request, pk):
    """Bascule l'état ouvert/fermé d'un restaurant."""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    restaurant.est_ouvert = not restaurant.est_ouvert
    restaurant.save(update_fields=["est_ouvert"])
    return Response({
        "id": restaurant.id,
        "nom": restaurant.nom,
        "est_ouvert": restaurant.est_ouvert,
    })


# ──────────────────────────────────────────────────────────────────────────────
# SYSTÈME LIVREUR
# ──────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def commandes_disponibles(request):
    """Liste des commandes acceptées sans livreur — filtrées par zone du livreur."""
    if request.user.role != 'livreur':
        return Response({"error": "Accès réservé aux livreurs"}, status=403)

    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.measure import D

    orders = (
        Order.objects
        .filter(status='accepted', livreur__isnull=True)
        .prefetch_related('items__dish__restaurant')
        .order_by('-created_at')
    )

    # Position du livreur pour annoter la distance
    livreur_point = None
    try:
        lp = request.user.livreur_profile
        if lp.location:
            livreur_point = lp.location
    except Exception:
        pass
    data = []
    for order in orders:
        items = [
            {"dish_title": item.dish.title, "quantity": item.quantity, "line_price": float(item.line_price)}
            for item in order.items.all()
        ]
        # Calcul de distance via le restaurant du premier plat
        distance_m = None
        if livreur_point:
            try:
                first_dish = order.items.first()
                if first_dish and first_dish.dish.restaurant and first_dish.dish.restaurant.location:
                    from django.contrib.gis.measure import Distance as GisDistance
                    d = livreur_point.distance(first_dish.dish.restaurant.location)
                    distance_m = round(d * 111320)  # degrés → mètres approx
            except Exception:
                pass

        data.append({
            "id": order.id,
            "created_at": order.created_at,
            "delivery_address": order.delivery_address,
            "total": float(order.total),
            "items": items,
            "distance_m": distance_m,
        })
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reserver_commande(request, order_id):
    """Un livreur réserve une commande (premier arrivé, premier servi)."""
    if request.user.role != 'livreur':
        return Response({"error": "Accès réservé aux livreurs"}, status=403)

    from django.db import transaction
    from django.utils import timezone as tz

    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), id=order_id)

        if order.livreur is not None:
            return Response({"error": "Cette commande est déjà réservée par un autre livreur"}, status=400)

        if order.status not in ['accepted']:
            return Response({"error": "Cette commande n'est pas disponible à la réservation"}, status=400)

        order.livreur = request.user
        order.livreur_reserved_at = tz.now()
        order.status = 'in_progress'
        order.save(update_fields=['livreur', 'livreur_reserved_at', 'status'])

    # Marquer le livreur comme indisponible
    try:
        profile = request.user.livreur_profile
        profile.disponible = False
        profile.save(update_fields=['disponible'])
    except Exception:
        pass

    # Notifier le client
    if order.user and order.user.fcm_token:
        livreur_name = request.user.get_full_name() or request.user.username
        try:
            matricule = request.user.livreur_profile.matricule_moto
        except Exception:
            matricule = ""
        send_push_notification(
            fcm_token=order.user.fcm_token,
            title="🛵 Livreur assigné !",
            body=f"{livreur_name} ({matricule}) va livrer votre commande #{order.id}. Montrez-lui votre QR code.",
            data={"order_id": str(order.id), "type": "livreur_assigned"},
        )

    return Response({"ok": True, "message": "Commande réservée avec succès"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def valider_qr(request):
    """Le livreur scanne et valide le QR code d'une commande."""
    if request.user.role != 'livreur':
        return Response({"error": "Accès réservé aux livreurs"}, status=403)

    qr_code = request.data.get("qr_code", "").strip()
    if not qr_code:
        return Response({"error": "qr_code manquant"}, status=400)

    try:
        order = Order.objects.select_related('user').get(qr_code=qr_code)
    except Order.DoesNotExist:
        return Response({"error": "QR code invalide"}, status=404)

    if order.livreur_id != request.user.id:
        return Response({"error": "Ce QR code ne correspond pas à votre commande"}, status=403)

    if order.qr_validated:
        return Response({"ok": True, "already_validated": True, "order_id": order.id})

    from django.utils import timezone as tz
    order.qr_validated = True
    order.qr_validated_at = tz.now()
    order.save(update_fields=['qr_validated', 'qr_validated_at'])

    return Response({
        "ok": True,
        "order_id": order.id,
        "client": order.user.get_full_name() or order.user.username if order.user else "",
        "delivery_address": order.delivery_address,
        "total": float(order.total),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_livreur_position(request):
    """Le livreur met à jour sa position GPS."""
    if request.user.role != 'livreur':
        return Response({"error": "Accès réservé aux livreurs"}, status=403)

    lat = request.data.get("latitude")
    lng = request.data.get("longitude")

    if lat is None or lng is None:
        return Response({"error": "latitude et longitude requis"}, status=400)

    from django.contrib.gis.geos import Point as GisPoint
    from django.utils import timezone as tz

    profile, _ = LivreurProfile.objects.get_or_create(
        user=request.user,
        defaults={"matricule_moto": "NC"}
    )
    profile.latitude = lat
    profile.longitude = lng
    profile.location = GisPoint(float(lng), float(lat), srid=4326)
    profile.location_updated_at = tz.now()
    profile.save(update_fields=['latitude', 'longitude', 'location', 'location_updated_at'])

    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_livraisons(request):
    """Commandes assignées au livreur connecté."""
    if request.user.role != 'livreur':
        return Response({"error": "Accès réservé aux livreurs"}, status=403)

    orders = (
        Order.objects
        .filter(livreur=request.user)
        .prefetch_related('items__dish')
        .select_related('user')
        .order_by('-created_at')
    )
    data = []
    for order in orders:
        items = [
            {"dish_title": item.dish.title, "quantity": item.quantity, "line_price": float(item.line_price)}
            for item in order.items.all()
        ]
        data.append({
            "id": order.id,
            "status": order.status,
            "created_at": order.created_at,
            "delivery_address": order.delivery_address,
            "delivery_lat": float(order.delivery_lat) if order.delivery_lat else None,
            "delivery_lng": float(order.delivery_lng) if order.delivery_lng else None,
            "phone_number": order.phone_number,
            "total": float(order.total),
            "qr_validated": order.qr_validated,
            "client_name": order.user.get_full_name() if order.user else "",
            "client_phone": order.user.telephone if order.user else "",
            "items": items,
        })
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def livreur_position_for_order(request, order_id):
    """Position en temps réel du livreur — accessible par le client propriétaire de la commande."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.livreur:
        return Response({"error": "Pas de livreur assigné"}, status=404)
    try:
        profile = LivreurProfile.objects.get(user=order.livreur)
        if profile.latitude and profile.longitude:
            return Response({
                "latitude": float(profile.latitude),
                "longitude": float(profile.longitude),
            })
        return Response({"error": "Position inconnue"}, status=404)
    except LivreurProfile.DoesNotExist:
        return Response({"error": "Profil livreur introuvable"}, status=404)

# ── Page de gestion des commandes (web admin) ─────────────────────────────────

@login_required
def gestion_commandes(request):
    """Tableau de bord de gestion des commandes — accès staff/admin/employe."""
    if request.user.role not in ('admin', 'employe') and not request.user.is_staff:
        return redirect('accueil')

    orders = (
        Order.objects
        .prefetch_related('items__dish')
        .select_related('user', 'livreur')
        .order_by('-created_at')
    )

    pending    = orders.filter(status='pending')
    accepted   = orders.filter(status='accepted')
    in_progress = orders.filter(status='in_progress')
    done       = orders.filter(status='done')
    cancelled  = orders.filter(status='cancelled')

    return render(request, 'orders/gestion_commandes.html', {
        'pending':      pending,
        'accepted':     accepted,
        'in_progress':  in_progress,
        'done':         done,
        'cancelled':    cancelled,
        'total_active': pending.count() + accepted.count() + in_progress.count(),
        'steps': ['Commande reçue', 'Acceptée', 'En préparation', 'Livrée'],
        'current_step': 0,
    })


@login_required
@require_post_method
def avancer_statut(request, order_id):
    """Passe la commande à l'étape suivante (ou annule)."""
    if request.user.role not in ('admin', 'employe') and not request.user.is_staff:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    order = get_object_or_404(Order, id=order_id)
    action = request.POST.get('action', 'next')

    next_status = {
        'pending':     'accepted',
        'accepted':    'in_progress',
        'in_progress': 'done',
    }

    if action == 'cancel':
        order.status = 'cancelled'
    elif action == 'next' and order.status in next_status:
        order.status = next_status[order.status]
    order.save(update_fields=['status'])

    # Notification FCM client
    if order.user and order.user.fcm_token:
        labels = {
            'accepted':    ('✅ Commande acceptée !', f'Votre commande #{order.id} a été acceptée par le restaurant.'),
            'in_progress': ('🍳 En préparation !',    f'Le restaurant prépare votre commande #{order.id}.'),
            'done':        ('🛵 Livrée !',             f'Votre commande #{order.id} a été livrée. Bon appétit !'),
            'cancelled':   ('❌ Annulée',              f'Votre commande #{order.id} a été annulée.'),
        }
        if order.status in labels:
            title, body = labels[order.status]
            send_push_notification(
                fcm_token=order.user.fcm_token,
                title=title,
                body=body,
                data={"order_id": str(order.id), "status": order.status},
            )

    messages.success(request, f"Commande #{order.id} → {order.get_status_display()}")
    return redirect('gestion_commandes')


# ──────────────────────────────────────────────────────────────────────────────
# INSCRIPTION RESTAURANT (interface web admin)
# ──────────────────────────────────────────────────────────────────────────────

@login_required(login_url='/connexion/')
def inscription_restaurant(request):
    """Page web pour créer un restaurant avec géolocalisation automatique."""
    from .models import Restaurant, TypeCuisine

    error = None
    success = None
    types_cuisine_qs = TypeCuisine.objects.all()

    if request.method == 'POST':
        nom              = request.POST.get('nom', '').strip()
        description      = request.POST.get('description', '').strip()
        types_ids        = request.POST.getlist('types_cuisine')  # liste d'IDs
        adresse          = request.POST.get('adresse', '').strip()
        ville            = request.POST.get('ville', '').strip()
        code_postal      = request.POST.get('code_postal', '').strip()
        pays             = request.POST.get('pays', 'Congo').strip()
        telephone        = request.POST.get('telephone', '').strip()
        email            = request.POST.get('email', '').strip()
        site_web         = request.POST.get('site_web', '').strip()
        photo_principale = request.POST.get('photo_principale', '').strip()
        latitude         = request.POST.get('latitude', '').strip()
        longitude        = request.POST.get('longitude', '').strip()

        if not all([nom, adresse, ville]):
            error = "Nom, adresse et ville sont obligatoires."
        else:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None
            restaurant = Restaurant(
                nom=nom,
                description=description,
                adresse=adresse,
                ville=ville,
                code_postal=code_postal,
                pays=pays,
                telephone=telephone,
                email=email,
                site_web=site_web,
                photo_principale=photo_principale,
                latitude=lat,
                longitude=lng,
            )
            restaurant.save()
            if types_ids:
                restaurant.types_cuisine.set(
                    TypeCuisine.objects.filter(id__in=types_ids)
                )
            success = f"✅ Restaurant «{nom}» créé avec succès ! (ID #{restaurant.id})"

    return render(request, 'admin/inscription_restaurant.html', {
        'error': error,
        'success': success,
        'types_cuisine': types_cuisine_qs,
    })
