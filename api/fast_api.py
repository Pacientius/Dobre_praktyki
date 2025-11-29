import csv

class Movie:
    def __init__(self, movieId, title, genres):
        self.movieId = movieId
        self.title = title
        self.genres = genres


class Link:
    def __init__(self, movieId, imdbId, tmdbId):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId


class Rating:
    def __init__(self, userId, movieId, rating, timestamp):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp


class Tag:
    def __init__(self, userId, movieId, tag, timestamp):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp



def load_movies():
    movies = []
    with open("files/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie = Movie(
                movieId=row["movieId"],
                title=row["title"],
                genres=row["genres"]
            )
            movies.append(movie.__dict__) 
    return movies

def load_links():
    items = []
    with open("files/links.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = Link(row["movieId"], row["imdbId"], row["tmdbId"])
            items.append(item.__dict__)
    return items

def load_ratings():
    items = []
    with open(r"files/ratings.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = Rating(row["userId"], row["movieId"], row["rating"], row["timestamp"])
            items.append(item.__dict__)
    return items

def load_tags():
    items = []
    with open("files/tags.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = Tag(row["userId"], row["movieId"], row["tag"], row["timestamp"])
            items.append(item.__dict__)
    return items
