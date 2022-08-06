import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from dataclasses import dataclass


@dataclass
class Odcinek:
    number: float
    type: str

#players += [quality, hosting, translator, playerLink, hosNum]

@dataclass
class PlayerOption:
    quality: str
    hostingName: str
    translator: str
    embedLink: str

@dataclass
class DownloadLink:
    links: list
    episode: float
    season: float
    

episodes = []
series = ["pierwsza_seria", "naruto_shippuuden"] 

checkedCategory = ["oparte na mandze"]
allowedCategory = ["oparte na mandze"]

downloadLinks = []

epStart = 190
epEnd = 222
leftEpisodes = epEnd - epStart +1

for serieIndx in range(0, len(series)):
    if leftEpisodes <= 0:
        continue
    
    #Getting serie episodes list
    serie = series[serieIndx]
    siteUrl = "https://narutoboruto.wbijam.pl/" + serie + ".html"
    print("Searching episodes in: " + siteUrl)
    page = requests.get(siteUrl)
    if page.status_code != 200:
        print("Site couldn't be reached: " + str(page))
        exit()
    epTable = BeautifulSoup(page.content, 'html.parser').find(class_='lista').find_all("tr", class_='lista_hover')
    epTable.reverse()
    
    
    #Scrapping episode data
    allEpisodes=0
    for eps in epTable:
        allEpisodes+=1
        if(not epStart<= allEpisodes <= epEnd):
            continue
        epCategory = list(eps)[3].text
        if epCategory not in checkedCategory:
            allow = input("Download episode with this desc: " +
                            list(eps)[3].text + "? (Y/N) ")
            if allow=='Y' or allow=='y':
                allowedCategory+=[epCategory]
            checkedCategory+=[epCategory]
        if epCategory not in allowedCategory:
            print("Skipping episode number " + str(allEpisodes) + " (" + epCategory + ")")
            continue
        episodes+=[Odcinek(allEpisodes, epCategory)]
    print("Added " + str(len(episodes)) + " episodes to download")

    numLen = len(str(allEpisodes))
    
    #Scrapping players data
    links = []
    for episode in episodes:
        epLink = "https://narutoboruto.wbijam.pl/" + \
            serie + "-" + str(episode.number).zfill(numLen) + ".html"
        print("Searching videos in: " + epLink)
        page = requests.get(epLink)
        if page.status_code != 200:
            print("Site couldn't be reached: " + str(page))
            exit()

        rawPlayers = BeautifulSoup(page.content, 'html.parser').find(class_='lista').find_all("tr", class_='lista_hover')
        print("Found hostings: ")

        players = []

        
        #Scrapping embed Players URL and data
        for rawPlayer in rawPlayers:
            online = list(rawPlayer)[3].text
            hosting = list(rawPlayer)[5].text
            translator = list(rawPlayer)[7].text
            quality = list(rawPlayer)[9].text.replace(
                "oglądaj [", '').replace("]", '')
            embedLink = "https://narutoboruto.wbijam.pl/odtwarzacz-" + \
                list(rawPlayer)[9].find("span")["rel"] + ".html"

            if(online == "ONLINE"):
                players += [PlayerOption(quality, hosting, translator, embedLink)]
                print(str(len(players)) + ". " + translator +
                      " " + hosting + " " + quality)
                

        print("\n Choosing player: ")
        qualityList = ["FHD", "HD", "SD"]

        
        sources = []
        
        # class Player:
        #     quality: string
        #     hostingName: string
        #     translator: string
        #     embedLink: string

        for player in players:
            if player.quality in qualityList:
                if "cda" in player.hostingName or "sibnet" in player.hostingName:
                    playerSite = requests.get(player.embedLink)
                    srcLink = BeautifulSoup(
                        playerSite.content, "html.parser").find('iframe')['src']
                    sources += [srcLink]
                    print("Added player " + srcLink)
        downloadLinks+=[DownloadLink(sources, episode.number, serieIndx+1)]
    leftEpisodes-=len(episodes)
    epEnd-=allEpisodes
    if(epStart>allEpisodes):
        epStart-=allEpisodes
    else:
        epStart=1

for link in downloadLinks:
    ydl_opts = {
                'outtmpl': 'Naruto S' + str(link.season) + 'E' + str(link.episode).zfill(numLen) + '.mp4'
            }

    sourceIndx = 0
    retry = 1
    with YoutubeDL(ydl_opts) as ydl:
        while retry==1:
            retry=0
            try:
                ydl.download(link.links[sourceIndx])
            except:
                sourceIndx += 1
                retry=1
            
print('Done')
