#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import json
import re

agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
headers = {'User-Agent': agent}
base = "https://www.azlyrics.com/"
searchBase = "https://search.azlyrics.com/search.php"

def artists(letter):
    if letter.isalpha() and len(letter) == 1:
        letter = letter.lower()
        url = base + letter + ".html"
        req = requests.get(url, headers=headers)
        soup = BeautifulSoup(req.content, "html.parser")
        data = []

def search(stext):
    sorry = "Sorry, I couldn't find any songs for the lyrics that you provided."
    # TODO: if reached 20, make a new request with pageNum++
    xReq = requests.get(base + 'geo.js', headers=headers) # Get key for search
    if xReq.status_code != 200:
        return "Could not get a valid response from server."
    x = re.search(r"\(\"value\", \"([^']*)\"\);", xReq.text).group(1) # ("value", "x");

    pageNum = 1
    searchUrl = searchBase + "?q=" + stext + "&w=lyrics&p=" + str(pageNum) + "&x=" + x
    searchReq = requests.get(searchUrl, headers=headers)
    soup = BeautifulSoup(searchReq.content, 'html.parser')
    searchResult = soup.find_all("td", attrs={"class": "visitedlyr", "id": None}) # Get the results
    if searchReq.status_code != 200:
        return "Could not get a valid response from server."
    elif not searchResult:
        return sorry
    else:
        resultDict = {} # Example: {'1': ['songTitle', 'lyricsResult', 'songLink'], ...}
        for r in searchResult:
            a = r.find('a', href=True)
            songNo = a.contents[0].rstrip('. ') # Get result number
            songTitle = a.contents[1].text + a.contents[2] + a.contents[3].text
            lyricsResult = r.a.small.text
            songLink = a['href']
            resultDict[songNo] = [songTitle, lyricsResult, songLink] # Add the result to the dict
        return resultDict


def songs(artist):
    sorry = "Sorry, I couldn't find any songs for '" + artist.strip() + "'."
    a = artist.lower().replace(" ", "")
    a = re.sub(r'[^A-Za-z0-9]', '', a) # [1] substitute everything except numbers and letters
    first_char = a[0]
    url = base + first_char + "/" + a + ".html"
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        return sorry
    soup = BeautifulSoup(req.content, 'html.parser')

    songs = {}
    all_albums = soup.find('div', id='listAlbum')
    first_album = all_albums.find('div', class_='album')
    album_name = first_album.get_text()
    songs[album_name] = []

    for tag in first_album.find_next_siblings('div'): # Go through all 'div' elements after first album
        if tag.get('class') is None:
            pass
        elif 'album' in tag.get('class'): # Found album, set the album
            album_name = tag.get_text()
            songs[album_name] = []
        elif 'listalbum-item' in tag.get('class'): # Found song, add it to current album
            songs[album_name].append(tag.text)
        else:
            pass

    return songs


def lyrics(artist, song):
    a = artist.lower().replace(" ", "")
    a = re.sub(r'[^A-Za-z0-9]', '', a) # [1] substitute everything except numbers and letters
    s = song.lower().replace(" ", "")
    s = re.sub(r'[^A-Za-z0-9]', '', s)
    url = base + "lyrics/" + a + "/" + s + ".html"
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")

    l = soup.find_all("div", attrs={"class": None, "id": None}, limit=1)
    l = [x.getText() for x in l]
    if not l:
        sorry = "Sorry, I couldn't find '" + song.strip() + "' by '" + artist.strip() + "'. Maybe try to 'Search by lyrics' ?"
        return sorry
    else:
        return l


def albums(artist):
    sorry = "Sorry, I couldn't find any albums for '" + artist.strip() + "'."
    a = artist.lower().replace(" ", "")
    a = re.sub(r'[^A-Za-z0-9]', '', a) # [1] substitute everything except numbers and letters
    first_char = a[0]
    url = base + first_char + "/" + a + ".html"
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        return sorry
    soup = BeautifulSoup(req.content, 'html.parser')

    all_albums = soup.find_all('div', class_='album') # [2] using find_all and get_text to get album names
    all_albums = [album.getText() for album in all_albums if album.getText() not in "other songs:"]
    
    return sorry if not all_albums else all_albums


def lyricsFromUrl(url):
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, "html.parser")

    l = soup.find_all("div", attrs={"class": None, "id": None}, limit=1)
    l = [x.getText() for x in l]
    if not l:
        sorry = "Something went wrong while getting the lyrics."
        return sorry
    else:
        return l

# [1] https://stackoverflow.com/a/23142281/2031851
# [2] https://stackoverflow.com/a/21997788/2031851