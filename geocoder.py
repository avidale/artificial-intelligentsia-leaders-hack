import json
import logging
import math
import os
import requests


logger = logging.getLogger(__name__)


def text_to_address(text, token=None):
    if token is None:
        token = os.environ.get('GEOCODER_TOKEN')
    if token is None:
        raise ValueError('GEOCODER_TOKEN variable is not set')
    r = requests.get('https://geocode-maps.yandex.ru/1.x', params={
        'geocode': text,
        'apikey': token,
        'format': 'json',
    })
    if not r.ok:
        logger.warning('Geocoder request bad code {}, text: {}'.format(r.status_code, r.text))
        return
    pois = r.json()['response']['GeoObjectCollection']['featureMember']
    if not pois:
        logger.warning('Geocoder search for "{}" is empty'.format(text))
        return
    poi = pois[0]['GeoObject']
    return Address.from_geo_object(poi)


class Address:
    def __init__(self, lat=None, lon=None, text=None, geo_object=None, raw_address=None):
        self.lat = lat
        self.lon = lon
        self.text = text
        self.geo_object = geo_object
        self.raw_address = raw_address

    def __repr__(self):
        return 'Address(lat={}, lon={}, text="{}")'.format(self.lat, self.lon, self.text, )

    @classmethod
    def from_geo_object(cls, data):
        lon, lat = [float(x) for x in data['Point']['pos'].split()]
        text = data['metaDataProperty']['GeocoderMetaData']['text']
        return cls(lat=lat, lon=lon, text=text, geo_object=data)

    @property
    def short_text(self):
        return shorten_address(self.text)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def to_dict(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'text': self.text,
            'geo_object': self.geo_object,
            'raw_address': self.raw_address
        }


def shorten_address(text):
    parts = text.split()
    if parts[0] == 'Россия,':
        parts = parts[1:]
    if parts[0] == 'Москва,':
        parts = parts[1:]
    result = ' '.join(parts)
    return result


class GeoCache:
    def __init__(self, token=None):
        self.token = token
        self.cache = {}
    def __call__(self, address_text):
        if not self.cache.get(address_text):
            address = text_to_address(address_text, token=self.token)
            if not address:
                return None
            self.cache[address_text] = address
        return self.cache[address_text]
    def save(self, filename):
        data = {k: v.to_dict() for k, v in self.cache.items()}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    def load(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            self.cache = {k: Address.from_dict(v) for k, v in json.load(f).items()}


def geo_distance(addr1, addr2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = math.radians(addr1.lat)
    lon1 = math.radians(addr1.lon)
    lat2 = math.radians(addr2.lat)
    lon2 = math.radians(addr2.lon)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
