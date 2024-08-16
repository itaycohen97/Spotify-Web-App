import json
import os, requests, base64, datetime, logging
import time

from SongLibrary import *
from user import User

uri = os.environ.get('uri')
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
client_token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
post_url = "https://accounts.spotify.com/api/token"
scope = "playlist-modify-public playlist-modify-private user-library-read playlist-read-private user-read-currently-playing user-modify-playback-state user-top-read"
get_url = "https://accounts.spotify.com/authorize"
log = logging.getLogger()


def redirect_to_spotify_url():
    print(client_id)
    get_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": uri,
        "scope": scope
    }
    request = requests.get(url=get_url, params=get_params)
    return request.url


def generate_user(code: str):
    """
                    second part of logging in
                    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {client_token}"
    }
    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": uri,
    }
    request = requests.post(post_url, headers=headers, data=body)

    if request.status_code not in range(200, 299):
        print(f"First Login Failed, Status Code: {request.status_code}" )
        return None
    access_token_header = request.json()
    current_epoch = time.time()

    # Number of seconds to add
    seconds_to_add = 30

    # Calculate new epoch time
    new_epoch = current_epoch + seconds_to_add

    expires_in = datetime.datetime.now() + datetime.timedelta(seconds=access_token_header['expires_in'])

    usr_id = json.dumps([access_token_header['access_token'], int(time.time()+access_token_header['expires_in'])])
    return User(usr_id)


def get_currently_playing(header):
    request = requests.get("https://api.spotify.com/v1/me/player/currently-playing?market=IL",
                           headers=header)
    if request.status_code == 204:
        print("recently played is None")
        return None
    if request.status_code not in range(200, 299):
        print(str(request.status_code) + "is the status code for get user data")
        return None
    request_json = request.json()
    song = Song(
        name=request_json['item']['name'],
        artist=request_json['item']['artists'][0]['name'],
        album=request_json['item']['album']['name'],
        release_date=request_json['item']['album']['release_date'],
        image=request_json['item']['album']['images'][1]['url'],
        link=request_json['item']['external_urls']['spotify'],
        popularity=request_json['item']['popularity'],
        id=request_json['item']['id'],
        uri=request_json['item']['uri']
    )
    return song


# def get_user_data(user_credentials: User):
#     request = requests.get("https://api.spotify.com/v1/me", headers=user_credentials.get_headers())
#     if request.status_code not in range(200, 299):
#         print(str(request.status_code) + "is the status code for get user data")
#         return False
#     data = request.json()
#     # TODO: create new user object
#     print(data)
#     cur_user = {
#         "name": data["display_name"],
#         "user_id": data["id"],
#         "uri": data["uri"],
#         "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOWwtsGvuHl9CxFrQDLG0C-XXU9lpnLIY0jzohdM2I1g1DvjnOo8f1p7v9g7ad26mkXgs&usqp=CAU"
#     }
#     if request.json()["images"]:
#         cur_user["image"] = request.json()["images"][0]["url"]
#     return cur_user


def get_last_saved(header):
    request = requests.get("https://api.spotify.com/v1/me/tracks",
                           headers=header)
    request_json = request.json()
    songlist = []
    for song in request_json["items"]:
        song = Song(
            name=song['track']['name'],
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
    return songlist


def get_top_artists(header):
    request = requests.get("https://api.spotify.com/v1/me/top/artists?time_range=medium_term&limit=20&offset=0",
                           headers=header)
    request_json = request.json()["items"]
    artists = []
    for artist in request_json:
        artists.append(Artist(
            name=artist['name'],
            followers=artist['followers']['total'],
            genres=artist['genres'],
            link=artist['external_urls']['spotify'],
            id=artist['id'],
            image=artist['images'][1]['url'],
            popularity=artist['popularity']
        ))
    return artists


def get_top_tracks(header):
    request = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=20&offset=0",
                           headers=header)
    request_json = request.json()
    song_list = []
    for song in request_json["items"]:
        new_song = Song(
            name=song['name'],
            album=song['album']['name'],
            artist=song['album']['artists'][0]['name'],
            release_date=song['album']['release_date'],
            image=song['album']['images'][1]['url'],
            link=song['external_urls']['spotify'],
            popularity=song['popularity'],
            id=song['id'],
            uri=song['uri']
        )
        song_list.append(new_song)
    return song_list


def get_artist_seed(header):
    request = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=3&offset=0",
                           headers=header)
    request_json = request.json()
    result = request_json["items"][0]['id'] + "," + request_json["items"][1]['id']
    return result


def get_recommendation(header, genres, popularity, danceability, energy, seed_artists):
    seed_artists = seed_artists
    seed_genres = genres
    min_danceability = danceability - 0.2
    max_danceability = danceability + 0.2
    min_popularity = popularity - 20
    max_popularity = popularity + 20
    min_energy = energy - 0.2
    max_energy = energy + 0.2

    request = requests.get("https://api.spotify.com/v1/recommendations",
                           headers=header,
                           params={
                               "limit": "30",
                               "market": "IL",
                               "seed_artists": seed_artists,
                               "seed_genres": seed_genres,
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
                song = Song(
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
            return recommendation
        else:
            return False


def get_genres(header):
    request = requests.get("https://api.spotify.com/v1/recommendations/available-genre-seeds",
                           headers=header)
    request_json = request.json()
    return request_json['genres']


def make_playlist(header, user_data, uris):
    request = requests.post(f"https://api.spotify.com/v1/users/{user_data.spotify_id}/playlists",
                            headers=header,
                            data="{\"name\":\"Latest Recommendations\",\"description\":\"Based On What You Hear\",\"public\":false}")
    if request.status_code not in range(200, 299):
        print("Could Not Make Playlist, Status Code: " + str(request.status_code))
        return False
    playlist_id = request.json()['id']

    request = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                            headers=header,
                            params={
                                "uris": uris
                            })
    if request.status_code not in range(200, 299):
        print("Could Not Add to Playlist, Status Code: " + str(request.status_code))
        return False
    playlist_url = "https://open.spotify.com/playlist/" + playlist_id
    return playlist_url
