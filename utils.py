#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup


def get_random_word():
    url = "http://tools.wmflabs.org/anagrimes/hasard.php?langue=fr"
    base = "https://fr.wiktionary.org"

    res = requests.get(url)

    soup = BeautifulSoup(res.content, 'html.parser')

    header = soup.find(id='firstHeading')
    lien = soup.find(id='ca-view').a.get('href')

    mot = header.get_text()
    lien = base + lien

    return mot, lien
