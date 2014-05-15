#!/usr/bin/env python
import os, sys
import glob
import re
import csv

from translate import Translator
from rosetta import polib

po_files = glob.glob("*/locale/*/LC_MESSAGES/*.po")

for po_file in po_files:
    m = re.search('locale/(\w+)/LC_', po_file)
    lang = m.group(1)

    csv_path = 'translations/'+lang+'.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'rb') as csvfile:
            table = csv.reader(csvfile)
            translations = {}
            for row in table:
                if len(row) == 0:
                    continue
                key = row[0].encode('utf8')
                translations[key] = row[1]

    else:
        continue

    po = polib.pofile(po_file)

    found = set()

    for entry in po:
        search = entry.msgid.encode('utf8')
        if search in translations:
            found.add(search)
            translation = translations[search].decode('utf8')
            entry.msgstr = translation

    print lang, len(found), "translations"
    print set(translations.keys()) - found, "unused"
    po.save()
