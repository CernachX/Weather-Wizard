from flask import Flask, render_template, request, jsonify
import requests  # To make HTTP requests to APIs

# Initialize the Flask application
app = Flask(__name__)

# Replace with your OpenWeatherMap API key
API_KEY = "f0486a238f3f0fe2bbd249440f6441cc"  # Get your key from: https://openweathermap.org/
app.template_folder = 'templates_wA'  # Specify the folder where HTML templates are stored

# Function to get the user's current latitude and longitude using Google's Geolocation API
def getCurrentLocation():
    """
    Fetch the user's current latitude and longitude using Google's Geolocation API.
    """
    apiKey = "AIzaSyDG5A-68WHa81nCStN9nNNB6ufjWXuFfLo"  # Replace with your Google API key
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={apiKey}"
    response = requests.post(url)  # Send a POST request to the API
    data = response.json()  # Parse the JSON response
    lat = data["location"]['lat']  # Extract latitude
    lng = data["location"]['lng']  # Extract longitude
    return (lat, lng)  # Return latitude and longitude as a tuple

# Function to fetch weather data for a given location
def get_weather_data(location):
    """
    Fetch weather data for a given location using OpenWeatherMap's Geocoding and Weather APIs.
    """
    # Step 1: Get latitude and longitude using the Geocoding API
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {
        "q": location,  # City name
        "appid": API_KEY,  # API key
        "limit": 1  # Limit results to 1
    }
    try:
        # Make a request to the Geocoding API
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_response.raise_for_status()  # Raise an exception for bad status codes
        geocode_data = geocode_response.json()

        # Check if the response contains valid data
        if not geocode_data:
            print(f"Error: No geocoding results for location '{location}'")
            return None

        # Extract latitude and longitude from the response
        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']

        # Step 2: Fetch weather data using the latitude and longitude
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        weather_params = {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"  # Get temperature in Celsius
        }
        # Make a request to the Weather API
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()  # Raise an exception for bad status codes
        weather_data = weather_response.json()

        # Add Fahrenheit temperature to the weather data
        celsius_temp = weather_data['main']['temp']  # Get temperature in Celsius
        fahrenheit_temp = (celsius_temp * 9/5) + 32  # Convert to Fahrenheit
        weather_data['main']['temp_f'] = round(fahrenheit_temp, 2)  # Add Fahrenheit temp to the data

        return weather_data  # Return the weather data

    except requests.exceptions.RequestException as e:
        # Handle any exceptions during the API requests
        print(f"Error fetching weather data: {e}")
        return None

# Route to fetch the user's current location and return it as a city name
@app.route('/current-location', methods=['POST'])
def current_location():
    """
    Fetch the user's current location (latitude and longitude) and return the city name.
    """
    try:
        # Get the user's latitude and longitude
        lat, lng = getCurrentLocation()

        # Use the OpenWeatherMap reverse geocoding API to get the city name
        reverse_geocode_url = "http://api.openweathermap.org/geo/1.0/reverse"
        reverse_geocode_params = {
            "lat": lat,
            "lon": lng,
            "appid": API_KEY,
            "limit": 1
        }
        # Make a request to the reverse geocoding API
        response = requests.get(reverse_geocode_url, params=reverse_geocode_params)
        response.raise_for_status()
        data = response.json()

        # Check if the response contains valid data
        if not data:
            return jsonify({"error": "Could not determine your location."})

        # Extract the city name from the response
        city_name = data[0]['name']
        return jsonify({"location": city_name})  # Return the city name as JSON

    except requests.exceptions.RequestException as e:
        # Handle any exceptions during the API requests
        print(f"Error fetching current location: {e}")
        return jsonify({"error": "Could not fetch your current location."})

# Main route to display the weather app
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Render the weather app page and handle form submissions for fetching weather data.
    """
    if request.method == 'POST':
        # Get the location entered by the user
        location = request.form.get('location')
        if not location:
            # If no location is entered, display an error message
            return render_template('weatherApp.html', error="Please enter a valid location.")
        
        # Fetch weather data for the entered location
        weather_data = get_weather_data(location)
        if weather_data:
            # Render the template with the weather data
            return render_template('weatherApp.html', weather_data=weather_data)
        else:
            # Render the template with an error message if data could not be fetched
            return render_template('weatherApp.html', error="Could not retrieve weather data. Please check the location and your API key.")
    
    # Render the template for a GET request
    return render_template('weatherApp.html')

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for development