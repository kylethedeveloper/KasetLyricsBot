#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import json
import re

agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) \
        AppleWebKit/537.36 (KHTML, like Gecko) brave/0.7.11'
headers = {'User-Agent': agent}
base = "https://www.azlyrics.com/"

def artists(letter):
    if letter.isalpha() and len(letter) == 1:
        letter = letter.lower()
        url = base + letter + ".html"
        req = requests.get(url, headers=headers)
        soup = BeautifulSoup(req.content, "html.parser")
        data = []

        for div in soup.find_all("div", {"class": "container main-page"}):
            links = div.findAll('a')
            for a in links:
                data.append(a.text.strip())
        return json.dumps(data)
    else:
        raise Exception("Unexpected Input")


def songs(artist):
    artist = artist.lower().replace(" ", "")
    first_char = artist[0]
    url = base + first_char + "/" + artist + ".html"
    req = requests.get(url, headers=headers)

    artist = {
        'artist': artist,
        'albums': {}
    }

    soup = BeautifulSoup(req.content, 'html.parser')

    all_albums = soup.find('div', id='listAlbum')
    first_album = all_albums.find('div', class_='album')
    album_name = first_album.b.text
    s = []

    for tag in first_album.find_next_siblings(['a', 'div']):
        if tag.name == 'div':
            artist['albums'][album_name] = s
            s = []
            if tag.b is None:
                pass
            elif tag.b:
                album_name = tag.b.text

        else:
            if tag.text == "":
                pass
            elif tag.text:
                s.append(tag.text)

    artist['albums'][album_name] = s

    return json.dumps(artist)


def lyrics(artist, song):
    a = artist.lower().replace(" ", "")
    a = re.sub(r'[^A-Za-z0-9]', '', a) # [1] substitute everything except numbers and letters
    s = song.lower().replace(" ", "")
    s = re.sub(r'[^A-Za-z0-9]', '', s)
    url = base + "lyrics/" + a + "/" + s + ".html"

    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")
    l = soup.find_all("div", attrs={"class": None, "id": None})
    if not l:
        sorry = "Sorry, I couldn't find '" + song.strip() + "' by '" + artist.strip() + "'. Maybe try to /searchbylyrics ?"
        return sorry
    elif l:
        l = [x.getText() for x in l]
        return l


def debuging(artist):
    artist = artist.lower().replace(" ", "")
    first_char = artist[0]
    url = base + first_char + "/" + artist + ".html"
    req = requests.get(url, headers=headers)

    artist = {
        'artist': artist,
        'albums': {}
    }

    soup = BeautifulSoup(req.content, 'html.parser')

    all_albums = soup.find('div', id='listAlbum')
    first_album = all_albums.find('div', class_='album')
    print(first_album)

#debuging(artistName)

# [1] https://stackoverflow.com/a/23142281/2031851
