# Import and return database
def get_database(name, *args, **kwargs):
    if name == 'imdb':
        from .imdb import ImdbDatabase
        return ImdbDatabase(*args, **kwargs)
    if name == 'omdb':
        from .omdb import OmdbDatabase
        return OmdbDatabase(*args, **kwargs)
    if name == 'tmdb':
        from .tmdb import TmdbDatabase
        return TmdbDatabase(*args, **kwargs)
    else:
        raise ValueError("Unknown database name")
