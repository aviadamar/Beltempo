from datetime import datetime, timedelta
import re
import requests

from countryinfo import CountryInfo
from decouple import config
from flask import request
import geocoder
from geopy.geocoders import Nominatim
from geotext import GeoText
import pycountry
import pytz
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


def get_location_by_name(name):
    """Get location information by given name."""
    location = {'lat': None, 'lon': None, 'city': None, 'country': None}
    if is_country(name):
        location['country'] = name.title()
        location['city'] = get_capital(name)
    elif is_city(name):
        location['city'] = name.title()
        location['country'] = find_country(name)
    else:
        is_location(location)
    location['lat'], location['lon'] = get_location_latlon(
        f"{location['city']} {location['country']}")
    return location


def get_location_summary(location):
    """Returns wikipedia summary for value."""
    return {'url': wikipedia.page(location).url, 'summary': wikipedia.summary(location, chars=1000)}


def is_location(location, dcity="London", dcountry="United Kingdom"):
    """Checks if we got a valid location from ip.

    In case of invalid location the function will insert a defaults values.
    """
    if location['city'] is None or location['country'] is None:
        location['city'], location['country'] = dcity, dcountry
    return None


def is_country(name):
    """Checks if a given name represent a country."""
    check = pycountry.countries.get(name=name)
    return check is not None


def is_city(name):
    """Checks if a given name is a city"""
    places = GeoText(name.title())
    return len(places.cities) > 0


def find_country(city):
    """finds the country of a given city."""
    search = city
    result = GeoText(wikipedia.summary(search, sentences=3))
    return result.countries.pop(0)


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
def get_timezone(capital):
    """Return timezone code by capital."""
    try:
        for tzone in pytz.all_timezones:
            if capital in tzone:
                return tzone
    except UnknownTimeZoneError:
        return 'Etc/Greenwich'


def get_local_time(country):
    """Returns time at user location."""
    capital = get_capital(country)
    user_time_zone = get_timezone(capital)
    t = pytz.timezone(user_time_zone)
    date = t.localize(datetime.now())
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
    themes = ('sun', 'rain', 'clouds', 'storm')
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
    evarage_temp = [round((float(j.group(1)) + float(j.group(2))) / 2)
                    for j in matches2]
    match_pic = [get_theme(description) +
                 ".svg" for description in description_list]

    info = list(zip(description_list, evarage_temp, match_pic))
    del info[0]
    return info


def setting_info(location):
    """Setting all information dict according to given location."""

    all_days_info = get_days_info(location)
    today_info = all_days_info.pop(0)
    time = get_local_time(location['country'])
    next_days_dates = get_next_days(7, time)
    location_wiki_info = get_location_summary(location['city'])

    info = {
        'city': location['city'],
        'country': location['country'],
        'date': time.strftime("%a %d %b %Y").upper(),
        'time': time.strftime("%H:%M"),
        'today': today_info,
        'all_days_info': list(zip(next_days_dates, all_days_info)),
        'summary': location_wiki_info['summary'],
        'wiki_url': location_wiki_info['url'],
        'theme': get_theme(today_info[0]),
    }

    print(info)
    return info
