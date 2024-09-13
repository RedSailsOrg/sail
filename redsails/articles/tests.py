import re
from html import unescape
from pathlib import Path

import requests

import pytest

from articles.management.commands import loaddata


def checkup(path, client):
    url = '/' + str(path.relative_to('/data/dst')).removesuffix('index.html')
    if '@' in url:
        url = url.rstrip('/')

    print(url)
    res = client.get(url)
    assert res.status_code == 200
    expected = path.read_text()
    expected = re.sub(r"\['N/A'\]", 'None', expected)

    found = res.content.decode()
    found = re.sub(re.escape('https://redsails.s3.amazonaws.com/'), '/', found)
    found = re.sub('"/media/', '"/', found)
    found = re.sub('</a><a class="author"', '</a>\n<a class="author"', found)
    assert expected == found


def test_mirror(db, client):
    loaddata.Command.handle()

    for root, dirs, files in Path('/data/dst').walk():
        for fn in files:
            path = root / fn
            if '-ch' in str(path):
                continue
            if path.name == 'index.html':
                checkup(path, client)
