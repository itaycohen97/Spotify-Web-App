import requests, datetime, base64,SongLibrary, requests, os
from helpers import shorten_str


uri = os.environ.get('uri')

class User(object):
    def __init__(self, name, user_id, uri, image, top_tracks, current_song, top_artist, latest_recommendation,last_saved):
        self.name = name
        self.user_id = user_id
        self.image = image
        self.uri = uri
        self.top_tracks = top_tracks
        self.current_song = current_song
        self.top_artists = top_artist
        self.last_saved = last_saved
        self.latest_recommendation = latest_recommendation


class SpotifyApi(object):
    client_id = os.environ.get('client_id')
    client_secret = os.environ.get('client_secret')
    post_url = "https://accounts.spotify.com/api/token"
    scope = "playlist-modify-public playlist-modify-private user-library-read playlist-read-private user-read-currently-playing user-modify-playback-state user-top-read"
    get_url = "https://accounts.spotify.com/authorize"

    def __init__(self, code=None):
        self.user = User(None, None, None, None, None, None, None, None, None)
        self.code = code
        self.header = None
    


    def login_url(self):
        get_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": uri,
            "scope": self.scope
        }
        request = requests.get(url=self.get_url, params=get_params)
        print(request.url)
        return request

    def get_client_credentials(self):
        """
            Returns a base64 encoded string
            """
        client_creds = f"{self.client_id}:{self.client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def set_code(self, code):
        self.code = code

    def get_token(self):
        """
                    second part of logging in
                    """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.get_client_credentials()
        }
        body = {
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": uri,
        }
        request = requests.post(self.post_url, headers=headers, data=body)
        if request.status_code not in range(200, 299):
            print("First Login Failed, Status Code: " + request.status_code)
            return False
        data = request.json()
        now = datetime.datetime.now()
        # print(data)
        access_token = data['access_token']
        expires_in = data['expires_in']  # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        self.header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.access_token
        }
        return True

    def get_user_data(self):
        request = requests.get("https://api.spotify.com/v1/me", headers=self.header)
        if request.status_code not in range(200, 299):
            print(str(request.status_code) + "is the status code for get user data")
            return False
        # print(request.json())
        self.user.name = request.json()["display_name"]
        self.user.user_id = request.json()["id"]
        self.user.uri = request.json()["uri"]
        if request.json()["images"]:
            self.user.image = request.json()["images"][0]["url"]
        else:
            self.user.image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOWwtsGvuHl9CxFrQDLG0C-XXU9lpnLIY0jzohdM2I1g1DvjnOo8f1p7v9g7ad26mkXgs&usqp=CAU"
        return True

    def get_last_saved(self):
        request = requests.get("https://api.spotify.com/v1/me/tracks",
                               headers=self.header)
        request_json = request.json()
        songlist = []
        for song in request_json["items"]:
            song = SongLibrary.Song(
                name=shorten_str(song['track']['name']),
                album=song['track']['album']['name'],
                artist=song['track']['album']['artists'][0]['name'],
                release_date=song['track']['album']['release_date'],
                image=song['track']['album']['images'][1]['url'],
                link=song['track']['external_urls']['spotify'],
                popularity=song['track']['popularity'],
                id=song['track']['id'],
                uri=None
            )
            songlist.append(song)
        self.user.last_saved = songlist
        return songlist

    def recently_played(self):
        request = requests.get("https://api.spotify.com/v1/me/player/currently-playing?market=IL",
                               headers=self.header)
        if request.status_code == 204:
            print("recently played is None")
            return None
        if request.status_code not in range(200, 299):
            print(str(request.status_code) + "is the status code for get user data")
            return None
        request_json = request.json()
        song = SongLibrary.Song(
            name=shorten_str(request_json['item']['name']),
            artist=request_json['item']['artists'][0]['name'],
            album=request_json['item']['album']['name'],
            release_date=request_json['item']['album']['release_date'],
            image=request_json['item']['album']['images'][1]['url'],
            link=request_json['item']['external_urls']['spotify'],
            popularity=request_json['item']['popularity'],
            id=request_json['item']['id'],
            uri = request_json['item']['uri']
        )
        self.user.current_song = song
        return song

    def skip_to_next_song(self):
        request = requests.post("https://api.spotify.com/v1/me/player/next",
                                headers=self.header)
        return self.recently_played()
        

    def get_top_tracks(self):
        request = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=20&offset=0",
                               headers=self.header)
        request_json = request.json()
        song_list = [None] * 20
        for song in range(0, 20):
            song_list[song] = SongLibrary.Song(
                name=shorten_str(request_json["items"][song]['name']),
                album=request_json["items"][song]['album']['name'],
                artist=request_json["items"][song]['album']['artists'][0]['name'],
                release_date=request_json["items"][song]['album']['release_date'],
                image=request_json["items"][song]['album']['images'][1]['url'],
                link=request_json["items"][song]['external_urls']['spotify'],
                popularity=request_json["items"][song]['popularity'],
                id=request_json['items'][song]['id'],
                uri=request_json['items'][song]['uri']

            )
        self.user.top_tracks = song_list
        self.get_top_artists()
        return song_list

    def get_track_seeds(self):
        return self.user.top_tracks[0].id

    def get_artist_seed(self):
        result = self.user.top_artists[0].id
        result += ","
        result += self.user.top_artists[1].id
        return result

    def get_top_artists(self):
        request = requests.get("https://api.spotify.com/v1/me/top/artists?time_range=medium_term&limit=20&offset=0",
                               headers=self.header)
        request_json = request.json()["items"]
        artists = []
        for artist in request_json:
            artists.append(SongLibrary.Artist(
                name=artist['name'],
                followers=artist['followers']['total'],
                genres=artist['genres'],
                link=artist['external_urls']['spotify'],
                id=artist['id'],
                image=artist['images'][1]['url'],
                popularity=artist['popularity']
            ))
        self.user.top_artists = artists
        self.get_artist_seed()
        return artists

    def get_genres(self):
        request = requests.get("https://api.spotify.com/v1/recommendations/available-genre-seeds",
                               headers=self.header)
        request_json = request.json()
        return request_json['genres']

    def get_recommendation(self, genres, popularity, danceability, energy):
        seed_artists = self.get_artist_seed()
        seed_tracks = self.get_track_seeds()
        seed_genres = genres
        min_danceability = danceability - 0.2
        max_danceability = danceability + 0.2
        min_popularity = popularity - 20
        max_popularity = popularity + 20
        min_energy = energy - 0.2
        max_energy = energy + 0.2

        request = requests.get("https://api.spotify.com/v1/recommendations",
                               headers=self.header,
                               params={
                                   "limit": "10",
                                   "market": "IL",
                                   "seed_artists": seed_artists,
                                   "seed_genres": seed_genres,
                                   "seed_tracks": seed_tracks,
                                   "min_danceability": min_danceability,
                                   "max_danceability": max_danceability,
                                   "min_energy": min_energy,
                                   "max_energy": max_energy,
                                   "min_popularity": min_popularity,
                                   "max_popularity": max_popularity
                               })
        if request.status_code not in range(200, 299):
            print("Could Not get Reccomendations, Status Code: " + str(request.status_code))
            return False
        else:
            tracks = request.json()['tracks']
            if len(tracks) > 0:
                recommendation = []
                for track in tracks:
                    song = SongLibrary.Song(
                        name=track['name'],
                        artist=track['artists'][0]['name'],
                        link=track['album']['external_urls']['spotify'],
                        image=track['album']['images'][1]['url'],
                        album=track['album']['name'],
                        id=track['id'],
                        popularity=track['popularity'],
                        release_date=None,
                        uri=track['uri']
                    )
                    recommendation.append(song)
                self.user.latest_recommendation = recommendation
                return recommendation
            else:
                return False

    def make_playlist(self):
        request = requests.post(f"https://api.spotify.com/v1/users/{self.user.user_id}/playlists",
                                headers=self.header,
                                data="{\"name\":\"Latest Recommendations\",\"description\":\"Based On What You Hear\",\"public\":false}")
        if request.status_code not in range(200, 299):
            print("Could Not Make Playlist, Status Code: " + str(request.status_code))
            return False
        playlist_id = request.json()['id']
        uris = ""
        for item in self.user.latest_recommendation:
            if item:
                uris += item.uri
                uris += ","

        request = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                                headers=self.header,
                                params={
                                    "uris":uris
                                })
        if request.status_code not in range(200, 299):
            print("Could Not Add to Playlist, Status Code: " + str(request.status_code))
            return False
        playlist_url = "https://open.spotify.com/playlist/" + playlist_id
        return playlist_url


