from utils import get_random_word
import logging
import os
import json
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Chargement de la variable d'environemment TOKEN_BOT du fichir .env
load_dotenv()

# Activation du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# La commande de base pour discuter avec le robot
# Elle sert également pour lancer une partie


def start(update, context):
    """Envoyer le message de démarrage quand la commande /start est exécutée."""

    mot_meta = get_random_word()
    mot = mot_meta[0].upper()
    lien = mot_meta[1]
    
    trouve = ""
    for lettre in mot:
        if lettre == " " or lettre == "-":
            trouve += lettre
        else:            
            trouve += "*"

    meta = {
        "mot": mot,
        "lien": lien,
        "trouve": trouve,
        "scores": {
            update.message.from_user.first_name: 0
        },
        "tentatives": {
            update.message.from_user.first_name: 10
        }
    }
    set_word_meta(update, meta)
    update.message.reply_text("Devinez le mot mystère\n\n" + trouve)


def reveler(update, context):
    # Récupération du mot mystère
    mot_dic = get_word_meta(update)
    mot_dic["trouve"] = mot_dic["mot"]
    set_word_meta(update, mot_dic)
    update.message.reply_text(
        "Le mot mystère était " + mot_dic['mot'] + ".\n\nPour plus d'informations : \n" + mot_dic['lien'])


def echo(update, context):
    """Gestion du message saisi par un joueur."""

    user = update.message.from_user.first_name

    # Récupération du mot mystère
    mot_dic = get_word_meta(update)

    # Récupération des tentatives des joueurs
    tentatives = mot_dic["tentatives"]

    mot = mot_dic["mot"]
    trouve = list(mot_dic["trouve"])

    message = update.message.text.upper()

    if mot_dic["trouve"] == mot:
        return

    # On ne continue pas si le joueur n'a plus de tentatives
    if user in tentatives and tentatives[user] < 1 and len(message) == 1:
        update.message.reply_markdown("*" + user + "*, vous n'avez plus de tentatives.")
        return

    if len(message) == 1:
        for i in range(len(mot)):
            if message == mot[i]:
                if trouve[i] == "*":
                    if user in mot_dic["scores"]:
                        mot_dic["scores"][user] = mot_dic["scores"][user] + 1
                    else:
                        mot_dic["scores"][user] = 1
                trouve[i] = mot[i]

        mot_dic["trouve"] = "".join(trouve)
        if mot_dic["trouve"] == mot:
            print_success_message(update, mot_dic)
        else:
            update.message.reply_text(
                "Devinez le mot mystère\n\n" + mot_dic["trouve"])

        # Reduction du nombre de tentatives
        if user in tentatives:
            tentatives[user] = tentatives[user] - 1
        else:
            tentatives[user] = 9

        if tentatives[user] > 1:
            update.message.reply_markdown("*" + user + "*, il vous reste *" + str(tentatives[user]) + "* tentatives.")
        elif tentatives[user] == 1:
            update.message.reply_markdown("*" + user + "*, il vous reste qu'une tentative.")
        else :
            update.message.reply_markdown("*" + user + "*, vous n'avez plus de tentatives.")

    else:
        if (message == mot) and (user in tentatives) and (tentatives[user] > 0):
            if user in mot_dic["scores"]:
                mot_dic["scores"][user] = mot_dic["scores"][user] + mot_dic["trouve"].count("*")
            else:
                mot_dic["scores"][user] = mot_dic["trouve"].count("*")
            
            mot_dic["trouve"] = message
            print_success_message(update, mot_dic)

    set_word_meta(update, mot_dic)


def error(update, context):
    """Gestion des erreurs."""
    logger.warning('Update "%s" \ncaused error "%s"', update, context.error)


def get_word_meta(update):
    # Récupération du mot mystère
    fichier = open(f"{update.message.chat.id}.json", "r")
    mot_dic = json.load(fichier)
    fichier.close()

    return mot_dic


def print_success_message(update, mot_dic):
    if update.message.chat.type == "group":
        msg = "*" + update.message.from_user.first_name + "* a trouvé le mot. \nC'était *" + mot_dic['mot'] + "*."
        msg += "\n\nPour plus d'informations : \n" + mot_dic['lien']
        msg += "\n\n*Scores* :"

        # Affichage des scores des joueurs
        for joueur in mot_dic["scores"]:
            msg += '\n' + joueur + ': ' + str(mot_dic["scores"][joueur]) + ' points'

        update.message.reply_markdown(msg)
    else:
        update.message.reply_markdown(
            "Bravo! Vous avez trouvé le mot. \nC'était *" + mot_dic['mot'] +"*.\n\nPour plus d'informations : \n" + mot_dic['lien'])


def set_word_meta(update, mot_dic):
    # Sauvegarde du mot mystère
    fichier = open(f"{update.message.chat.id}.json", "w")
    json.dump(mot_dic, fichier, ensure_ascii=False)
    fichier.close()


def main():
    """Démarrage du robot."""

    TOKEN_BOT = os.getenv('TOKEN_BOT')
    updater = Updater(TOKEN_BOT, use_context=True)

    # Récupération du dispatcher
    dp = updater.dispatcher

    # Différentes commandes liées au robot
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("reveler", reveler))

    # Gestion des messages reçus de Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # Gestion des erreurs
    dp.add_error_handler(error)

    # Démarrage du robot
    updater.start_polling()

    # Gestion de l'intérruption du programme
    updater.idle()


if __name__ == '__main__':
    main()
