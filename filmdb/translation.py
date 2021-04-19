from google_trans_new import google_translator

translator = google_translator()


def translate_in_romanian(content):
    return translator.translate(content, lang_src='en', lang_tgt='ro')
