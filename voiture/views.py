import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Car, CarCategory, Reservation


# ── Helpers ───────────────────────────────────────────────────────────────────

def _booked_ranges(car):
    """Retourne la liste JSON des périodes déjà réservées (pending/confirmed)."""
    reservations = Reservation.objects.filter(
        car=car,
        statut__in=['pending', 'confirmed'],
        date_fin__gte=date.today(),
    ).values('date_debut', 'date_fin')
    return json.dumps([
        {'from': str(r['date_debut']), 'to': str(r['date_fin'])}
        for r in reservations
    ])


def _check_availability(car, date_debut, date_fin, exclude_id=None):
    """True si aucune réservation active ne chevauche les dates demandées."""
    qs = Reservation.objects.filter(
        car=car,
        statut__in=['pending', 'confirmed'],
    ).filter(
        Q(date_debut__lt=date_fin) & Q(date_fin__gt=date_debut)
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return not qs.exists()


# ── Accueil ───────────────────────────────────────────────────────────────────

def voiture_accueil(request):
    cars = (
        Car.objects
        .filter(status='available')
        .select_related('shop', 'category')
        .prefetch_related('images')
    )

    q            = request.GET.get('q', '').strip()
    cat_id       = request.GET.get('cat', '')
    transmission = request.GET.get('transmission', '')
    fuel         = request.GET.get('fuel', '')
    city         = request.GET.get('city', '').strip()
    driver       = request.GET.get('driver', '')

    if q:
        cars = cars.filter(
            Q(brand__icontains=q) | Q(model__icontains=q) |
            Q(description__icontains=q) | Q(color__icontains=q)
        )
    if cat_id:
        try:
            cars = cars.filter(category_id=int(cat_id))
        except (ValueError, TypeError):
            pass
    if transmission:
        cars = cars.filter(transmission=transmission)
    if fuel:
        cars = cars.filter(fuel=fuel)
    if city:
        cars = cars.filter(city__icontains=city)
    if driver == '1':
        cars = cars.filter(driver_included=True)

    total = cars.count()

    return render(request, 'voiture/accueil_voiture.html', {
        'cars':         cars[:60],
        'total':        total,
        'categories':   CarCategory.objects.all(),
        'q':            q,
        'cat_id':       cat_id,
        'transmission': transmission,
        'fuel':         fuel,
        'city':         city,
        'driver':       driver,
        'FUEL_CHOICES': Car.FUEL_CHOICES,
        'TRANS_CHOICES': Car.TRANSMISSION_CHOICES,
    })


# ── Détail + Réservation ──────────────────────────────────────────────────────

def detail_voiture(request, pk):
    car = get_object_or_404(Car, pk=pk, status='available')

    # ── Galerie ──
    images_qs = list(car.images.order_by('ordre', 'date_ajout'))
    gallery = []
    for img in images_qs:
        try:
            url = img.image.url
        except Exception:
            continue
        gallery.append({
            'pk':         img.pk,
            'url':        url,
            'principale': img.principale,
            'description': img.description or '',
        })

    main_image = next((i for i in gallery if i['principale']), gallery[0] if gallery else None)

    # ── Véhicules similaires (même catégorie, sinon remplissage) ──
    base_qs = (
        Car.objects.filter(status='available')
        .exclude(pk=pk)
        .select_related('category', 'shop')
        .prefetch_related('images')
    )
    if car.category:
        autres = list(base_qs.filter(category=car.category)[:6])
    else:
        autres = []
    if len(autres) < 6:
        excl = [c.pk for c in autres] + [pk]
        autres += list(base_qs.exclude(pk__in=excl)[:6 - len(autres)])

    # ── Traitement POST : création de réservation ──
    reservation_ok  = False
    reservation_obj = None
    form_error      = None
    form_data       = {}

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"/connexion/?next=/voiture/modele/{pk}/")

        date_debut_str = request.POST.get('date_debut', '').strip()
        date_fin_str   = request.POST.get('date_fin',   '').strip()
        telephone      = request.POST.get('telephone',  '').strip()
        message        = request.POST.get('message',    '').strip()

        form_data = {
            'date_debut': date_debut_str,
            'date_fin':   date_fin_str,
            'telephone':  telephone,
            'message':    message,
        }

        try:
            d_debut = date.fromisoformat(date_debut_str)
            d_fin   = date.fromisoformat(date_fin_str)
            today   = date.today()

            if d_debut < today:
                form_error = "La date de début ne peut pas être dans le passé."
            elif d_fin <= d_debut:
                form_error = "La date de fin doit être postérieure à la date de début."
            elif (d_fin - d_debut).days < 1:
                form_error = "La durée minimale de location est d'1 jour."
            elif not _check_availability(car, d_debut, d_fin):
                form_error = "Ce véhicule est déjà réservé sur cette période. Choisissez d'autres dates."
            else:
                nombre_jours = (d_fin - d_debut).days
                prix_total   = nombre_jours * float(car.prix_actuel)

                reservation_obj = Reservation.objects.create(
                    car=car,
                    client=request.user,
                    date_debut=d_debut,
                    date_fin=d_fin,
                    nombre_jours=nombre_jours,
                    prix_total=prix_total,
                    telephone=telephone,
                    message_client=message,
                )
                reservation_ok = True
                form_data = {}   # reset du formulaire

        except (ValueError, TypeError):
            form_error = "Dates invalides. Utilisez le format JJ/MM/AAAA."

    # ── Contexte commun GET/POST ──
    context = {
        'car':            car,
        'gallery':        gallery,
        'main_image':     main_image,
        'images_data':    json.dumps(gallery, default=str),
        'autres':         autres,
        'booked_ranges':  _booked_ranges(car),
        'today_str':      str(date.today()),
        'reservation_ok': reservation_ok,
        'reservation':    reservation_obj,
        'form_error':     form_error,
        'form_data':      form_data,
    }
    return render(request, 'voiture/detail_voiture.html', context)


# ── Mes réservations (client) ─────────────────────────────────────────────────

@login_required(login_url='/connexion/')
def mes_reservations(request):
    reservations = (
        Reservation.objects
        .filter(client=request.user)
        .select_related('car', 'car__shop')
        .prefetch_related('car__images')
    )
    return render(request, 'voiture/mes_reservations.html', {
        'reservations': reservations,
    })


# ── Annuler une réservation ───────────────────────────────────────────────────

@login_required(login_url='/connexion/')
@require_POST
def annuler_reservation(request, pk):
    resa = get_object_or_404(Reservation, pk=pk, client=request.user)
    if resa.is_cancellable():
        resa.statut = 'cancelled'
        resa.save(update_fields=['statut', 'updated_at'])
    return redirect('voiture:mes_reservations')


# ══════════════════════════════════════════════════════════════════════════════
#  API JSON — pour l'application mobile Flutter
# ══════════════════════════════════════════════════════════════════════════════

from django.http import JsonResponse


def _img_url(request, field):
    try:
        if field and field.name:
            return request.build_absolute_uri(field.url)
    except Exception:
        pass
    return None


def api_categories_voiture(request):
    cats = CarCategory.objects.all()
    data = [{"id": c.pk, "nom": c.name, "icon": c.icon} for c in cats]
    return JsonResponse(data, safe=False)


def api_voitures(request):
    qs = (Car.objects
          .filter(status='available')
          .select_related('shop', 'category')
          .prefetch_related('images'))
    q            = request.GET.get('q', '').strip()
    cat          = request.GET.get('cat', '').strip()
    transmission = request.GET.get('transmission', '').strip()
    fuel         = request.GET.get('fuel', '').strip()
    driver       = request.GET.get('driver', '').strip()
    if q:
        qs = qs.filter(Q(brand__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    if cat:
        try:
            qs = qs.filter(category_id=int(cat))
        except ValueError:
            pass
    if transmission:
        qs = qs.filter(transmission=transmission)
    if fuel:
        qs = qs.filter(fuel=fuel)
    if driver == '1':
        qs = qs.filter(driver_included=True)

    data = []
    for c in qs[:60]:
        main_img = c.images.filter(principale=True).first() or c.images.first()
        data.append({
            "id":           c.pk,
            "brand":        c.brand,
            "model":        c.model,
            "year":         c.year,
            "color":        c.color,
            "seats":        c.seats,
            "doors":        c.doors,
            "transmission": c.get_transmission_display(),
            "fuel":         c.get_fuel_display(),
            "air_conditioning": c.air_conditioning,
            "driver_included":  c.driver_included,
            "daily_price":  float(c.daily_price),
            "prix_promo":   float(c.promotional_price) if c.promotional_price else None,
            "prix_actuel":  float(c.prix_actuel),
            "remise_pct":   c.remise_pct,
            "city":         c.city,
            "image":        _img_url(request, main_img.image) if main_img else None,
            "categorie":    {"id": c.category.pk, "nom": str(c.category)} if c.category else None,
        })
    return JsonResponse(data, safe=False)


def api_voiture_detail(request, pk):
    c = get_object_or_404(Car, pk=pk, status='available')
    images = []
    for img in c.images.order_by('ordre', 'date_ajout'):
        try:
            images.append({
                "url":        request.build_absolute_uri(img.image.url),
                "principale": img.principale,
            })
        except Exception:
            pass

    booked = [
        {'start': str(r.date_debut), 'end': str(r.date_fin)}
        for r in Reservation.objects.filter(
            car=c, statut__in=['pending', 'confirmed'],
            date_fin__gte=date.today()
        )
    ]

    return JsonResponse({
        "id":           c.pk,
        "brand":        c.brand,
        "model":        c.model,
        "year":         c.year,
        "color":        c.color,
        "seats":        c.seats,
        "doors":        c.doors,
        "transmission": c.get_transmission_display(),
        "fuel":         c.get_fuel_display(),
        "air_conditioning": c.air_conditioning,
        "luggage_capacity": c.luggage_capacity,
        "driver_included":  c.driver_included,
        "daily_price":  float(c.daily_price),
        "prix_promo":   float(c.promotional_price) if c.promotional_price else None,
        "prix_actuel":  float(c.prix_actuel),
        "remise_pct":   c.remise_pct,
        "deposit":      float(c.deposit),
        "city":         c.city,
        "location":     c.location,
        "address":      c.address,
        "description":  c.description,
        "status":       c.status,
        "images":       images,
        "booked_ranges": booked,
        "categorie":    {"id": c.category.pk, "nom": str(c.category)} if c.category else None,
        "shop_tel":     c.shop.telephone if hasattr(c.shop, 'telephone') else None,
    })


@require_POST
def api_reserver_voiture(request, pk):
    import json as _json
    from django.contrib.auth.decorators import login_required as _lr
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentification requise"}, status=401)
    car = get_object_or_404(Car, pk=pk, status='available')
    try:
        body       = _json.loads(request.body)
        d_debut    = date.fromisoformat(body['date_debut'])
        d_fin      = date.fromisoformat(body['date_fin'])
        telephone  = body.get('telephone', '')
        message    = body.get('message', '')
    except (KeyError, ValueError):
        return JsonResponse({"error": "Données invalides"}, status=400)

    today = date.today()
    if d_debut < today:
        return JsonResponse({"error": "La date de début ne peut pas être dans le passé."}, status=400)
    if d_fin <= d_debut:
        return JsonResponse({"error": "La date de fin doit être postérieure à la date de début."}, status=400)
    if not _check_availability(car, d_debut, d_fin):
        return JsonResponse({"error": "Véhicule non disponible sur cette période."}, status=409)

    nombre_jours = (d_fin - d_debut).days
    prix_total   = nombre_jours * float(car.prix_actuel)
    resa = Reservation.objects.create(
        car=car, client=request.user,
        date_debut=d_debut, date_fin=d_fin,
        nombre_jours=nombre_jours, prix_total=prix_total,
        telephone=telephone, message_client=message,
    )
    return JsonResponse({"id": resa.pk, "status": "pending", "prix_total": float(resa.prix_total)}, status=201)
