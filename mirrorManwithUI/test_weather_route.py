from flask import Flask, jsonify, send_from_directory
from services.weather_service import get_current_weather

app = Flask(
    __name__,
    static_folder="views/static"
)


@app.route("/")
def home():
    return send_from_directory(
        "views/static",
        "index.html"
    )


@app.route("/api/weather")
def weather_api():

    weather = get_current_weather()

    if weather is None:
        return jsonify({
            "status": "error",
            "message": "Weather data is currently unavailable"
        }), 503

    return jsonify({
        "status": "success",
        "data": weather
    })


if __name__ == "__main__":
    app.run(debug=True)