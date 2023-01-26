import gzip
import math
import os
import sqlite3

import arrow
import pandas as pd
import requests
from textdistance import levenshtein

from curator import Database

class TmdbDatabase(Database):
    def __init__(self):
        super().__init__("tmdb")

        # Get movie IDs from TMDB, and cache them
        suffix = arrow.utcnow().shift(days=-1).format('MM_DD_YYYY')
        cache_name = f'movie_ids_{suffix}.json.gz'
        cache_path = os.path.join(self.cache, cache_name)
        if not os.path.exists(cache_path):
            r = requests.get(f'http://files.tmdb.org/p/exports/{cache_name}')
            with open(cache_path, 'wb') as f:
                f.write(r.content)

        # Parse movie IDs table
        with open(cache_path, 'rb') as f:
            data = gzip.decompress(f.read())
        text = data.decode('utf-8')
        df = pd.read_json(text, lines=True)

        # Convert to FTS5-enabled SQLite databse
        db = sqlite3.connect(':memory:')
        db.execute('CREATE VIRTUAL TABLE movie_ids USING fts5(id, original_title, popularity, adult, video);')
        df.to_sql('movie_ids', db, if_exists='append', index=False)
        self.db = db

    def get_year(self, id):
        return None # TODO

    def query_exact(self, name, year=None):
        results = self.db.execute(
            f'''SELECT original_title, popularity, id FROM movie_ids
                WHERE original_title = "{name}"
                ORDER BY popularity''').fetchall()
        if year:
            results = list(filter(lambda r: year == self.get_year(r[2]), results))
        if not results:
            return None
        r = max(results, key=lambda r: r[1])
        return {
            'name': r[0],
            'year': self.get_year(r[2]),
        }

    def query_fuzzy(self, name, year=None):
        results = self.db.execute(
            f'''SELECT original_title, popularity, id FROM movie_ids
                WHERE original_title MATCH "{name}" AND popularity >= 0.61
                ORDER BY popularity''').fetchall()
        def score(record):
            original_title, popularity = record[:2]
            distance = levenshtein.distance(original_title, name)
            if distance == 0:
                return math.inf
            return popularity * 1/distance
        r = max(results, key=score)
        return {
            'name': r[0],
            'year': self.get_year(r[2]),
        }

    def query(self, name, year=None):
        match = self.query_exact(name, year)
        if match:
            return match
        match = self.query_fuzzy(name, year)
        if match:
            return match
        return None
