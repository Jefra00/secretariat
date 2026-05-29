import os
from django.core.files import File
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from services.models import Service, ServiceTexte
from commandes.models import Order,OrderFile
from paiements.models import Payment,Invoice

@login_required
def paiement_initier(request):
    """
    Étape finale : enregistre la commande, les fichiers et le paiement une fois le paiement confirmé.
    """
    user = request.user
    data = request.session.get('commande_en_attente')

    if not data:
        messages.error(request, "Aucune commande en attente de paiement.")
        return redirect("espace_client")

    montant = Decimal(str(data["montant_total"]))
    mode = data["mode_paiement"]

    if request.method == "POST":
        from services.models import Service, ServiceTexte  # import local pour éviter les boucles

        service = Service.objects.get(id=data["service_id"])
        texte = None
        if data.get("texte_id"):
            texte = ServiceTexte.objects.filter(id=data["texte_id"]).first()

        # ✅ Étape 1 — Création de la commande
        order = Order.objects.create(
            client=user,
            service=service,
            montant_total=montant,
            remise_appliquee=getattr(service, "remise", 0),
            mode_paiement=mode,
            notes_client=data["notes_client"],
            adresse=data["adresse"],
            statut="en_attente",
        )

        # ✅ Étape 2 — Gestion des fichiers uploadés temporairement
        fichiers_temp = request.session.get("fichiers_temp", [])
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")

        for nom_fichier in fichiers_temp:
            chemin = os.path.join(temp_dir, nom_fichier)
            if os.path.exists(chemin):
                with open(chemin, "rb") as f:
                    django_file = File(f, name=nom_fichier)
                    OrderFile.objects.create(
                        order=order,
                        fichier=django_file,
                        type_fichier="document_client"
                    )
                os.remove(chemin)

        # ✅ Étape 3 — Paiement en attente
        paiement = Payment.objects.create(
            order=order,
            montant=montant,
            mode=mode,
            statut="en_attente",
        )

        # ✅ Étape 4 — Facture
        Invoice.objects.create(
            payment=paiement,
            montant_total=montant,
            tva=Decimal("19.25"),
        )

        # ✅ Étape 5 — Nettoyage de session
        request.session.pop("commande_en_attente", None)
        request.session.pop("fichiers_temp", None)

        # ✅ Message de confirmation
        if texte:
            msg = f"✅ Paiement confirmé. Votre commande pour « {texte.titre} » ({service.nom}) est enregistrée et en attente de traitement."
        else:
            msg = f"✅ Paiement confirmé. Votre commande pour « {service.nom} » est enregistrée et en attente de traitement."
        messages.success(request, msg)
        return redirect("espace_client")

    return render(request, "paiements/initier.html", {
        "montant": montant,
        "mode": mode,
        "user": user,
    })
