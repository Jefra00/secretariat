import json
import logging
import os

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True

    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
    if not raw or raw.strip() == "{}":
        logger.warning("FIREBASE_CREDENTIALS_JSON non configuré — notifications push désactivées.")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_dict = json.loads(raw)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception as e:
        logger.error(f"Erreur init Firebase Admin : {e}")
        return False


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Envoie une notification push via Firebase Cloud Messaging.
    Silencieux si Firebase n'est pas configuré.
    """
    if not fcm_token:
        return

    if not _init_firebase():
        return

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    icon="ic_notification",
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default"),
                ),
            ),
        )

        messaging.send(message)
        logger.info(f"Notification FCM envoyée : {title}")
    except Exception as e:
        logger.error(f"Erreur envoi FCM : {e}")
