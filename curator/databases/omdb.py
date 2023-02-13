import bz2
import csv
import io
import logging
import math
import os

import arrow
import milli
import requests

from curator import Database

class OmdbDatabase(Database):
    def __init__(self):
        super().__init__("omdb")

        # Check if cached index exists
        suffix = arrow.utcnow().format('YYYY-MM-DD')
        cache_name = f'index_milli_{suffix}'
        cache_path = os.path.join(self.cache, cache_name)
        if os.path.exists(cache_path):
            self.ix = milli.Index(cache_path, 1024*1024*1024) # 1 GiB
            return

        # Otherwise create one
        logging.info("Creating movie index...")
        csv1 = self.get_omdb_dataset('all_movies')
        csv2 = self.get_omdb_dataset('all_movie_aliases_iso')
        movies = {}
        for row in csv1:
            movie_id = int(row['id'])
            movies[movie_id] = {
                'id': movie_id,
                'name': row['name'],
                'year': row['date'][:4],
                'aliases': [],
            }
        for row in csv2:
            movie_id = int(row['movie_id'])
            movie = movies.setdefault(movie_id, { 'id': movie_id, 'aliases': [] })
            movie['aliases'].append(row['name'])
        os.mkdir(cache_path)
        self.ix = milli.Index(cache_path, 1024*1024*1024) # 1 GiB
        self.ix.add_documents(list(movies.values()))

    def get_omdb_dataset(self, name):
        suffix = arrow.utcnow().format('MM_DD_YYYY')
        cache_name = f'{name}_{suffix}.csv.bz2'
        cache_path = os.path.join(self.cache, cache_name)
        if not os.path.exists(cache_path):
            r = requests.get(f'http://www.omdb.org/data/{name}.csv.bz2')
            with open(cache_path, 'wb') as f:
                f.write(r.content)

        # Parse compressed CSV dataset
        with open(cache_path, 'rb') as f:
            data = bz2.decompress(f.read())
        text = data.decode('utf-8')
        return csv.DictReader(io.StringIO(text), delimiter=',')

    def query(self, name, year=None):
        results = self.ix.search(name)
        if not results:
            return None
        movie = self.ix.get_document(results[0])
        return {
            'name': name,
            'oname': movie.get('name'),
            'year': movie.get('year'),
        }
