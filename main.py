from utils import get_random_word
import logging
import os
import json
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Chargement de la variable d'environemment TOKEN_BOT du fichir .env
load_dotenv()

# Activation du logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# La commande de base pour discuter avec le robot
# Elle sert également pour lancer une partie
def start(update, context):
    """Envoyer le message de démarrage quand la commande /start est exécutée."""

    mot_meta = get_random_word()
    mot = mot_meta[0].upper()
    lien = mot_meta[1]
    trouve = "*" * len(mot)

    meta = {
        "mot": mot,
        "lien": lien,
        "trouve": trouve
    }
    set_word_meta(update, meta)
    update.message.reply_text(f"Devinez le mot mystère\n\n" + trouve)


def reveler(update, context):
    # Récupération du mot mystère
    mot_dic = get_word_meta(update)
    mot_dic["trouve"] = mot_dic["mot"]
    set_word_meta(update, mot_dic)
    update.message.reply_text(f"Le mot mystère était {mot_dic['mot']}.\n\nPour plus d'informations : {mot_dic['lien']}")


def echo(update, context):
    """Gestion du message saisi par un joueur."""

    # Récupération du mot mystère
    mot_dic = get_word_meta(update)

    mot = mot_dic["mot"]
    trouve = list(mot_dic["trouve"])

    message = update.message.text.upper()
    if len(message) == 1:
        for i in range(len(mot)):
            if message == mot[i]:
                trouve[i] = mot[i]
        mot_dic["trouve"] = "".join(trouve)
        if mot_dic["trouve"] == mot:
            print_success_message(update, mot_dic)
        else:
            update.message.reply_text(f"Devinez le mot mystère\n\n" + mot_dic["trouve"])
    else:
        if message == mot:
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
        update.message.reply_markdown(f"*{update.message.from_user.first_name}* a trouvé le mot. C'était *{mot_dic['mot']}*.\n\nPour plus d'informations : {mot_dic['lien']}")
    else:
        update.message.reply_markdown(f"Bravo! Vous avez trouvé le mot. C'était *{mot_dic['mot']}*.\n\nPour plus d'informations : {mot_dic['lien']}")


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
