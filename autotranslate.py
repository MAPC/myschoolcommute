#!/usr/bin/env python
import os, sys
import glob
import re

from translate import Translator
from rosetta import polib

po_files = glob.glob("*/locale/*/LC_MESSAGES/*.po")

for po_file in po_files:
    m = re.search('locale/(\w+)/LC_', po_file)

    translator = Translator(to_lang=m.group(1))

    po = polib.pofile(po_file)

    for entry in po.untranslated_entries():
        try:
            translation = translator.translate(entry.msgid.encode('utf8'))
            print translation
            entry.msgstr = translation
        except KeyError:
            print "ERROR:" + entry.msgid
            raise

    po.save()
