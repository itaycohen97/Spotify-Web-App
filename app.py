from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from tempfile import mkdtemp
import SpotifyApi
from SpotifyApi import *

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def home(error=""):
    if 'user' in session:
        session['user'].recently_played()
        return render_template("home.html", user=session['user'].user, token=session['user'].access_token)
    return render_template("landing.html", error=error)


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
    return render_template("profile2.html", headline="Top Artists", user=session['user'], skip=skip())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = SpotifyApi()
        return redirect(session['user'].login_url().url)
    else:
        return redirect("/")


@app.route('/loggedin', methods=['GET', 'POST'])
def logged_in():
    if request.args.get('code'):
        session['user'].code = request.args['code']
        logged_in = session['user'].get_token()
        if logged_in:
            session['user'].get_user_data()
            return redirect("/")
        else:
            session.pop('user', None)
            return home(error="Sorry, Something Went Wrong...")
    else:
        session.pop('user', None)
        return home(error="Sorry, Something Went Wrong...")


def skip():
    session['user'].skip_to_next_song()
    print(session['user'].recently_played())


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'user' in session:

        if request.method == 'POST':
            session['user'].get_top_artists()
            session['user'].get_top_tracks()
            songlist = session['user'].get_recommendation(genres=request.form.get("genres"),
                                                          popularity=int(request.form.get("popularity")),
                                                          danceability=float(request.form.get("danceability")),
                                                          energy=float(request.form.get("energy")))
            if songlist:
                headline = "Here Are Some Songs We Think You'll Like!"
                return render_template("view_songs.html", user=session['user'].user, headline=headline,
                                       songlist=songlist, playlist_url=True)
            else:
                headline = "Sorry, Something Went Wrong..."
                return render_template("home.html", user=session['user'].user, headline=headline)

        else:
            genre = session['user'].get_genres()
            return render_template("rec_form.html", user=session['user'].user, genre=genre)
    else:
        return redirect("/")


@app.route('/makeplaylist')
def makeplaylist():
    data = session['user'].make_playlist()
    headline = "Here Are Some Songs We Think You'll Like!"
    return render_template("view_songs.html", user=session['user'].user, headline=headline,
                           songlist=session['user'].user.latest_recommendation,
                           success="Added to Spotify")


@app.route('/topartists')
def topartists():
    if 'user' in session:
        session['user'].recently_played()
        session['user'].get_top_artists()
        headline = "Top Artists"
        return render_template("view_artists.html", user=session['user'].user, headline=headline,
                               artists=session['user'].user.top_artists)
    return redirect("/")


@app.route('/toptracks')
def toptracks():
    if 'user' in session:
        session['user'].recently_played()
        session['user'].get_top_tracks()
        headline = "Top Tracks"
        return render_template("view_songs.html", user=session['user'].user, headline=headline,
                               songlist=session['user'].user.top_tracks)
    return redirect('/')


@app.route('/lastsaved')
def last_saved():
    if 'user' in session:
        session['user'].recently_played()
        session['user'].get_last_saved()
        headline = "Here Are Your Latest Saved Tracks"
        return render_template("view_songs.html", user=session['user'].user, headline=headline,
                               songlist=session['user'].user.last_saved)


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    session.pop('user', None)
    return render_template("500.html")


if __name__ == '__main__':
    app.run()
