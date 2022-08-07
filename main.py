import requests
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from dataclasses import dataclass


@dataclass
class Odcinek:
    number: float
    type: str

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
    
animeName=input("Enter name of the anime: ")


#searching if anime exists
page = requests.get("http://wbijam.pl/")
if page.status_code != 200:
    print("Site http://wbijam.pl/ couldn't be reached: " + str(page))
    exit()
animeTable = BeautifulSoup(page.content, 'html.parser').find(id='myTopnav').find_all(class_='dropdown')[2].find(class_='dropdown-content').find_all(class_='sub_link')

for anime in animeTable:
    if anime.text.lower() == animeName.lower():
        print("Anime found!")
        subLink = anime['href']
        break

#scrapping series
seriesName = []
seriesLink = []
page = requests.get(subLink)
seriesTable = BeautifulSoup(page.content, 'html.parser').find(id='myTopnav').find_all(class_='dropdown')[0].find(class_='dropdown-content').find_all('a')

for serie in seriesTable:
    skipSerie=input("Search in season: " + serie.text + "? (Y/N/skip) ")
    if skipSerie.lower() == 'n':
        continue
    elif skipSerie.lower() == 'skip':
        print("Skipping rest of the seasons/extra")
        break
    elif skipSerie.lower() != 'y':
        print("Skipping this season")
        continue
    seriesLink+=[serie['href']]
    seriesName+=[serie.text]

episodes = []

checkedCategory = ["oparte na mandze"]
allowedCategory = ["oparte na mandze"]

downloadLinks = []

for serieIndx in range(0, len(seriesLink)):
    #Getting serie episodes list
    serieLink = seriesLink[serieIndx]
    siteUrl = subLink + serieLink
    print("Searching episodes in: " + siteUrl)
    page = requests.get(siteUrl)
    if page.status_code != 200:
        print("Site couldn't be reached: " + str(page))
        exit()
    epTable = BeautifulSoup(page.content, 'html.parser').find(class_='lista').find_all("tr", class_='lista_hover')
    epTable.reverse()
    
    print("Found " + str(len(epTable)) + " episodes")
    epStart=int(input("Start episode number from " + seriesName[serieIndx] + ": "))
    if(not 1 <= epStart < len(epTable)):
        print("Start episode must be in range!")
        exit()
    
    epEnd=int(input("Last episode number from this serie: "))
    if(not 1 <= epEnd < len(epTable)):
        print("End episode must be in range!")
        exit()
    
    #Scrapping episode data
    allEpisodes=0
    for eps in epTable:
        allEpisodes+=1
        if(not epStart <= allEpisodes <= epEnd):
            continue
        if(allEpisodes>epEnd):
            break
        epCategory = list(eps)[3].text
        if epCategory not in checkedCategory:
            allow = input("Download episode with this desc: " +
                            list(eps)[3].text + "? (Y/N) ")
            if allow.lower()=='y':
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
        epLink = subLink + serieLink.replace('.html', '') + "-" + str(episode.number).zfill(numLen) + ".html"
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
            embedLink = subLink + "odtwarzacz-" + \
                list(rawPlayer)[9].find("span")["rel"] + ".html"

            if(online == "ONLINE"):
                players += [PlayerOption(quality, hosting, translator, embedLink)]
                print(str(len(players)) + ". " + translator +
                      " " + hosting + " " + quality)
                

        print("\n Choosing player: ")
        

        
        sources = []
        
        # class Player:
        #     quality: string
        #     hostingName: string
        #     translator: string
        #     embedLink: string
        
        def check(list1, list2):
            for l1 in list1:
                for l2 in list2:
                    if l1==l2:
                        return True
            return False            
        
        qualityList = ["FHD", "HD", "SD"]
        supportedHostings=['cda', 'sibnet', 'd-on']
        
        for player in players:
            if check(qualityList, player.quality.split(" + ")) == True:
                if player.hostingName in supportedHostings:
                    playerSite = requests.get(player.embedLink)
                    srcLink = BeautifulSoup(
                        playerSite.content, "html.parser").find('iframe')['src']
                    sources += [srcLink]
                    print("Added player " + srcLink)
        downloadLinks+=[DownloadLink(sources, episode.number, seriesName[serieIndx])]

print("Searching complete! \n \n")
print("Starting downloads \n")

for link in downloadLinks:
    ydl_opts = {
                'outtmpl': './Downloads/' + animeName.capitalize() + '/' + link.season + '/' + animeName.capitalize() + ' E' + str(link.episode).zfill(numLen) + '.mp4'
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