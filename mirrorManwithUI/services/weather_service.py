import os
import requests
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")

load_dotenv(ENV_PATH)

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")

last_weather_data = None


def generate_gentle_suggestions(today_forecasts):
    suggestions = []

    will_rain = False
    will_thunder = False
    max_temp = -100
    high_humidity = False

    today = datetime.now().date()

    for item in today_forecasts:
        forecast_time = datetime.fromtimestamp(item["dt"])

        if forecast_time.date() != today:
            continue

        condition = item["weather"][0]["description"].lower()
        temp = item["main"]["temp"]
        humidity = item["main"]["humidity"]

        max_temp = max(max_temp, temp)

        if "rain" in condition:
            will_rain = True

        if "thunderstorm" in condition:
            will_thunder = True

        if humidity >= 85:
            high_humidity = True

    if will_thunder:
        suggestions.append({
            "message": "There may be a thunderstorm today. It would be safer to stay indoors if possible.",
            "priority": "high"
        })

    if will_rain:
        suggestions.append({
            "message": "It may rain later today. Taking an umbrella would be a good idea.",
            "priority": "medium"
        })

    if max_temp >= 32:
        suggestions.append({
            "message": "It may get quite warm today. Please remember to drink enough water.",
            "priority": "medium"
        })

    if high_humidity:
        suggestions.append({
            "message": "The air may feel a little heavy today. Try to stay cool and comfortable.",
            "priority": "low"
        })

    if not suggestions:
        suggestions.append({
            "message": "The weather looks comfortable today. Have a pleasant day.",
            "priority": "low"
        })

    return suggestions


def get_current_weather():
    global last_weather_data

    try:
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

        params = {
            "lat": LAT,
            "lon": LON,
            "appid": API_KEY,
            "units": "metric"
        }

        current_response = requests.get(current_url, params=params, timeout=10)
        forecast_response = requests.get(forecast_url, params=params, timeout=10)

        current_data = current_response.json()
        forecast_data = forecast_response.json()

        if current_response.status_code != 200:
            print("Current weather API error:", current_data)
            return last_weather_data

        if forecast_response.status_code != 200:
            print("Forecast API error:", forecast_data)
            return last_weather_data

        weather_data = {
            "temperature": round(current_data["main"]["temp"]),
            "humidity": current_data["main"]["humidity"],
            "condition": current_data["weather"][0]["description"],
            "suggestions": generate_gentle_suggestions(forecast_data["list"])
        }

        last_weather_data = weather_data
        return weather_data

    except Exception as e:
        print("Weather fetch failed:", e)
        return last_weather_data


if __name__ == "__main__":
    weather = get_current_weather()
    print(weather)