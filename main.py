#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

import setupInfo
import re
from telegram import Update, constants
from telegram.utils.helpers import mention_markdown
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext,
                          ConversationHandler,
    PicklePersistence,
)
GETEEDITION = 1
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

PALAVRAS = "palavras"

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Esse Bot Marca a Morgana quando alguém fala uma palavra que caia '
                              'no filtro.\n'
                              '/changelist Inicia edição de lista de palavras\n'
                              '/cancel Cancela edição de palavras'
                              'Comandos do modo de edição:\n'
                              '"add <regex>" - Adiciona regex(es) separados por ";" ao filtro.\n'
                              '"ls" Para Listar os regex existentes.\n'
                              '"ls <palavra>" Para Listar retornar o(s) regex(es) que dão match.\n'
                              '"rm <indice>" Para remover um regex da lista.\n'
                              '"mv <indice> <regex>" Para altesrar um regex da lista.')


def change_list(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Digite os comandos. Use /cancel para sair do modo de edição.')

    return GETEEDITION


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Edição de palavra cancelada')

    return ConversationHandler.END


def new_word(update: Update, context: CallbackContext) -> int:
    logger.info('Getting Word')
    regex = update.message.text.lower()[len('add '):].split(';')
    context.bot_data[PALAVRAS].extend(regex)
    update.message.reply_text(f'Adicionando {regex} ao filtro.')

    return GETEEDITION


def remove_word(update: Update, context: CallbackContext) -> int:
    logger.info('Remove Word')
    index = int(update.message.text.lower().split('rm ')[1])
    try:
        del context.bot_data[PALAVRAS][index]
    except IndexError:
        logger.log('Index out of bounds')
        update.message.reply_text(f'{index} não existe. Por favor tente novamente.')
        return GETEEDITION

    update.message.reply_text(f'item {index} Removido com sucesso.')
    return GETEEDITION


def change_word(update: Update, context: CallbackContext) -> int:
    logger.info('Change Word')
    try:
        index = int(update.message.text.split(' ')[1])
        regex = update.message.text[update.message.text.find(str(index)) + len(str(index)) + 1:]
        context.bot_data[PALAVRAS][index] = regex
    except IndexError:
        logger.log('Index out of Bounds')
        update.message.reply_text(f'índice não existe. Por favor tente novamente.')
        return GETEEDITION
    update.message.reply_text(f'Palavra editada com sucesso.')

    return GETEEDITION


def checkMatch(regex: str, word: str) -> bool:
    return bool(re.search(regex, word, re.IGNORECASE))


def show_word(update: Update, context: CallbackContext) -> int:
    logger.info('Show Word')
    word = update.message.text.lower()[len('ls '):]
    entries = "".join([f'mv {index} {regex}\n' for index, regex in
                       enumerate(context.bot_data[PALAVRAS]) if checkMatch(regex, word)])
    if len(entries):
        update.message.reply_text(entries)
    else:
        update.message.reply_text(f'Não existe regex para {word}, use add <regex> para adicionar.')

    return GETEEDITION


def que_daniel(update: Update, context: CallbackContext) -> None:
    nome_el = re.match(r'.*(\b[A-Z]\w+el\b).*', update.message.text)
    update.message.reply_text(f'Que {nome_el.group(1)}?')


def que_larissa(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Que Larissa?')


def list_words(update: Update, context: CallbackContext) -> int:
    if len(context.bot_data[PALAVRAS]) > 0:
        wordList = "\n".join([
            f'{index} - {item}' for index, item in enumerate(context.bot_data[PALAVRAS])
        ])
        update.message.reply_text(wordList)
    else:
        update.message.reply_text('Nenhuma palavra registrada.')

    return GETEEDITION


def filterPutaria(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    regexCompilado = f'.*\\b({"|".join(context.bot_data[PALAVRAS])})\\b.*'
    if update.message\
            and checkMatch(regexCompilado, update.message.text)\
            and not update.message.from_user.id == 215849116\
            and not (update.message.reply_to_message and
                     update.message.reply_to_message.from_user.id == 215849116)\
            and all(entity.user.id != 215849116 for entity in update.message.parse_entities([
                         constants.MESSAGEENTITY_MENTION])):
        mention = mention_markdown(215849116, 'Morgana Burguesinha')
        update.message.reply_markdown(mention)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    pp = PicklePersistence(filename='botData.pickle')
    updater = Updater(setupInfo.TOKEN, persistence=pp, use_context=True)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.bot_data[PALAVRAS] = dispatcher.bot_data.get(PALAVRAS, [])
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('changelist', change_list)],
        states={
            GETEEDITION: [
                MessageHandler(Filters.regex(
                    re.compile('^add .*$', re.IGNORECASE)), new_word),
                MessageHandler(Filters.regex(
                    re.compile('^rm \d+$', re.IGNORECASE)), remove_word),
                MessageHandler(Filters.regex(
                    re.compile('^ls$', re.IGNORECASE)), list_words),
                MessageHandler(Filters.regex(
                    re.compile('^ls .*$', re.IGNORECASE)), show_word),
                MessageHandler(Filters.regex(
                    re.compile('^mv \d+ .*$', re.IGNORECASE)), change_word),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(
        MessageHandler(Filters.regex(re.compile(r'.*\bLarissa\b.*', re.IGNORECASE)), que_larissa)
    )
    dispatcher.add_handler(
        MessageHandler(Filters.regex(r'.*\b[A-Z]\w+el\b.*'), que_daniel)
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            filterPutaria))


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()