# Import and return database
def get_database(name):
    if name == 'tmdb':
        from .tmdb import TmdbDatabase
        return TmdbDatabase()
    else:
        raise ValueError("Unknown database name")
