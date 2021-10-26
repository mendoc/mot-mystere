# Mot Mystère

---

## Description
Jeu consistant à deviner un mot choisit au hasard en proposant des lettres qui le compose. 

## Comment jouer ?
Ce jeu se joue sur Telegram. en procédant comme suit.
1. Démarrer une nouvelle conversation en recherchant **@PenduWikiBot**
2. Appuyer sur le bouton **DEMARRER** ou envoyer **/start**

## Executer en local
Il est possible de faire tourner le robot en local.
1. Cloner le dépôt
2. Créer un fichier `.env` en y ajoutant la ligne suivante :
```bash
TOKEN_BOT=1998987378:ABEwSgfigf1CXNZXZU_gArH0MONF0jJ3ufC
```
Adapter la valeur de `TOKEN_BOT` avec un token généré par [BotFather](https://core.telegram.org/bots).   
3. A la racine du projet, exécuter les commades suivantes pour installer les dépendances du projet :
```bash
pip install pipenv
python -m venv env
source env/bin/activate
pipenv install
```
4. Puis, exécuter le robot pour qu'il écoute les messages qui lui sont envoyés
```bash
pipenv run python main.py
```

## Prérquis
**Python 3.6** a été utilisé pour ce projet