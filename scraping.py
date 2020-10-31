import requests
from bs4 import BeautifulSoup

from urllib.parse import parse_qs

def google_img(text, extra='книга+обложка'):
    r = requests.get('https://www.google.ru/search?q={}+{}'.format(text.replace(' ', '+'), extra))
    soup = BeautifulSoup(r.text)
    href = soup.find('img').parent.parent['href']
    return parse_qs(href.split('?', 1)[1])['imgurl'][0]
