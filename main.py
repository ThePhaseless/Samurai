import requests
import os
import argparse
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from dataclasses import dataclass


parser = argparse.ArgumentParser(
    prog="main.py", description="Download anime from Wbijam.pl")

parser.add_argument("-n", "--name", help="Name of the anime")
parser.add_argument("-p", "--path", help="Base download path")
parser.add_argument(
    "-a", "--all", help="Download all episodes (without openings and etc)", action='store_true')
parser.add_argument(
    "-f", "--file", help="Download all anime from ")
args = parser.parse_args()


def check(list1, list2):
    for l1 in list1:
        for l2 in list2:
            if l1 == l2:
                return True
    return False


def searchForFiles(path):
    existingFiles = []
    path = (args.path or "./Downloads") + "\\" + path
    try:
        os.chdir(path)
    except:
        return {}
    for file in os.listdir():
        if "E" in file and ".mp4" in file and not ".part" in file:
            existingFiles += [int(file.replace(".mp4", "").replace("E", ""))]
    print("Found " + str(len(existingFiles)) + " downloaded episodes")
    return existingFiles


@dataclass
class Odcinek:
    number: float
    season: str
    type: str
    link: str
    players: list


@dataclass
class PlayerOption:
    server: str
    translator: str
    quality: str
    link: str


qualityList = ["FHD", "HD", "SD"]
supportedHostings = ['cda', 'sibnet', 'd-on']

animeNames = [args.name]
if args.file == None:
    if args.name == None:
        animeNames += [input("Enter name of the anime: ")]
else:
    f = open(args.file, "r")
    for animeName in f:
        animeNames += [animeName]

animeNames.pop(0)

for animeName in animeNames:
    # searching if anime exists
    page = requests.get("http://wbijam.pl/")
    if page.status_code != 200:
        print("Site http://wbijam.pl/ couldn't be reached: " + str(page))
        exit()
    animeTable = BeautifulSoup(page.content, 'html.parser').find(id='myTopnav').find_all(
        class_='dropdown')[2].find(class_='dropdown-content').find_all(class_='sub_link')

    found = False

    for anime in animeTable:
        if anime.text.lower().strip() == animeName.lower().strip():
            print("Anime found!")
            subLink = anime['href']
            found = True
            break

    if not found:
        print("Couldn't find anime with name: " + animeName)
        continue

    # scrapping season
    seasonNames = []
    seasonLinks = []
    page = requests.get(subLink)
    seasonsTable = BeautifulSoup(page.content, 'html.parser').find(id='myTopnav').find_all(
        class_='dropdown')[0].find(class_='dropdown-content').find_all('a')

    animeName = BeautifulSoup(page.content, 'html.parser').find(id='myTopnav').find_all(
        class_='dropdown')[0].find(class_='dropbtn').text.replace("\n        \n", "")
    animeNameOg = animeName
    for season in seasonsTable:
        if args.all and 'seria' in season.text:
            seasonLinks += [season['href']]
            seasonNames += [season.text]
            continue
        elif args.all:
            continue
        skipSeason = input("Search in season: " +
                           season.text + "? (Y/N/skip) ")
        if skipSeason.lower() == 'n':
            continue
        elif skipSeason.lower() == 'skip':
            print("Skipping rest of the seasons/extra")
            break
        elif skipSeason.lower() != 'y':
            print("Skipping this season")
            continue
        seasonLinks += [season['href']]
        seasonNames += [season.text]

    episodes = []

    checkedCategory = ["oparte na mandze"]
    allowedCategory = ["oparte na mandze"]

    for seasonIndx in range(0, len(seasonLinks)):
        # Getting season episodes list
        seasonName = seasonNames[seasonIndx]
        if 'seria' in seasonName:
            seasonName = 'S' + str(seasonIndx+1)
        elif args.all:
            continue
        seasonLink = seasonLinks[seasonIndx]
        fullUrl = subLink + seasonLink
        print("Searching episodes in: " + fullUrl)
        page = requests.get(fullUrl)
        if page.status_code != 200:
            print("Site couldn't be reached: " + str(page))
            exit()
        epTable = BeautifulSoup(page.content, 'html.parser').find(
            class_='lista').find_all("tr", class_='lista_hover')
        epTable.reverse()

        print("Found " + str(len(epTable)) + " episodes")

        if args.all == True:
            start = 1
            end = len(epTable)
        epStart = start or int(input("Start episode number from " +
                                     seasonNames[seasonIndx] + ": "))
        while (not 1 <= epStart <= len(epTable)):
            print("Start episode must be in range!")
            epStart = int(input("Start episode number from " +
                                seasonName[seasonIndx] + ": "))

        epEnd = end or int(input("Last episode number from this season: "))
        while (not 1 <= epEnd <= len(epTable)):
            print("End episode must be in range!")
            epEnd = int(input("Last episode number from this season: "))

        skipList = searchForFiles(animeNameOg + "//" + seasonName)
        # Scrapping episode data
        allEpisodes = 0
        for eps in epTable:
            allEpisodes += 1
            if allEpisodes in skipList:
                print("Episode " + str(allEpisodes) +
                      " already downloaded, skipping...")
                continue
            if (not epStart <= allEpisodes <= epEnd):
                continue
            if (allEpisodes > epEnd):
                break
            epCategory = list(eps)[3].text
            if epCategory not in checkedCategory:
                allow = input("Download episode with this desc: " +
                              list(eps)[3].text + "? (Y/N) ")
                if allow.lower() == 'y':
                    allowedCategory += [epCategory]
                checkedCategory += [epCategory]
            if epCategory not in allowedCategory:
                print("Skipping episode number " +
                      str(allEpisodes) + " (" + epCategory + ")")
                continue
            episodes += [Odcinek(allEpisodes, seasonName,
                                 epCategory, eps.find('td').find('a')['href'], [])]
        print("Added " + str(len(episodes)) + " episodes to queue")
        numLen = len(str(allEpisodes))

    # Scrapping players data
    for episode in episodes:
        epLink = subLink + episode.link
        print("Searching videos in: " + epLink)
        page = requests.get(epLink)
        if page.status_code != 200:
            print("Site couldn't be reached: " + str(page))
            exit()

        rawPlayers = BeautifulSoup(page.content, 'html.parser').find(
            class_='lista').find_all("tr", class_='lista_hover')

        if len(rawPlayers) == 0:
            print("Couldn't find any hosting for this episode, maybe it's not out yet")
            continue
        print("Found hostings: ")

        # Scrapping embed Players URL and data
        for rawPlayer in rawPlayers:
            online = list(rawPlayer)[3].text
            hosting = list(rawPlayer)[5].text
            translator = list(rawPlayer)[7].text
            quality = list(rawPlayer)[9].text.replace(
                "oglądaj [", '').replace("]", '')
            embedLink = subLink + "odtwarzacz-" + \
                list(rawPlayer)[9].find("span")["rel"] + ".html"

            if (online == "ONLINE"):
                if check(qualityList, quality.split(" + ")) == True:
                    if hosting in supportedHostings:
                        playerSite = requests.get(embedLink)
                        srcLink = BeautifulSoup(
                            playerSite.content, "html.parser").find('iframe')['src']
                        episode.players += [PlayerOption(hosting,
                                                         translator, quality, srcLink)]
                        print(str(len(episode.players)) + ". " + translator +
                              " " + hosting + " " + quality)

    print("Searching complete! \n \n")
    print("Starting downloads \n")

    for episode in episodes:
        ydl_opts = {
            'outtmpl': (args.path + "/" or './Downloads/') + animeName + '/' + episode.season + '/' 'E' + str(episode.number).zfill(numLen) + '.mp4'
        }
        with YoutubeDL(ydl_opts) as ydl:
            for player in episode.players:
                try:
                    ydl.download(player.link)
                except:
                    continue
                finally:
                    break

print('Done')
