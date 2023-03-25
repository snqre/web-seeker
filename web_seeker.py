import requests, time, json, re, requests_cache, commando, concurrent.futures
from tqdm import tqdm
from bs4 import BeautifulSoup
from requests.exceptions import SSLError
from urllib3.exceptions import MaxRetryError
import pickle, itertools
import multiprocessing
import threading
requests_cache.install_cache("web_seeker_cache", expire_after=3600)
class Anime:
    def __init__(self, 
                 title ="", 
                 japanese_title ="",
                 url ="",
                 image_url ="",
                 type ="",
                 episodes ="",
                 status ="",
                 duration ="",
                 rating ="",
                 score ="",
                 rank ="",
                 popularity ="",
                 members ="",
                 synopsis ="",
                 season ="",
                 tags =[]):
        self.title=title
        self.japanese_title=japanese_title
        self.url=url
        self.image_url=image_url
        self.type=type
        self.episodes=episodes
        self.status=status
        self.duration=duration
        self.rating=rating
        self.score=score
        self.rank=rank
        self.popularity=popularity
        self.members=members
        self.synopsis=synopsis
        self.season=season
        self.tags=tags
# 500_000 to 1_000_000 for thorough scrape
def gen_anime_w_mal(cooldown=1, 
                    timeout=1, 
                    id=0, 
                    debug=False) -> Anime:
    time.sleep(cooldown)
    content =requests.get(f"https://api.jikan.moe/v4/anime/{id}/full")
    json_content =json.loads(json.dumps(content.json()))
    is_generating =True
    timeout=timeout
    while is_generating:
        if content.status_code ==200 and "data" in json_content:
            is_generating =False
            # generate tags
            tags =[]
            for genre_type in ["genres", "explicit_genres", "themes"]:      
                for genre in json_content["data"][genre_type]:
                    string =str(genre)
                    genre_match =re.search("'name': '([^']*)'", string)
                    if genre_match:
                        genre_name =genre_match.group(1)
                        tags.append(genre_name)
            # everything else
            title =json_content["data"]["title"]
            japanese_title =json_content["data"]["title_japanese"]
            url =json_content["data"]["url"]
            image_url =json_content["data"]["images"]["jpg"]["large_image_url"]
            type =json_content["data"]["type"]
            episodes =[]
            status =json_content["data"]["status"]
            duration =json_content["data"]["duration"]
            rating =json_content["data"]["rating"]
            score =json_content["data"]["score"]
            rank =json_content["data"]["rank"]
            popularity =json_content["data"]["popularity"]
            members =json_content["data"]["members"]
            synopsis =json_content["data"]["synopsis"]
            season =json_content["data"]["season"]
            # now glue it and make Anime
            return Anime(title=title, 
                        japanese_title=japanese_title, 
                        url=url, 
                        image_url=image_url, 
                        type=type, 
                        episodes=episodes, 
                        status=status, 
                        duration=duration, 
                        rating=rating, 
                        score=score, 
                        rank=rank, 
                        popularity=popularity, 
                        members=members, 
                        synopsis=synopsis, 
                        season=season, 
                        tags=tags)
        elif content.status_code in [429, 503, 420, 500] and timeout >=1:
            timeout -=1
            time.sleep(cooldown)
        else:
            is_generating =False
# multiple animes gen per page | 88 known pages
def gen_anime_w_gogo(page=1, n_episodes=2_700, debug=False, progress_bar=None) -> Anime:
    animes =[]
    content =requests.get(f"https://gogoanime.gr/anime-list.html?page={page}")
    if content.status_code ==200:
        html =BeautifulSoup(content.content, "html.parser")
        tags =html.find_all("a", href=lambda href: href and href.startswith("/category/"))
        for tag in tags:
            match =re.search(r'href="([^"]*)"', str(tag))
            if match:
                href =match.group(1)
                href =href[10:]
            anime_page =requests.get(f"https://gogoanime.gr/category/{href}")
            if debug ==True:
                print(f"{href}")
            html =BeautifulSoup(anime_page.content, "html.parser")
            image_url =re.findall(
                            r'src\s*=\s*"([^"]*)"', 
                            str(
                            html.find_all(
                            class_="anime_info_body_bg")))
            title =re.search(
                            r'<h1>(.*?)</h1>', 
                            str(
                            html.find_all(
                            class_="anime_info_body_bg")))
            title =title.group(1)
            type =html.find("span", string="Type: ")
            type =type.parent
            type =type.find("a")
            type =type.text
            synopsis =html.find("span", string="Plot Summary: ")
            synopsis =synopsis.next_sibling
            synopsis =str(synopsis)
            synopsis.strip()
            synopsis =re.sub(r'\s+', " ", synopsis)
            tags =html.find("span", string="Genre: ")
            tags =tags.parent
            tags =re.findall(r'<a href=".*?" title="(.*?)">', str(tags))
            status =html.find("span", string="Status: ")
            status =status.parent
            status =re.findall(r'<a href=".*?" title="(.*?)">', str(status))
            status =str(status)
            japanese_title =html.find("span", string="Other name: ")
            japanese_title =japanese_title.parent
            pattern =r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+'
            matches =re.findall(pattern, str(japanese_title))
            if matches:
                japanese_title =matches[0]
            iframes =[]
            for episode in range(n_episodes):
                try:
                    url =f"https://gogoanime.gr/{href}-episode-{episode}"
                    episode_page =requests.get(url)
                    if debug ==True:
                        print(f"{href}: episode: {url}")
                except (MaxRetryError, SSLError) as error:
                    pass
                if episode_page.status_code ==200:
                    html =BeautifulSoup(episode_page.content, "html.parser")
                    iframe =html.find("iframe")
                    match =re.search(r'<iframe.*?src="(.*?)".*?</iframe>', str(iframe), re.DOTALL)
                    if match:
                        iframe =match.group(1)
                        iframes.append(iframe)
                    episodes =[]
                    for iframe in iframes:
                        episodes.append(iframe)
            animes.append(Anime(title=title, 
                                japanese_title=japanese_title, 
                                url=f"https://gogoanime.gr/category/{href}", 
                                image_url=image_url, 
                                type=type, 
                                episodes=episodes, 
                                status=status,
                                synopsis=synopsis,
                                tags=tags))
        return animes
# get the full anime abstractions for mal and gogo with a little help from god
def gen_all_anime(total_pages=88,total_urls=1_000_000) -> Anime:
    # base benchmark for mal 17.5 days | 72 days: 100 threads | cf 2 - 6 hours : 100 threads
    animes=[]
    def chunk(start:int=None, end:int=None):
        for url in tqdm(range(start,end)):
            anime =gen_anime_w_mal(id=url)
            try:
                x =anime.title
                animes.append(anime)
            except:
                pass
    def use_threading(n_threads=total_urls):
        urls_per_thread =total_urls //n_threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
            future_to_url ={executor.submit(chunk, i*urls_per_thread, (i+1)*urls_per_thread): i for i in range(n_threads)}
            for future in concurrent.futures.as_completed(future_to_url):
                future.result()
    use_threading(n_threads=100)
    # clean none type animes
    for anime in animes:
        if anime =="None":
            del anime
    # start next mt process
    def chunk(start:int=None, end:int=None):
        for page in tqdm(range(start,end)):
            lst =gen_anime_w_gogo(page=page)
            # check if they have titles
            for i in range(len(lst)):
                try:
                    x =lst[i].title
                    animes.append(lst[i])
                except:
                    pass
    def use_threading(n_threads=total_pages):
        pages_per_thread =total_pages //n_threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
            future_to_page ={executor.submit(chunk, i*pages_per_thread, (i+1)*pages_per_thread): i for i in range(n_threads)}
            for future in concurrent.futures.as_completed(future_to_page):
                future.result()
    # return the animes
    return animes
def animes_to_json(animes=[]) -> Anime:
    """ save anime lists to json """
    serialized_data ={"animes": []}
    for anime in animes:
        title =anime.title
        japanese_title =anime.japanese_title
        url =anime.url
        image_url =anime.image_url
        type =anime.type
        episodes =anime.episodes
        status =anime.status
        duration =anime.duration
        rating =anime.rating
        score =anime.score
        rank =anime.rank
        popularity =anime.popularity
        members =anime.members
        synopsis =anime.synopsis
        season =anime.season
        tags =anime.tags
        serialized_data["animes"].append({"title": title, 
                                          "japanese_title": japanese_title, 
                                          "url": url, 
                                          "image_url": image_url, 
                                          "type": type, 
                                          "episodes": episodes, 
                                          "status": status, 
                                          "duration": duration, 
                                          "rating": rating, 
                                          "score": score, 
                                          "rank": rank, 
                                          "popularity": popularity, 
                                          "members": members, 
                                          "synopsis": synopsis, 
                                          "season": season, 
                                          "tags": tags})
    with open("animes.json","w") as f:
        json.dump(serialized_data, f, indent=4)
def json_to_animes() -> Anime:
    pass
"""
animes =gen_all_anime()
for anime in animes:
    print(anime.title)
animes_to_json(animes=animes)
"""
