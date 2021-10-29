#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup


def get_random_word():
    url = "http://tools.wmflabs.org/anagrimes/hasard.php?langue=fr"
    base = "https://fr.wiktionary.org"

    res = requests.get(url)

    soup = BeautifulSoup(res.content, 'html.parser')

    header = soup.find(id='firstHeading')
    lien   = soup.find(id='ca-view').a.get('href')
    nature = soup.find(class_='titredef')
    image  = soup.find(class_='thumbimage')

    definition = soup.ol.li

    if definition.ul:
        definition.ul.clear()
    definition = definition.getText()

    mot = header.get_text().replace('’', '\'')
    lien = base + lien

    themes = ""
    if ")" in definition:
        index = definition.rfind(")")
        themes = definition[:index+1].replace(") (", ", ").replace(")", "").replace("(", "").strip()
        definition = definition[index+1:].strip()

    indices = {
        "nature": nature.string,
        "definition": definition
    }

    if len(themes):
        indices["themes"] = themes

    if (image):
        indices["image"] = "https:" + image.get('src')

    return mot, lien, indices