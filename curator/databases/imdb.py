import csv
import gzip
import hashlib
import io
import logging
import math
import os

import arrow
import milli
import requests
import textdistance

from curator import Database
from curator.util import confirm

IMDB_DISCLAIMER = """IMDb Dataset Terms and Conditions:
By using this backend you agree to IMDb Datesets terms and conditions.
Read more at https://www.imdb.com/interfaces/ regarding compliance with
the IMdb Non-Commercial Licensing and copyright/license.

To proceed, please confirm that Curator and data at ~/.cache/curator/imdb
is and will be used *only* for personal and non-commercial purposes.
"""

IMDB_ACKNOWLEDGEMENT = """Information courtesy of IMDb (https://www.imdb.com).
Used with permission."""

class ImdbDatabase(Database):
    def __init__(self, cache_days):
        super().__init__("imdb")

        # Common suffix
        today = arrow.utcnow().format('YYYY-MM-DD')

        # Check IMDb terms
        terms_hash = hashlib.sha256(IMDB_DISCLAIMER.encode('utf-8')).hexdigest()[:32]
        terms_path = os.path.join(self.cache, f'terms_{terms_hash}')
        if not os.path.exists(terms_path):
            print(IMDB_DISCLAIMER)
            if confirm("Do you agree/confirm this?", default='no'):
                with open(terms_path, 'w') as f:
                    f.write(f'```\n{IMDB_DISCLAIMER}```\n\nAgreed on {today}.\n')
            else:
                print("Curator cannot continue without accepting the IMDb terms.")
                exit(0)
        print(IMDB_ACKNOWLEDGEMENT)

        # Check if cached index exists
        for day in range(cache_days):
            day = arrow.utcnow().shift(days=-day).format('YYYY-MM-DD')
            cache_name = f'index_milli_{day}'
            cache_path = os.path.join(self.cache, cache_name)
            if os.path.exists(cache_path):
                logging.info(f"Using cached movie index from {day}")
                self.ix = milli.Index(cache_path, 4*1024*1024*1024) # 4 GiB
                return

        # Otherwise create one
        logging.info("Creating movie index...")
        title_akas = self.get_imdb_dataset('title.akas')
        title_basics = self.get_imdb_dataset('title.basics')
        title_ratings = self.get_imdb_dataset('title.ratings')
        movies = {}
        for row in title_basics:
            if row['titleType'] != 'movie' or row['startYear'] == '\\N':
                continue
            movie_id = row['tconst']
            movies[movie_id] = {
                'id': movie_id,
                'name': row['primaryTitle'],
                'year': row['startYear'],
                'akas': [],
                'votes': 0,
            }
        for row in title_akas:
            movie_id = row['titleId']
            movie = movies.get(movie_id)
            if movie is None:
                continue
            movie['akas'].append(row['title'])
        for row in title_ratings:
            movie_id = row['tconst']
            movie = movies.get(movie_id)
            if movie is None:
                continue
            movie['votes'] = int(row['numVotes'])
        os.mkdir(cache_path)
        self.ix = milli.Index(cache_path, 4*1024*1024*1024) # 4 GiB
        self.ix.add_documents(list(movies.values()))

    def get_imdb_dataset(self, name):
        today = arrow.utcnow().format('YYYY-MM-DD')
        cache_name = f'{name}_{today}.tsv.gz'
        cache_path = os.path.join(self.cache, cache_name)
        if not os.path.exists(cache_path):
            r = requests.get(f'https://datasets.imdbws.com/{name}.tsv.gz')
            with open(cache_path, 'wb') as f:
                f.write(r.content)

        # Parse compressed CSV dataset
        with open(cache_path, 'rb') as f:
            data = gzip.decompress(f.read())
        text = data.decode('utf-8')
        return csv.DictReader(io.StringIO(text), delimiter='\t', quoting=csv.QUOTE_NONE)

    def query(self, name, year=None):
        results = self.ix.search(name)
        if not results:
            return None
        movies = self.ix.get_documents(results)
        if year is not None:
            movies = list(filter(lambda m: m['year'] == str(year), movies))
        if not movies:
            return None
        for movie in movies:
            titles = [movie['name']] + movie['akas']
            distance = min(map(lambda title: textdistance.levenshtein(title, name), titles))
            popularity = math.log10(movie['votes'] + 1)
            movie['score'] = popularity - distance
        movie = max(movies, key=lambda m: m['score'])
        return {
            'name': name,
            'oname': movie.get('name'),
            'year': movie.get('year'),
            'dbid': 'imdbid-' + movie.get('id'),
        }
