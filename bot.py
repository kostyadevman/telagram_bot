from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
from os.path import join, exists
from os import makedirs
import logging
from config import TOKEN, keyboard_add_sentence, keyboard_create_lesson


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

CREATE_LESSON, GET_LESSON_NAME, ADD_SENTENCE, GET_EN_TEXT  = range(4)
EN_SOUND, GET_RU_TEXT, RU_SOUND, FROM_FILE, GET_SOUND = range(4,9)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    update.message.reply_text(
        'Invalid input'
    )
    logger.warning('Update "%s" caused error "%s"', update, error)


def start(bot, update, user_data):
    markup = ReplyKeyboardMarkup(
        keyboard_create_lesson,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    update.message.reply_text(
        'Hi! I am bot',
        reply_markup=markup
    )
    user_data['lesson_id'] = 1
    user_data['sentence_id'] = 1
    return CREATE_LESSON


def ask_lesson_name(bot, update):
    update.message.reply_text(
        'Give me the lesson name:'
    )
    return GET_LESSON_NAME


def get_lesson_name(bot, update, user_data):
    markup = ReplyKeyboardMarkup(
        keyboard_add_sentence,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    text = update.message.text
    lesson_name = 'NameLesson{} {}'.format(
        user_data['lesson_id'],
        text
    )
    user_data['lesson_name'] = lesson_name
    user_data['lesson_id'] += 1

    update.message.reply_text(
        'Lesson created! Now add the sentence',
        reply_markup=markup
    )
    return ADD_SENTENCE


def ask_en_text(bot, update):
    update.message.reply_text(
        'Write the english text:'
    )
    return GET_EN_TEXT


def get_en_text(bot, update, user_data):
    en_text = update.message.text
    user_data['en_text'] = en_text
    update.message.reply_text(
        'Make english sound:'
    )
    return EN_SOUND


def get_en_sound(bot, update, user_data):
    en_sound = bot.get_file(update.message.voice.file_id)
    en_sound_path = join(
        'data',
        user_data['lesson_name'],
        'EN'
    )

    if not exists(en_sound_path):
        makedirs(en_sound_path)
    en_sound_filename = join(
        en_sound_path,
        '{}_{}.{}'.format(
            user_data['sentence_id'],
            user_data['en_text'],
            'mp3'
        ))

    en_sound.download(en_sound_filename)
    update.message.reply_text(
        'Write the ru text:'
    )
    return GET_RU_TEXT


def get_ru_text(bot, update, user_data):
    ru_text = update.message.text
    user_data['ru_text'] = ru_text
    update.message.reply_text(
        'Make ru sound:'
    )
    return RU_SOUND


def get_ru_sound(bot, update, user_data):
    markup = ReplyKeyboardMarkup(
        keyboard_add_sentence,
        one_time_keyboard=True,
        resize_keyboard=True
    )

    ru_sound = bot.get_file(update.message.voice.file_id)
    ru_sound_path = join(
        'data',
        user_data['lesson_name'],
        'EN'
    )

    if not exists(ru_sound_path):
        makedirs(ru_sound_path)
    ru_sound_filename = join(
            ru_sound_path,
        '{}_{}.{}'.format(
            user_data['sentence_id'],
            user_data['en_text'],
            'mp3'
        ))
    user_data['sentence_id'] += 1
    ru_sound.download(ru_sound_filename)
    update.message.reply_text(
        'Add the sentence',
        reply_markup=markup
    )
    return ADD_SENTENCE


def ask_sentence_from_file(bot, update):
    update.message.reply_text(
        'Load the file with sentences ( *.txt )'
    )
    return FROM_FILE


def get_sentence_from_file(bot, update, user_data):
    file_with_sentences = bot.get_file(update.message.document.file_id)
    path_to_file = '{}.{}'.format(
        file_with_sentences.file_id,
        'txt'
    )
    file_with_sentences.download(path_to_file)

    with open(path_to_file, 'r', encoding='utf-8-sig') as input_file:
        sentences = input_file.read().splitlines()
    user_data['sentences'] = sentences
    update.message.reply_text(
        'Make sound: {} '.format(
            user_data['sentences'][0]
        )
    )

    user_data['language'] = 'EN'
    user_data['text'] = user_data['sentences'][0]
    del user_data['sentences'][0]
    return GET_SOUND


def get_sound(bot, update, user_data):

    sound = bot.get_file(update.message.voice.file_id)
    sound_path = join(
        'data',
        user_data['lesson_name'],
        user_data['language']
    )

    if not exists(sound_path):
        makedirs(sound_path)
    en_sound_filename = join(
        sound_path,
        '{}_{}.{}'.format(
            user_data['sentence_id'],
            user_data['text'],
            'mp3'
        ))
    print(en_sound_filename)
    sound.download(en_sound_filename)
    if not user_data['sentences']:
        markup = ReplyKeyboardMarkup(
            keyboard_add_sentence,
            one_time_keyboard=True,
            resize_keyboard=True
        )
        update.message.reply_text(
            'Add the sentence',
            reply_markup=markup
        )
        return ADD_SENTENCE
    update.message.reply_text(
        'make sound {} :'.format(
            user_data['sentences'][0]
        )
    )

    if (user_data['language'] == 'EN'):
        user_data['language'] = 'RU'
    else:
        user_data['sentence_id'] += 1
        user_data['language'] = 'EN'

    user_data['text'] = user_data['sentences'][0]

    del user_data['sentences'][0]
    return GET_SOUND


def done(bot, update, user_data):
    update.message.reply_text(
        'Lesson {} created, {} sentendes added'.format(
            user_data['lesson_name'],
            user_data['sentence_id']
        ))
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            CREATE_LESSON: [RegexHandler('^Create lesson$',
                                         ask_lesson_name
                                         ),
                            ],
            GET_LESSON_NAME: [MessageHandler(Filters.text,
                                             get_lesson_name,
                                             pass_user_data=True
                                             ),
                              ],
            ADD_SENTENCE: [RegexHandler('^Add Sentence$',
                                        ask_en_text
                                        ),
                           RegexHandler('^From file$',
                                        ask_sentence_from_file,
                                        ),
                           RegexHandler('^Done$',
                                        done,
                                        pass_user_data=True
                                        )
                           ],
            GET_SOUND: [MessageHandler(Filters.voice,
                                       get_sound,
                                       pass_user_data=True)
                        ],
            GET_EN_TEXT: [MessageHandler(Filters.text,
                                         get_en_text,
                                         pass_user_data=True
                                         )
                          ],
            EN_SOUND: [MessageHandler(Filters.voice,
                                      get_en_sound,
                                      pass_user_data=True
                                      )],
            GET_RU_TEXT: [MessageHandler(Filters.text,
                                         get_ru_text,
                                         pass_user_data=True
                                         )
                          ],
            RU_SOUND: [MessageHandler(Filters.voice,
                                     get_ru_sound,
                                      pass_user_data=True
                                     )
                       ],
            FROM_FILE: [MessageHandler(Filters.document,
                                       get_sentence_from_file,
                                       pass_user_data=True)
                        ]
        },

        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]

    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()