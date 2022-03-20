from flask import Flask, render_template, request, redirect, make_response
from flask_session import Session
from tempfile import mkdtemp
import json
from SpotifyApi import *
from helpers import *
from spotify import *
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def define_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global current_session
        current_session = json.loads(request.cookies.get('current_session'))
        is_expired = datetime.strptime(current_session['expires'], '%m/%d/%Y, %H:%M:%S') < datetime.now()
        if is_expired is True:
            return redirect('/logout')
        global user_data
        try:
            user_data = json.loads(request.cookies.get('user_data'))
        except:
            user_data = get_user_data(current_session["header"])
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
@define_user
def home(error=""):
    user_data['current_song'] = recently_played(header=current_session['header'])
    return render_template("home.html", user=user_data, animations=True)


@app.route('/test')
def homepage():
    session['user'] = User(
        name="Itay Cohen",
        image="https://i.scdn.co/image/ab6775700000ee859bcdfe103aed2de2e665cb93",
        user_id=None,
        uri=None,
        top_artist=None,
        top_tracks=None,
        current_song=None,
        latest_recommendation=None,
        last_saved=None
    )
    return render_template("profile.html", headline="Top Artists", user=session['user'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(login_url())
    else:
        return redirect("/")


@app.route('/loggedin', methods=['GET', 'POST'])
def logged_in():
    if request.args.get('code'):
        get_login_data = get_token(request.args['code'])
        if get_login_data[0] == True:
            redirecting = redirect('/')
            cur_user = get_user_data(get_login_data[1]['header'])
            redirecting.set_cookie('current_session', json.dumps(get_login_data[1]))
            redirecting.set_cookie('user_data', json.dumps(cur_user))
            return redirecting
    else:
        session.pop('user', None)
        return home(error="Sorry, Something Went Wrong...")

@app.route('/logout')
def logout():
    loggedout = redirect("/")
    loggedout.delete_cookie("current_session")
    loggedout.delete_cookie("user_data")
    return loggedout


@app.route('/recommend', methods=['GET', 'POST'])
@login_required
@define_user
def recommend():
    if request.method == 'POST':
        user_seed = get_artist_seed(header=current_session['header'])
        songlist = get_recommendation(header=current_session['header'], genres=request.form.get("genres"),
                                                        popularity=int(request.form.get("popularity")),
                                                        danceability=float(request.form.get("danceability")),
                                                        energy=float(request.form.get("energy")), seed_artists=user_seed)
        if songlist:
            tracks_uri = ""
            for item in songlist:
                if item:
                  tracks_uri += item.uri
                  tracks_uri += ","
            headline = "Here Are Some Songs We Think You'll Like!"
            result = make_response(render_template("view_songs.html", user=user_data, headline=headline,
                                    songlist=songlist, playlist_url=True))
            result.set_cookie('tracks_uri', tracks_uri)
            return result
        else:
            headline = "Sorry, Something Went Wrong..."
            return render_template("home.html", user=user_data, headline=headline)

    else:
        genre = get_genres(header=current_session['header'])
        return render_template("rec_form.html", user=user_data, genre=genre)


@app.route('/makeplaylist')
@login_required
@define_user
def makeplaylist():
    data = make_playlist(header=current_session['header'], user_data=user_data, uris=request.cookies.get('tracks_uri'))
    headline = "Here Are Some Songs We Think You'll Like!"
    return redirect(data)

@app.route('/topartists')
@login_required
@define_user
def topartists():
    top_artists = get_top_artists(header=current_session['header'])
    headline = "Here Are Your Top Artists"
    return render_template("view_artists.html", user=user_data, headline=headline,
                            artists=top_artists)


@app.route('/toptracks')
@login_required
@define_user
def toptracks():
    top_tracks = get_top_tracks(header=current_session['header'])
    headline = "Top Tracks"
    return render_template("view_songs.html", user=user_data, headline=headline,
                            songlist=top_tracks)


@app.route('/lastsaved')
@login_required
@define_user
def last_saved():
        last_saved = get_last_saved(header=current_session['header'])
        headline = "Here Are Your Latest Saved Tracks"
        return render_template("view_songs.html", user=user_data, headline=headline,
                               songlist=last_saved)


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    return render_template("500.html")


if __name__ == '__main__':
    app.run()


