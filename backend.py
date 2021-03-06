from datetime import datetime, timedelta
import json
import re

from countryinfo import CountryInfo
from decouple import config
from flask import request
import geocoder
from geopy.geocoders import Nominatim
import pycountry
import pytz
import requests
import wikipedia


WEATHER = config("WEATHER")


def get_ip():
    """Returns device ip."""
    # By Tirtha R: https://stackoverflow.com/questions/3759981/get-ip-address-of-visitors-using-flask-for-python
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']  # if behind a proxy


def get_location_by_ip():
    """Returns geo information of a device according to this ip address."""
    ip = get_ip()
    geo = geocoder.ip(ip)
    if geo.lat is None:
        return {'lat': 51.5074, 'lon': 0.1278,
                'city': 'London', 'country': 'United Kingdom'}
    else:
        location = {'lat': geo.lat, 'lon': geo.lng, 'city': geo.city,
                    'country': pycountry.countries.get(alpha_2=geo.country).name}
        return location


def get_countries_json():
    """Returns countries cities information from file."""
    # Credit: Project by russ666 Tlicensed under the MIT License https://github.com/russ666/all-countries-and-cities-json
    path = r"countries.json"
    with open(path) as json_file:
        return json.load(json_file)


def is_country(name, countries):
    """Check if a given name is country."""
    return name in countries


def cities_generator(countries):
    """Returns all main cities in the world."""
    for country, cities in countries.items():
        for city in cities:
            yield city, country


def is_city(name, countries):
    """Checks if given name is city and returns its country."""
    for city, country in cities_generator(countries):
        if name == city:
            return city, country
    return None


def get_location_by_name(name):
    """Get location information by given name."""
    location = {'lat': None, 'lon': None, 'city': None, 'country': None}
    name = name.title()
    countries = get_countries_json()

    if is_country(name, countries):
        location['country'] = name.title()
        location['city'] = get_capital(name)
    else:
        city = is_city(name, countries)
        if city:
            location['city'] = city[0]
            location['country'] = city[1]
        else:
            location = default_location()
    location['lat'], location['lon'] = get_location_latlon(
        f"{location['city']} {location['country']}")
    return location


def get_location_summary(location):
    """Returns wikipedia summary for value."""
    search = f"{location['city']} city in {location['country']}"
    return {'url': wikipedia.page(location).url, 'summary': wikipedia.summary(search, chars=1000)}


def default_location(dcity="London", dcountry="United Kingdom"):
    """Return a default value for location."""
    return {'lat': None, 'lon': None, 'city': dcity, 'country': dcountry}


def get_capital(country):
    """Returns Country Capital."""
    country = CountryInfo(country)
    return country.capital()


def get_location_latlon(location):
    """Returns the latitude and longitude number of a given location or address."""
    geolocator = Nominatim(user_agent="Beltempo")
    location = geolocator.geocode(location)
    return (location.latitude, location.longitude)


# Times
def get_timezone(capital, country):
    """Return timezone code by capital."""
    for tzone in pytz.all_timezones:
        p = tzone.partition('/')
        if capital in p or country in p:
            return tzone
    return 'Europe/London'


def get_local_time(country):
    """Returns time at user location."""
    capital = get_capital(country).title()
    user_time_zone = get_timezone(capital, country)
    t = pytz.timezone(user_time_zone)
    date = datetime.now(t)
    return date


def get_next_days(num, date):
    """Returns next 6 days of the week."""
    # manipulation of this idea: https://stackoverflow.com/questions/993358/creating-a-range-of-dates-in-python
    next_days = [timedelta(days=x) + date for x in range(num)][1:]
    return [(day.strftime("%a").upper(), day.strftime("%d").upper()) for day in next_days]


def get_weather(lat, lon):
    url = "https://rapidapi.p.rapidapi.com/forecast/daily"
    querystring = {"lat": lat, "lon": lon}
    headers = {
        'x-rapidapi-host': "weatherbit-v1-mashape.p.rapidapi.com",
        'x-rapidapi-key': WEATHER,
    }
    return requests.request("GET", url, headers=headers, params=querystring).text


def get_pattern(pattern, text):
    p = re.compile(pattern)
    return list(p.finditer(text))


def get_theme(day):
    """Returns css theme name according to current weather."""
    day = day.lower()
    if day in ('clear sky', 'few clouds', 'isolated clouds'):
        return 'sun'
    if day in ('broken clouds', 'overcast clouds', 'scattered clouds', 'few clouds'):
        return 'clouds'
    if day in ('light rain', 'light shower rain'):
        return 'rain'
    if day in ('heavy rain', 'moderate rain', 'thunderstorm with rain'):
        return 'storm'
    return 'clouds'


def get_days_info(location):
    """Returns a tuple with day weather description, degrees and match icon name."""
    latitude = str(location['lat'])
    longitude = str(location['lon'])

    r = get_weather(latitude, longitude)

    matches = get_pattern(r'"description":"(\D+)"},', r)
    matches2 = get_pattern(r'"low_temp":(\d*\.?\d?),"max_temp":(\d*\.?\d?)', r)

    description_list = [str(i).split('"')[3] for i in matches]
    low = [round(float(j.group(1))) for j in matches2]
    maxi = [round(float(j.group(2))) for j in matches2]
    match_pic = [get_theme(description)
                 + ".svg" for description in description_list]

    info = list(zip(description_list, low, maxi, match_pic))
    del info[0]
    return info


def sentences(theme):
    s = {
        'sun': "Here Comes The Sun",
        'clouds': "There Is No Sunshine When She is Gone",
        'rain': "It's Raining Men",
        'storm': ""
    }
    return s[theme]


def setting_info(location):
    """Setting all information dict according to given location."""

    all_days_info = get_days_info(location)
    today_info = all_days_info.pop(0)
    time = get_local_time(location['country'])
    next_days_dates = get_next_days(7, time)
    location_wiki_info = get_location_summary(location)
    theme = get_theme(today_info[0])

    info = {
        'city': location['city'],
        'country': location['country'],
        'date': time.strftime("%a %d %b %Y").upper(),
        'time': time.strftime("%H:%M"),
        'today': today_info,
        'all_days_info': list(zip(next_days_dates, all_days_info)),
        'summary': location_wiki_info['summary'],
        'wiki_url': location_wiki_info['url'],
        'theme': theme,
        'sentence': sentences(theme),
    }

    return info
