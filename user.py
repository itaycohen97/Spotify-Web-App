import json
import time
from datetime import datetime

import requests
from flask_login import UserMixin

# from spotify import get_user_data


class User(UserMixin):
    def __init__(self, id):

        self.id = id
        token, expiration = json.loads(id)
        self.token = token
        self.expiration = expiration
        self.name = None
        self.spotify_id = None
        self.uri = None
        self.image = None

        self.top_artist = None
        self.top_tracks = None
        self.current_song = None
        self.latest_recommendation = None
        self.last_saved = None

        self.get_user_data()

    def is_expired(self):
        return self.expiration < time.time()

    def time_to_expire(self):
        return self.expiration - time.time()

    def get_headers(self):
        if self.is_expired():
            return None
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.token
        }

    def to_cookie(self):
        return {
            "token": self.token,
            "expiration": str(self.expiration)
        }

    def get_user_data(self):
        request = requests.get("https://api.spotify.com/v1/me", headers=self.get_headers())
        if request.status_code not in range(200, 299):
            print(str(request.status_code) + "is the status code for get user data")
            return False
        data = request.json()
        self.name = data["display_name"]
        self.spotify_id = data["id"]
        self.uri = data["uri"]
        self.image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOWwtsGvuHl9CxFrQDLG0C-XXU9lpnLIY0jzohdM2I1g1DvjnOo8f1p7v9g7ad26mkXgs&usqp=CAU"

        if request.json()["images"]:
            self.image = request.json()["images"][0]["url"]
        return True

    def get_id(self):
        try:
            return str(self.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None

    def set_currently_playing(self, song):
        self.current_song = song



# class User:
#
#     def __init__(self, name, image, user_id, uri, top_artist, top_tracks, current_song, latest_recommendation,
#                  last_saved):
#         self.name = name
#         self.image = image
#         self.user_id = user_id
#         self.uri = uri
#