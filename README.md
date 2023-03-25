This is a Python script that scrapes anime information from two different websites, MyAnimeList and GogoAnime. The script imports several Python libraries, including requests, time, json, re, requests_cache, commando, concurrent.futures, tqdm, and BeautifulSoup.

The Anime class is defined to store anime information. The class contains various attributes, such as title, japanese_title, url, image_url, type, episodes, status, duration, rating, score, rank, popularity, members, synopsis, season, and tags.

The gen_anime_w_mal function generates anime information using the MyAnimeList website. It takes four parameters: cooldown, timeout, id, and debug. The function sleeps for a certain amount of time specified by the cooldown parameter, and then sends a request to the MyAnimeList API to get anime information for a specific anime ID. If the API is still generating the data, the function waits until the data is ready. Once the data is available, the function extracts the relevant anime information and creates an Anime object.

The gen_anime_w_gogo function generates anime information using the GogoAnime website. It takes three parameters: page, n_episodes, and debug. The function sends a request to the GogoAnime website to get a list of anime on a specific page. It then iterates over each anime on the page, sends a request to the anime's page to get more information, and extracts the relevant anime information to create an Anime object.

The script also installs a requests cache to reduce the number of requests made to the websites, and uses multiprocessing and threading to speed up the scraping process. Finally, the script handles various errors and retries requests if necessary.

This is mainly for educational purposes and for demonstrations, please check if these sites are happy with using these webscrapers and their data commercially.
