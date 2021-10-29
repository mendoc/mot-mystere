from utils import get_random_word
import logging
import os
import json
from random import randint
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
    indices = mot_meta[2]

    trouve = ""
    for lettre in mot:
        if lettre == " " or lettre == "-" or lettre == "'":
            trouve += lettre
        else:
            trouve += "*"

    meta = {
        "mot": mot,
        "lien": lien,
        "indices": indices,
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
    update.message.reply_markdown(
        "Le mot mystère était *" + mot_dic['mot'] + "*.\n\n_Définition_:\n" + mot_dic["indices"]["definition"] + "\n\n[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")")


def indice(update, context):
    # Récupération du mot mystère
    user = update.message.from_user.first_name
    mot_dic = get_word_meta(update)

    if not user in mot_dic["tentatives"] or mot_dic["tentatives"][user] > 5:
        update.message.reply_markdown("Trop tôt pour avoir des indices.")
        return

    indices = mot_dic["indices"]
    i = randint(0, len(indices)-1)
    key = [*indices][i]

    if key == "image":
        update.message.reply_photo(indices["image"])
    else:
        update.message.reply_markdown("*Indice:* \n\n_" + key.capitalize() + "_ :\n" + indices[key])


def get_indice_nature(update, context):
    get_indice(update, "nature")


def get_indice_definition(update, context):
    get_indice(update, "definition")


def get_indice_themes(update, context):
    get_indice(update, "themes")


def get_indice_image(update, context):
    indice = get_indice(update, "image")


def get_indice(update, key):
    # Récupération du mot mystère
    user    = update.message.from_user.first_name
    message = update.message.text.upper()
    mot_dic = get_word_meta(update)

    # Récupération des tentatives des joueurs
    tentatives = mot_dic["tentatives"]

    mot = mot_dic["mot"]

    if mot_dic["trouve"] == mot:
        update.message.reply_markdown("La partie est déjà terminée. 🙂")
        return False

    if user in tentatives and tentatives[user] < 1:
        update.message.reply_markdown("🗣 *" + user + "*, vous n'avez plus de tentatives.")
        return False

    if not user in mot_dic["tentatives"] or mot_dic["tentatives"][user] > 5:
        update.message.reply_markdown("Trop tôt pour avoir des indices.")
        return False
    
    indices = mot_dic["indices"]

    if not key in indices:
        if key == "image": update.message.reply_markdown("😔 Pas d'image displonible pour ce mot.")
        elif key == "themes": update.message.reply_markdown("😔 Aucun thème displonible pour ce mot.")
        return False

    indice = indices[key]
    if indice: 
        
        if key == "image":
            update.message.reply_photo(indice)
        else:
            update.message.reply_markdown("*Indice:* \n\n_" + key.capitalize() + "_ :\n" + indice)

        # Reduction du nombre de tentatives
        if user in tentatives:
            tentatives[user] = tentatives[user] - 1
        else:
            tentatives[user] = 9

        if tentatives[user] > 1:
                update.message.reply_markdown("*" + user + "*, il vous reste *" + str(tentatives[user]) + "* tentatives.")
        elif tentatives[user] == 1:
            update.message.reply_markdown("⚠️ *" + user + "*, il vous reste qu'une tentative.")
        else:
            update.message.reply_markdown("*" + user + "*, vous n'avez plus de tentatives.")

    mot_dic["tentatives"] = tentatives
    
    set_word_meta(update, mot_dic)


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
        else:
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
        msg += "*\n\n_Définition_:\n" + mot_dic["indices"]["definition"]
        msg += "\n\n" + "[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")"
        msg += "\n\n*Scores* :"

        # Affichage des scores des joueurs
        for joueur in mot_dic["scores"]:
            msg += '\n' + joueur + ': ' + str(mot_dic["scores"][joueur]) + ' points'

        update.message.reply_markdown(msg)
    else:
        update.message.reply_markdown(
            "Bravo! Vous avez trouvé le mot. \nC'était *" + mot_dic['mot'] +"*.\n\n"
            + "[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")")


def set_word_meta(update, mot_dic):
    # Sauvegarde du mot mystère
    fichier = open(str(update.message.chat.id) + ".json", "w")
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
    dp.add_handler(CommandHandler("nature", get_indice_nature))
    dp.add_handler(CommandHandler("definition", get_indice_definition))
    dp.add_handler(CommandHandler("themes", get_indice_themes))
    dp.add_handler(CommandHandler("image", get_indice_image))

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
