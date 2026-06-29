from twilio.rest import Client
from django.conf import settings

def send_order_status_sms(phone_number, order_id, new_status):
    """Envoie un SMS au client après changement de statut."""

    if not phone_number:
        return  # Pas de numéro → on ne fait rien

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    status_text = {
        "pending": "Votre commande a été enregistrée.",
        "accepted": "Votre commande a été acceptée.",
        "in_progress": "Votre commande est en cours de préparation.",
        "done": "Votre commande est prête.",
        "cancelled": "Votre commande a été annulée."
    }

    message_body = f"Bonjour ! Le statut de votre commande #{order_id} a été mis à jour : {status_text.get(new_status, new_status)}"

    try:
        client.messages.create(
            body=message_body,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=phone_number,
        )
    except Exception as e:
        print("Erreur envoi SMS :", e)
