# Import and return database
def get_database(name):
    if name == 'omdb':
        from .omdb import OmdbDatabase
        return OmdbDatabase()
    if name == 'tmdb':
        from .tmdb import TmdbDatabase
        return TmdbDatabase()
    else:
        raise ValueError("Unknown database name")
