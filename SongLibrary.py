class Song(object):
    def __init__(self, name, artist, album, release_date, image, link, popularity, id, uri):
        self.name = name
        self.artist = artist
        self.album = album
        self.release_date = release_date
        self.image = image
        self.link = link
        self.id = id
        self.popularity = popularity
        self.uri = uri

    def __repr__(self):
        return f"song name: {self.name}, artist: {self.artist}, album: {self.album}, release_date: {self.release_date}, image: {self.image}, link: {self.link}, id: {self.id}, popularity: {self.popularity}, uri: {self.uri}"




class Artist(object):
    def __init__(self, name, genres, followers, id, image, popularity, link):
        self.name = name
        self.genres = genres
        self.followers = followers
        self.id = id
        self.image = image
        self.popularity = popularity
        self.link = link

    def print(self):
        print("---------------------------")
        print("Name:", self.name)
        print("genres:", self.genres)
        print("followers:", self.followers)
        print("link:", self.link)
        print("image:", self.image)
        print("id:", self.id)
