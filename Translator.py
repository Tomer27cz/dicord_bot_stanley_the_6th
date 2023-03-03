import googletrans
from database import text, language_list

translator = googletrans.Translator()

print(googletrans.LANGCODES)

for lang in language_list:
    print(lang)
    globals()[f'text_{lang}'] = dict(zip(text.keys(), text.values()))
    for i in text.keys():
        val_at_key = text[i]
        translated = translator.translate(val_at_key, dest=lang)
        globals()[f'text_{lang}'][i] = translated.text

for lang in language_list:
    print(f"text_{lang} = {globals()[f'text_{lang}']}")