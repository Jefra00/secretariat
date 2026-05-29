# support/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import SupportTicket, TicketMessage
from .forms import SupportTicketForm, TicketMessageForm


@login_required
def liste_tickets(request):
    """Liste des tickets du client connecté avec pagination."""
    tickets_list = SupportTicket.objects.filter(user=request.user, actif=True).order_by('-date_creation')
    
    # 🔹 Pagination : 6 tickets par page
    paginator = Paginator(tickets_list, 6)
    page_number = request.GET.get("page")
    tickets = paginator.get_page(page_number)
    
    return render(request, "support/liste_tickets.html", {"tickets": tickets})


@login_required
def nouveau_ticket(request):
    """Création d’un nouveau ticket de support."""
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, "✅ Votre demande a été envoyée au support.")
            return redirect("support:liste_tickets")
        else:
            messages.error(request, "⚠️ Veuillez corriger les erreurs du formulaire.")
    else:
        form = SupportTicketForm()
    return render(request, "support/nouveau_ticket.html", {"form": form})


@login_required
def details_ticket(request, reference):
    """Détail d’un ticket + fil de discussion."""
    ticket = get_object_or_404(SupportTicket, reference=reference, user=request.user)
    messages_ticket = ticket.messages.filter(visible_par_client=True)

    if request.method == "POST":
        msg_form = TicketMessageForm(request.POST, request.FILES)
        if msg_form.is_valid():
            msg = msg_form.save(commit=False)
            msg.ticket = ticket
            msg.auteur = request.user
            msg.save()
            ticket.statut = 'en_cours'
            ticket.date_mise_a_jour = timezone.now()
            ticket.save(update_fields=['statut', 'date_mise_a_jour'])
            messages.success(request, "💬 Votre message a été envoyé.")
            return redirect("support:details_ticket", reference=ticket.reference)
    else:
        msg_form = TicketMessageForm()

    return render(request, "support/details_ticket.html", {
        "ticket": ticket,
        "messages_ticket": messages_ticket,
        "msg_form": msg_form,
    })
