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

    nature = soup.find(class_='titredef')

    definiton = soup.ol.li

    if definiton.ul:
        definiton.ul.clear()
    definiton = definiton.getText()

    mot = header.get_text()
    lien = base + lien

    themes = ""
    if ")" in definiton:
        index = definiton.rfind(")")
        themes = definiton[:index+1].replace(") (", ", ").replace(")", "").replace("(", "").strip()
        definiton = definiton[index+1:].strip()

    indices = {
        "nature": nature.string,
        "definiton": definiton
    }

    if len(themes):
        indices["themes"] = themes

    return mot, lien, indices