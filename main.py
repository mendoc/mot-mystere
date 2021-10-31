from utils import get_random_word
import logging
import os
import json
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, CallbackContext

# Chargement de la variable d'environemment TOKEN_BOT du fichir .env
load_dotenv()

# Activation du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def set_word_meta(filename: str, mot_dic):
    # Sauvegarde du mot mystère
    fichier = open(filename, "w")
    json.dump(mot_dic, fichier, ensure_ascii=False)
    fichier.close()


def get_word_meta(filename: str):
    # Récupération du mot mystère
    fichier = open(filename, "r")
    mot_dic = json.load(fichier)
    fichier.close()

    return mot_dic


def print_success_message(update: Update, mot_dic):
    if update.message.chat.type == "group":
        msg = "*" + update.message.from_user.first_name + "* a trouvé le mot. \nC'était *" + mot_dic['mot'] + "*."
        msg += "\n\n" + "[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")"
        msg += "\n\n*Scores* :"

        # Affichage des scores des joueurs
        for joueur in mot_dic["scores"]:
            msg += '\n' + joueur + ': ' + str(mot_dic["scores"][joueur]) + ' points'

        update.message.reply_markdown(msg)
    else:
        update.message.reply_markdown(
            "Bravo! Vous avez trouvé le mot. \nC'était *" + mot_dic['mot'] + "*.\n\n"
            + "[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")")


# La commande de base pour discuter avec le robot
# Elle sert également pour lancer une partie

def start(update: Update, context: CallbackContext):
    """Envoyer le message de démarrage quand la commande /start est exécutée."""
    filename = str(update.message.chat.id) + ".json"

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

    mot_dic = {
        "mot": mot,
        "lien": lien,
        "indices": indices,
        "trouve": trouve,
        "propositions": [],
        "scores": {
            update.message.from_user.first_name: 0
        },
        "tentatives": {
            update.message.from_user.first_name: 10
        }
    }
    set_word_meta(filename, mot_dic)
    update.message.reply_text("Devinez le mot mystère\n\n" + trouve)


def reveler(update: Update, context: CallbackContext):
    # Récupération du mot mystère
    filename = str(update.message.chat.id) + ".json"
    mot_dic = get_word_meta(f"{update.message.chat.id}.json")
    mot_dic["trouve"] = mot_dic["mot"]
    set_word_meta(filename, mot_dic)
    update.message.reply_markdown(
        "Le mot mystère était *" + mot_dic['mot'] + "*.\n\n_Définition_:\n" + mot_dic["indices"][
            "definition"] + "\n\n[Plus d'informations sur Wiktionnaire](" + mot_dic["lien"] + ")")


def indice(update: Update, context: CallbackContext):
    user = update.message.from_user.first_name
    mot_dic = get_word_meta(f"{update.message.chat.id}.json")
    tentatives = mot_dic["tentatives"]

    if not user in tentatives or tentatives[user] > 5:
        update.message.reply_text("Trop tôt pour avoir des indices.")
        return

    mot = mot_dic["mot"]

    if mot_dic["trouve"] == mot:
        update.message.reply_text("La partie est déjà terminée. 🙂")
        return False

    if user in tentatives and tentatives[user] < 1:
        update.message.reply_markdown("🗣 *" + user + "*, vous n'avez plus de tentatives.")
        return False

    keyboard = [
        [InlineKeyboardButton("La nature du mot", callback_data='nature')],
        [InlineKeyboardButton("Les thèmes du mot", callback_data='themes')],
        [InlineKeyboardButton("Une image illustrative", callback_data='image')],
        [InlineKeyboardButton("La définition du mot", callback_data='definition')],
    ]

    boutons = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Quel indice voulez-vous ?', reply_markup=boutons)


def gerer_choix_indice(update: Update, context: CallbackContext):
    query = update.callback_query
    filename = str(query.message.chat.id) + ".json"
    user = query.from_user.first_name
    choix = query.data
    mot_dic = get_word_meta(filename)
    tentatives = mot_dic["tentatives"]
    message = "Indice indisponible"

    indices = mot_dic["indices"]
    if not choix in indices:
        if choix == "image":
            message = "😔 Pas d'image disponible pour ce mot."
        elif choix == "themes":
            message = "😔 Aucun thème disponible pour ce mot."
        query.answer()
        query.edit_message_text(message, parse_mode="markdown")
    else:
        if choix == "image":
            query.answer()
            query.message.reply_photo(indices["image"])
            query.edit_message_text("_Image illustrative_", parse_mode="markdown")
        else:
            # Affichage de l'indice
            message = choix.capitalize() + ":\n" + indices[choix]
            query.answer(message, show_alert=True)

            if choix == "definition":
                # Réduction du nombre de tentatives
                if user in tentatives:
                    tentatives[user] = tentatives[user] - 1
                else:
                    tentatives[user] = 9

                # Affichage du nombre de tentatives restant
                if tentatives[user] > 1:
                    query.edit_message_text("*" + user + "*, il vous reste *" + str(tentatives[user]) + "* tentatives.",
                                            parse_mode="markdown")
                elif tentatives[user] == 1:
                    query.edit_message_text("⚠️ *" + user + "*, il vous reste qu'une tentative.", parse_mode="markdown")
                else:
                    query.edit_message_text("*" + user + "*, vous n'avez plus de tentatives.", parse_mode="markdown")

                # Mise à jour des données de la partie
                mot_dic["tentatives"] = tentatives

                set_word_meta(filename, mot_dic)
            else:
                query.edit_message_text("_Consultation de l'indice_", parse_mode="markdown")


def echo(update: Update, context: CallbackContext):
    """Gestion du message saisi par un joueur."""

    user = update.message.from_user.first_name

    # Récupération du mot mystère
    mot_dic = get_word_meta(f"{update.message.chat.id}.json")

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

        # Ajout de la lettre dans les propositions
        if not message in mot_dic["propositions"]:
            mot_dic["propositions"].append(message)

        mot_dic["trouve"] = "".join(trouve)
        if mot_dic["trouve"] == mot:
            print_success_message(update, mot_dic)
        else:
            reponse = "Devinez le mot mystère\n\n" + mot_dic["trouve"]

            if len(mot_dic["propositions"]) > 0:
                reponse += "\n\nLettres déjà proposées:\n"
                reponse += " ".join(mot_dic["propositions"])

            update.message.reply_text(reponse)

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

    filename = str(update.message.chat.id) + ".json"
    set_word_meta(filename, mot_dic)


def error(update: Update, context: CallbackContext):
    """Gestion des erreurs."""
    logger.warning('Update "%s" \ncaused error "%s"', update, context.error)


if __name__ == '__main__':
    """Démarrage du robot."""

    TOKEN_BOT = os.getenv('TOKEN_BOT')
    updater = Updater(TOKEN_BOT, use_context=True)

    # Récupération du dispatcher
    dp = updater.dispatcher

    # Différentes commandes liées au robot
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("indice", indice))
    dp.add_handler(CommandHandler("reveler", reveler))

    updater.dispatcher.add_handler(CallbackQueryHandler(gerer_choix_indice))

    # Gestion des messages reçus de Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # Gestion des erreurs
    dp.add_error_handler(error)

    # Démarrage du robot
    updater.start_polling()

    # Gestion de l'intérruption du programme
    updater.idle()
