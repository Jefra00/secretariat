from django import forms
from .models import SupportTicket, TicketMessage

# Classe CSS commune à tous les champs
BASE_INPUT_CLASS = (
    "w-full rounded-lg border-slate-300 dark:border-slate-700 "
    "bg-background-light dark:bg-background-dark focus:border-primary focus:ring-primary"
)

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['sujet', 'message', 'categorie', 'priorite']
        widgets = {
            'sujet': forms.TextInput(attrs={
                'class': BASE_INPUT_CLASS,
                'placeholder': 'Sujet de votre demande (ex: Problème de facturation, délai de livraison...)',
            }),
            'message': forms.Textarea(attrs={
                'class': BASE_INPUT_CLASS,
                'rows': 5,
                'placeholder': 'Décrivez en détail votre problème ou votre question pour que notre équipe puisse vous aider rapidement.',
            }),
            'categorie': forms.TextInput(attrs={
                'class': BASE_INPUT_CLASS,
                'placeholder': 'Ex: Facturation, Technique, Service Client...',
            }),
            'priorite': forms.Select(attrs={
                'class': BASE_INPUT_CLASS,
            }),
        }


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['contenu', 'piece_jointe']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': BASE_INPUT_CLASS,
                'rows': 3,
                'placeholder': 'Votre réponse ou précision...',
            }),
            'piece_jointe': forms.ClearableFileInput(attrs={
                'class': BASE_INPUT_CLASS,
            }),
        }
