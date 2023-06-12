import subprocess
import pytesseract as tesseract
import sudachipy as sudachi
import re as regex
import xml.etree.ElementTree as ET

from pynput import keyboard
from gtts import gTTS

def get_text():
    subprocess.run(["clear"])
    subprocess.run(["scrot", "-s", "-f", "-o", "screenshot.png"])
    text = tesseract.image_to_string("screenshot.png", lang="jpn")
    text = regex.sub(r"[^\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF々]+", '', text)
    return text

def tokenize_text(tokenizer, text):
    tokens = tokenizer.tokenize(text)
    return tokens

def filter_tokens(tokens):
    excluded = [
            "助詞", # particle
            "格助詞", # case marking particle
            "助動詞", # inflecting dependent word
            "接頭辞", # prefix
            "感動詞", # interjection
            "固有名詞", # proper noun
            "人名", # person's name
            ]

    filtered_tokens = []
    for token in tokens:
        for i, p in enumerate(token.part_of_speech()):
            if p in excluded:
                break
            if i == len(token.part_of_speech()) - 1:
                filtered_tokens.append(token)
    return filtered_tokens

def search_dictionary(entries, words):
    results = {}

    for word in words:
        results.setdefault(word, [])

    for entry in entries:
        result = {
            "writing": [],
            "reading": [],
            "definition": []
        }
        kanji_elements = [keb.text for keb in entry.findall(".//keb")]
        reading_elements = [reb.text for reb in entry.findall(".//reb")]

        for e in kanji_elements:
            if e in words:
                result["writing"].append(kanji_elements)
                result["reading"].append(reading_elements)
                for sense in entry.findall("sense"):
                    sense_definition = [gloss.text for gloss in sense.findall("gloss")]
                    result["definition"].append(sense_definition)
                results[e].append(result)
        if not result["definition"]:
            for e in reading_elements:
                if e in words:
                    result["writing"].append(kanji_elements)
                    result["reading"].append(reading_elements)
                    for sense in entry.findall("sense"):
                        sense_definition = [gloss.text for gloss in sense.findall("gloss")]
                        result["definition"].append(sense_definition)
                    results[e].append(result)
    return results

def print_results(words, results):
    for i, word in enumerate(words):
        print("================================================================================")
        for j, result in enumerate(results[word]):
            if result["writing"][0]:
                print(result["writing"])
            print(result["reading"])
            for definition in result["definition"]:
                print("* ", definition)
            if j != len(results[word]) - 1:
                print("--------------------------------------------------------------------------------")
        if i == len(words) - 1:
            print("================================================================================")

def on_activate():
    text = get_text()
    tokens = tokenize_text(tokenizer, text);
    filtered_tokens = filter_tokens(tokens)
    # maybe only get dictionary_form() if is verb or adjective?
    words = [t.dictionary_form() for t in filtered_tokens]
    results = search_dictionary(entries, words)
    print_results(words, results)
    for token in filtered_tokens:
        print(token.dictionary_form(), token.part_of_speech())

    '''
    # tts function
    tts = gTTS(text=text, lang="ja")
    tts.save("output.mp3")
    '''
    '''
    # trying spacy
    nlp = spacy.load("ja_core_news_sm")
    out = nlp(text)
    for o in out:
        print(o.text, o.pos_)
    '''
    '''
    # clipboard function 
    subprocess.run(["xclip", "-selection", "clipboard", "-in"], input=text.encode("utf-8"))
    '''

print("loading...")
tokenizer = sudachi.Dictionary().create()
tree = ET.parse("dictionary.xml")
entries = tree.getroot().findall("entry")
print("done")

def for_canonical(f):
    return lambda k: f(l.canonical(k))

hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<alt>+a'),
    on_activate)
with keyboard.Listener(on_press=for_canonical(hotkey.press), on_release=for_canonical(hotkey.release)) as l:
    l.join()
