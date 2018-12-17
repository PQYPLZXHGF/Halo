from datetime import datetime, timedelta

import pytz
import requests

from halo.DataStore import DataStore


class API:
    """
    This class is a wrapper for the Rest API endpoints of www.weatherbit.io.
    Currently it implements fetching current weather, forecast and 1 day
    (limit on free plan) historic weather data.
    """
    def __init__(self):
        self._base_url = "https://api.weatherbit.io/v2.0"
        self._headers = {'Accept': 'application/json', 'Accept-Charset': 'UTF-8'}

    def get_current_weather(self, query):
        """
        Fetches and returns current weather data.
        :param query: search query
        :return: a tuple containing city, city timezone, current weather data.
        """
        res = self._send_request(self._url_format("current", query))
        current_weather = {
            'status': res['data'][0]['weather']['description'],
            'code': res['data'][0]['weather']['code'],
            'temp': res['data'][0]['temp']
        }
        city = res['data'][0]['city_name'] + ", " + res['data'][0]['country_code']
        city_tz = res['data'][0]['timezone']
        DataStore().add_city((res['data'][0]['city_name'], res['data'][0]['country_code']))
        return city, city_tz, current_weather

    def get_forecast_weather(self, query):
        """
        Fetches and returns the forecast weather data.
        :param query: search query
        :return: forecast weather data.
        """
        query += "&days=5"
        res = self._send_request(self._url_format("forecast/daily", query))
        forecast_weather = res['data']
        return forecast_weather

    def get_forecast_weather_chart(self, query):
        """
        Fetches and returns the forecast weather chart data.
        :param query: search query
        :return: charting data.
        """
        query += "&days=5"
        res = self._send_request(self._url_format("forecast/3hourly", query))
        chart_data = [item['temp'] for item in res['data']]
        return chart_data

    def get_weather_history(self, query, tz):
        """
        Fetches and returns the historic weather data(1 day).
        :param query: search query
        :param tz: city timezone
        :return: historic weather data.
        """
        res = self._send_request(self._url_format("history/daily", query, tz))
        history_weather = res['data']
        return history_weather

    def get_weather_history_chart(self, query, tz):
        """
        Fetches and returns the historic weather data chart data(1 day).
        :param query: search query
        :param tz: city timezone
        :return: charting data.
        """
        res = self._send_request(self._url_format("history/hourly", query, tz))
        history_chart_data = [item['temp'] for item in res['data']]
        return history_chart_data

    def _url_format(self, slug, query, city_tz=None, days_count=1):
        if city_tz:
            start = datetime.now(pytz.timezone(city_tz)).replace(hour=0, minute=0, second=0, microsecond=0) \
                        .astimezone(pytz.utc) - timedelta(days=days_count)
            end = datetime.now(pytz.timezone(city_tz)).replace(hour=0, minute=0, second=0, microsecond=0) \
                .astimezone(pytz.utc)
            return "{base}/{slug}?{query}&start_date={start}&end_date={end}&key={key}"\
                .format(base=self._base_url, slug=slug, query=query,
                        start=start.strftime("%Y-%m-%d:%H"), end=end.strftime("%Y-%m-%d:%H"),
                        key=DataStore.get_api_key())
        else:
            return "{base}/{slug}?{query}&key={key}".format(base=self._base_url, slug=slug,
                                                            query=query, key=DataStore.get_api_key())

    def _send_request(self, url):
        try:
            r = requests.get(url, headers=self._headers)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 204:
                raise NotFound("The weather information for the requested city is not found.")
            elif r.status_code == 429:
                raise RateLimitReached("The API rate limit has reached. Please wait till it resets.")
            else:
                raise APIError("Something is broken. Please make sure your API key is valid or try again later.")
        except requests.ConnectionError:
            raise APIError("Something went wrong. Check your internet connection or please try again later.")


class APIError(Exception):
    pass


class NotFound(APIError):
    pass


class RateLimitReached(APIError):
    pass
