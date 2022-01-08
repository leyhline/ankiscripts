#!/usr/bin/python3

"""
Perform OCR on all PNG images in current folder, then send text and images
(in WEBP format to save space) to Anki.

Requires:
    * imagemagick
    * tesseract
    * anki-connect <https://foosoft.net/projects/anki-connect/>
    * "Japanese sentences" model <https://ankiweb.net/shared/info/1557722832>

:copyright: (C) 2021 Thomas Leyh <thomas.leyh@mailbox.org>
:license: GPL-3.0-only, see LICENSE for more details.
"""

import json
from os import mkdir
from os.path import join
from pathlib import Path
import re
from subprocess import run

import pytesseract
import requests


RE_WHITESPACE = re.compile(r"""\s""")


def postprocess_text(text):
    return RE_WHITESPACE.sub("", text)


def create_note(text_image_path, webp_image_path):
    text = pytesseract.image_to_string(str(text_image_path), lang="jpn")
    text = postprocess_text(text)
    print(text_image_path.name, text, sep="\t")
    return {
        "deckName": "Learning",
        "modelName": "Japanese sentences",
        "fields": {
            "SentKanji": text,
            "Notes": "Pokemon_Sword 0 Badges"
        },
        "tags": ["Pokemon_Sword"],
        "picture": [{
            "path": str(webp_image_path.resolve()),
            "filename": webp_image_path.name,
            "fields": ["Image"]
        }]
    }


def create_notes():
    webps = list(Path("webp").glob("*.webp"))
    text_images = list(Path("text").glob("*.png"))
    assert len(webps) == len(text_images)
    webps.sort()
    text_images.sort()
    notes = [create_note(png, webp) for png, webp in zip(text_images, webps)]
    return {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": notes
        }
    }


def process_to_webp():
    mkdir("webp")
    run(["mogrify", "-path", "webp", "-format", "webp", "-quality", "30", "-resize", "960x540", "*.png", "*.png"])


def process_to_text_images():
    mkdir("text")
    run(["mogrify", "-path", "text", "-format", "png", "-crop", "531x106+624+496", "+repage", "-colorspace", "gray", "-color-threshold", "gray(50%)-gray(100%)", "*.png"])


def main():
    process_to_webp()
    process_to_text_images()
    notes_dict = create_notes()
    json_notes_dict = json.dumps(notes_dict)
    response = requests.post("http://localhost:8765", data=json_notes_dict)
    print(json.dumps(response.json(), indent=4))


if __name__ == "__main__":
    main()

