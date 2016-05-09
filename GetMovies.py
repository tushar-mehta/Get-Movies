from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError,URLError
import requests
import subprocess
import pickle
import argparse
import json


# Returns all movies and it's page url
def get_movie_list(url):
    cont = requests.get(url)

    if cont.status_code == 200:
        soup = BeautifulSoup(cont.content, 'html.parser')
        movielinks = soup.find_all("a", class_="movielink")

        movies_data = []
        for movie in movielinks:
            movies_data.append((movie.string, movie['href']))

        return movies_data


# Returns all movies and it's torrent url
def get_movie_torrent_url(url):
    #print(url)
    cont = requests.get(url)

    if cont.status_code == 200:
        soup = BeautifulSoup(cont.content, 'html.parser')

        torrent_urls = soup.find_all('a', id="dt")
        return torrent_urls[0]['href']


# Saves torrent file of from given url
def get_movie_torrent(url):
    torrent_file = url.rsplit('/', 1)[1]
    print("downloading ", url)
    try:
        #headers = { 'User-Agent': 'Mozilla/5.0' }
        r = requests.get(url, headers='', stream=True)
        with open(torrent_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=32*1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
    except requests.exceptions.RequestException as e:
        print('\n' + OutColors.LR + str(e))
        sys.exit(1);


def search_movie(movie_name, movies):
    # Look for exact movie name match
    if movie_name in movies:
        print('Movie Name:{0}'.format(movie_name))
        print('Movie Torrent:{0}'.format(movies[movie_name]))
        return

    # Look for movie name as a keyword in list of movies (keys)
    movie_list = list(movies.keys())
    movies_found = [movie for movie in movie_list if movie_name.lower() in movie.lower()]

    for movie in movies_found:
        print('Found:{0} - {1}'.format(movie, movies[movie]))


if __name__ == '__main__':

    movie_resolution = '1080p'
    pages = 2
    # movies read from movies.json
    movies = {}

    movie_name = ''

    parser = argparse.ArgumentParser(description='Happy Movie Watching!')
    parser.add_argument('-m',  help='provide movie name')
    parser.add_argument('--resolution',  help='provide movie resolution')

    args = parser.parse_args()

    if args.m:
      movie_name = args.m

    if args.resolution:
      movie_resolution = args.resolution

    try:
        with open('movies.json', 'r') as f:
            movies = json.load(f)
    except IOError as e:
        print("warning: 'movies.json' not found")

    if movie_name:
        print('Searching for {0}...'.format(movie_name))
        search_movie(movie_name, movies)

    movies_data = []
    for page in list(range(1, pages+1)):
        url = 'https://yifymovie.re/search/0/{0}/All/0/latest/60/page/{1}/'.format(movie_resolution, page)

        # Get the list of tuples (movie name, url which contains link to torrent file)
        print("Crawling ", url)

        movies_per_page = get_movie_list(url)

        if not movies_per_page:
            print("Crawling is done.")
            break

        movies_data += movies_per_page;
        #print(movies_data)

    data_len = len(movies_data)
    for count, movie in enumerate(movies_data):
        if movie[0] not in movies:
            print("Retrieving torrent url {0}/{1} - {2}...".format(count+1, data_len, movie[0]))
            movies[movie[0]] = get_movie_torrent_url(movie[1]);

    # we found new movies from website
    if movies:
        try:
            print("Saving data to movies.json...")
            with open('movies.json', 'w') as f:
                json.dump(movies, f)
        except IOError as e:
            print("warning:failed to dump 'movies.json'")

        #import pdb
        #pdb.set_trace()