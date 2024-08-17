from tempfile import mkdtemp

import flask_login
from flask import Flask, redirect, make_response, session, render_template, request
from flask_login import LoginManager, login_required, current_user
from flask_session import Session

from spotify import *

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@login_manager.user_loader
def load_user(user_id):
    # Replace this with your actual user loading logic
    # For example, loading user data from a database
    return User(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    # Handle unauthorized access here
    # You can return a JSON response, redirect to a login page, or any other desired action
    print(
        "unauthorized access, redirecting to login page"
    )
    return redirect("/")

@app.route('/')
def home(error=""):
    if current_user.is_authenticated:
        # print("user will expire in: " + str(current_user.time_to_expire()))
        current_user.set_currently_playing(get_currently_playing(current_user.get_headers()))
        return render_template("home.html", user=current_user, animations=True)
    return render_template("landing.html", error='')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(redirect_to_spotify_url())
    else:
        return redirect("/")


@app.route('/loggedin', methods=['GET', 'POST'])
def logged_in():
    if 'code' in request.args:
        user = generate_user(request.args['code'])
        if user:
            flask_login.login_user(user, remember=False, duration=datetime.timedelta(seconds=user.time_to_expire()), force=False, fresh=True)
            return redirect('/')
    else:
        print("something went wrong with the login")
        return home(error="Sorry, Something Went Wrong...")


@app.route('/logout')
def logout():
    print("logging out")
    return redirect("/")


@app.route('/recommend', methods=['GET', 'POST'])
@login_required
def recommend():
    if request.method == 'POST':
        user_seed = get_artist_seed(header=current_user.get_headers())
        songlist = get_recommendation(header=current_user.get_headers(), genres=request.form.get("genres"),
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
            result = make_response(render_template("view_songs.html", user=current_user, headline=headline,
                                                   songlist=songlist, playlist_url=True))
            result.set_cookie('tracks_uri', tracks_uri)
            return result
        else:
            headline = "Sorry, Something Went Wrong..."
            return render_template("home.html", user=current_user, headline=headline)

    else:
        genre = get_genres(header=current_user.get_headers())
        return render_template("rec_form.html", user=current_user, genre=genre)


@app.route('/makeplaylist')
@login_required
def makeplaylist():
    data = make_playlist(header=current_user.get_headers(), user_data=current_user, uris=request.cookies.get('tracks_uri'))
    headline = "Here Are Some Songs We Think You'll Like!"
    return redirect(data)


@app.route('/topartists')
@login_required
def topartists():
    top_artists = get_top_artists(header=current_user.get_headers())
    headline = "Here Are Your Top Artists"
    return render_template("view_artists.html", user=current_user, headline=headline,
                           artists=top_artists)


@app.route('/toptracks')
@login_required
def toptracks():
    top_tracks = get_top_tracks(header=current_user.get_headers())
    headline = "Top Tracks"
    return render_template("view_songs.html", user=current_user, headline=headline,
                           songlist=top_tracks)


@app.route('/lastsaved')
@login_required
def last_saved():
    last_saved = get_last_saved(header=current_user.get_headers())
    headline = "Here Are Your Latest Saved Tracks"
    return render_template("view_songs.html", user=current_user, headline=headline,
                           songlist=last_saved)


@app.errorhandler(500)
def internal_server_error(e):
    print(e)
    return render_template("500.html")


if __name__ == '__main__':
    app.run(port=5000, debug=True)
