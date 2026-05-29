import os
from django.conf import settings
from django.core.files import File
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from services.models import Service,ServiceTexte
from .models import Order,OrderFile,ResultFile

@login_required
def creer_commande(request, service_id=None, texte_id=None):
    """Prépare une commande et enregistre temporairement les fichiers avant paiement."""
    user = request.user

    # 🔍 Identification du service
    if texte_id:
        texte = get_object_or_404(ServiceTexte, id=texte_id)
        service = texte.service
        prix = texte.prix
        limite_fichiers = texte.nombre_documents
    else:
        texte = None
        service = get_object_or_404(Service, id=service_id)
        prix = service.prix_final()
        limite_fichiers = None

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        mode_paiement = request.POST.get("mode_paiement", "")
        utiliser_adresse_profil = request.POST.get("utiliser_adresse_profil") == "oui"
        adresse = user.adresse if utiliser_adresse_profil else request.POST.get("adresse")

        if not adresse:
            messages.error(request, "Veuillez renseigner une adresse de livraison.")
            return render(request, "commandes/creer_commande.html", {
                "service": service,
                "texte": texte,
                "user": user,
                "prix": prix,
                "limite_fichiers": limite_fichiers,
            })

        # 📦 Stockage de la commande dans la session
        request.session['commande_en_attente'] = {
            "service_id": service.id,
            "texte_id": texte.id if texte else None,
            "montant_total": float(prix),
            "mode_paiement": mode_paiement,
            "notes_client": notes,
            "adresse": adresse,
        }

        # 📁 Sauvegarde temporaire des fichiers dans MEDIA_ROOT/temp
        fichiers = request.FILES.getlist("fichiers")
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        fichiers_temp = []
        for fichier in fichiers:
            temp_path = os.path.join(temp_dir, fichier.name)
            with open(temp_path, "wb+") as destination:
                for chunk in fichier.chunks():
                    destination.write(chunk)
            fichiers_temp.append(fichier.name)

        request.session["fichiers_temp"] = fichiers_temp

        return redirect("paiements:paiement_initier")

    return render(request, "commandes/creer_commande.html", {
        "service": service,
        "texte": texte,
        "user": user,
        "prix": prix,
        "limite_fichiers": limite_fichiers,
    })


@login_required
def mes_commandes(request):
    user = request.user
    commandes_list = (
        Order.objects
        .filter(client=user)
        .select_related('service')
        .prefetch_related('service__textes', 'fichiers', 'resultats')  # ✅ maintenant valide
        .order_by('-date_commande')
    )

    paginator = Paginator(commandes_list, 6)
    page = request.GET.get('page')
    commandes = paginator.get_page(page)

    stats = {
        "total": commandes_list.count(),
        "en_attente": commandes_list.filter(statut="en_attente").count(),
        "en_cours": commandes_list.filter(statut="en_cours").count(),
        "terminees": commandes_list.filter(statut="termine").count(),
    }

    return render(request, "commandes/mes_commandes.html", {
        "commandes": commandes,
        "stats": stats,
    })

@login_required
def resultats_commande(request, code_commande):
    commande = get_object_or_404(Order, code_commande=code_commande, client=request.user)
    resultats = ResultFile.objects.filter(order=commande).order_by('-date_ajout')

    return render(request, "commandes/voir_resultats.html", {
        "commande": commande,
        "resultats": resultats,
    })

@login_required
def modifier_commande(request, code_commande):
    commande = get_object_or_404(Order, code_commande=code_commande, client=request.user)

    if commande.statut != 'en_attente':
        messages.warning(request, "Vous ne pouvez modifier qu’une commande en attente.")
        return redirect('commandes:mes_commandes')

    if request.method == "POST":
        commande.notes_client = request.POST.get('notes_client', commande.notes_client)
        commande.adresse = request.POST.get('adresse', commande.adresse)
        commande.mode_paiement = request.POST.get('mode_paiement', commande.mode_paiement)
        commande.save()
        messages.success(request, "Commande mise à jour avec succès ✅")
        return redirect('commandes:mes_commandes')

    return render(request, 'commandes/modifier_commande.html', {'commande': commande})

@login_required
def creer_commande_pack(request, texte_id):
    """Créer une commande à partir d’un ServiceTexte (pack spécifique)."""
    texte = get_object_or_404(ServiceTexte, id=texte_id)
    service = texte.service
    user = request.user

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        mode_paiement = request.POST.get("mode_paiement", "")
        utiliser_adresse_profil = request.POST.get("utiliser_adresse_profil") == "oui"
        adresse = user.adresse if utiliser_adresse_profil else request.POST.get("adresse")

        if not adresse:
            messages.error(request, "Veuillez renseigner une adresse de livraison.")
            return render(request, "commandes/creer_commande.html", {"service": service, "user": user, "texte": texte})

        # ✅ Le prix utilisé est celui du pack
        order = Order.objects.create(
            client=user,
            service=service,
            montant_total=texte.prix,
            remise_appliquee=0,
            mode_paiement=mode_paiement,
            notes_client=notes,
            adresse=adresse,
        )

        # ✅ Upload fichiers si besoin
        fichiers_uploades = request.FILES.getlist("fichiers")
        for fichier in fichiers_uploades:
            OrderFile.objects.create(order=order, fichier=fichier, type_fichier="document_client")

        messages.success(request, f"Votre commande pour le pack « {texte.titre or service.nom} » a été enregistrée avec succès ✅")
        return redirect("espaces:espace_client")

    return render(request, "commandes/creer_commande.html", {"service": service, "user": user, "texte": texte})


@login_required
def creer_commande_texte(request, texte_id):
    """
    Vue dédiée aux commandes des packs de type ServiceTexte.
    Étape 1 : Préparation et enregistrement temporaire avant paiement.
    Étape 2 : Redirection vers la page de paiement.
    """
    user = request.user
    texte = get_object_or_404(ServiceTexte, id=texte_id)
    service = texte.service
    prix = texte.prix
    limite_fichiers = texte.nombre_documents

    if request.method == "POST":
        notes = request.POST.get("notes", "")
        mode_paiement = request.POST.get("mode_paiement", "")
        utiliser_adresse_profil = request.POST.get("utiliser_adresse_profil") == "oui"
        adresse = user.adresse if utiliser_adresse_profil else request.POST.get("adresse")

        if not adresse:
            messages.error(request, "Veuillez renseigner une adresse de livraison.")
            return render(request, "commandes/creer_commande_texte.html", {
                "texte": texte,
                "service": service,
                "prix": prix,
                "limite_fichiers": limite_fichiers,
            })

        # 🧾 Stocker les infos de commande en session
        request.session['commande_en_attente'] = {
            "service_id": service.id,
            "texte_id": texte.id,
            "montant_total": float(prix),
            "mode_paiement": mode_paiement,
            "notes_client": notes,
            "adresse": adresse,
            "type_commande": "texte",
        }

        # 📁 Sauvegarde temporaire des fichiers uploadés
        fichiers = request.FILES.getlist("fichiers")
        temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        fichiers_temp = []
        for fichier in fichiers:
            temp_path = os.path.join(temp_dir, fichier.name)
            with open(temp_path, "wb+") as destination:
                for chunk in fichier.chunks():
                    destination.write(chunk)
            fichiers_temp.append(fichier.name)

        request.session["fichiers_temp"] = fichiers_temp

        return redirect("paiements:paiement_initier")

    return render(request, "commandes/creer_commande_texte.html", {
        "texte": texte,
        "service": service,
        "prix": prix,
        "limite_fichiers": limite_fichiers,
        "user": user,
    })