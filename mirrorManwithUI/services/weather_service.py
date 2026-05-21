import os
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")

load_dotenv(ENV_PATH)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")

last_weather_data = None


def generate_suggestions(weather):
    suggestions = []

    temperature = weather["temperature"]
    humidity = weather["humidity"]
    condition = weather["condition"].lower()

    if "rain" in condition:
        suggestions.append({
            "message": "There is a chance of rain today. Please take an umbrella.",
            "priority": "medium"
        })

    if "thunderstorm" in condition:
        suggestions.append({
            "message": "Thunderstorm conditions are expected. It is safer to avoid going outside.",
            "priority": "high"
        })

    if temperature >= 32:
        suggestions.append({
            "message": "It is quite hot today. Please drink enough water.",
            "priority": "high"
        })

    if temperature <= 20:
        suggestions.append({
            "message": "It is a bit cold today. Please wear warm clothes.",
            "priority": "low"
        })

    if humidity >= 85:
        suggestions.append({
            "message": "Humidity is high today. Try to stay cool and comfortable.",
            "priority": "medium"
        })

    if not suggestions:
        suggestions.append({
            "message": "Weather looks normal today. Have a pleasant day.",
            "priority": "low"
        })

    return suggestions


def get_current_weather():
    global last_weather_data

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": LAT,
        "lon": LON,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print("Status Code:", response.status_code)

        data = response.json()

        if response.status_code != 200:
            print("API Error:", data)
            return last_weather_data

        weather_data = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
            "suggestions": []
        }

        weather_data["suggestions"] = generate_suggestions(weather_data)

        last_weather_data = weather_data

        return weather_data

    except Exception as e:
        print("Weather fetch failed:", e)
        return last_weather_data


if __name__ == "__main__":
    weather = get_current_weather()
    print("Weather Data:")
    print(weather)