import requests
import hashlib
import time
from django.shortcuts import render
from decouple import config


# 🔑 Lecture des variables d'environnement
API_KEY = config("HOTELBEDS_API_KEY", default="")
SECRET  = config("HOTELBEDS_SECRET", default="")

URL = "https://api.test.hotelbeds.com/hotel-api/1.0/hotels/availability"


# 🔐 Génération signature Hotelbeds
def generate_signature():
    timestamp = str(int(time.time()))
    raw = API_KEY + SECRET + timestamp
    return hashlib.sha256(raw.encode()).hexdigest()


# 🌍 Appel API
def get_hotels():

    print(f"API_KEY présente : {'OUI' if API_KEY else '❌ VIDE'}")
    print(f"SECRET présent  : {'OUI' if SECRET else '❌ VIDE'}")

    if not API_KEY or not SECRET:
        return [], "Clés API manquantes (.env non chargé)"

    signature = generate_signature()

    headers = {
        "Api-key": API_KEY,
        "X-Signature": signature,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    body = {
        "stay": {
            "checkIn": "2026-06-10",
            "checkOut": "2026-06-15"
        },
        "occupancies": [
            {
                "rooms": 1,
                "adults": 2,
                "children": 0
            }
        ],
        "destination": {
            "code": "PAR"
        },
        "filter": {
            "maxHotels": 12
        }
    }

    try:
        response = requests.post(URL, json=body, headers=headers, timeout=15)

        print("STATUS CODE:", response.status_code)
        print("RESPONSE:", response.text[:500])

        if response.status_code != 200:
            return [], f"Erreur API HTTP {response.status_code}"

        data = response.json()

        if "error" in data:
            return [], data["error"].get("message", "Erreur API")

        hotels_block = data.get("hotels", {})
        hotels = hotels_block.get("hotels", []) if isinstance(hotels_block, dict) else []

        print("HOTELS TROUVÉS:", len(hotels))

        return hotels, None

    except Exception as e:
        print("EXCEPTION:", e)
        return [], str(e)


# 🌐 Vue Django
def api(request):
    hotels, error = get_hotels()

    return render(request, "pages/api.html", {
        "hotels": hotels,
        "error": error
    })