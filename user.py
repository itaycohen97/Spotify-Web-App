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

        self.user_personal_data = self.get_user_data()
        self.name = None
        self.spotify_id = None
        self.uri = None
        self.image = None

        self.top_artist = None
        self.top_tracks = None
        self.current_song = None
        self.latest_recommendation = None
        self.last_saved = None

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
        user = UserData()
        request = requests.get("https://api.spotify.com/v1/me", headers=self.get_headers())
        if request.status_code not in range(200, 299):
            print(str(request.status_code) + "is the status code for get user data")
            return user
        data = request.json()
        return user.from_json(data)

    def get_id(self):
        try:
            return str(self.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None

    def set_currently_playing(self, song):
        self.current_song = song


class UserData:

    def __init__(self, name=None, image=None, user_id=None, uri=None):
        self.name = name
        self.image = image
        self.spotify_id = user_id
        self.uri = uri

    def from_json(self, data):
        self.name = data.get("display_name", "No Name")
        self.spotify_id = data.get("id", "No ID")
        self.uri = data.get("uri", "No URI")
        if data["images"]:
            self.image = data["images"][0]["url"]
        else:
            self.image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQOWwtsGvuHl9CxFrQDLG0C-XXU9lpnLIY0jzohdM2I1g1DvjnOo8f1p7v9g7ad26mkXgs&usqp=CAU"
        return self
