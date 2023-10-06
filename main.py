from flask import Flask, render_template, request, redirect
import config
import json
from ytmusicapi import YTMusic


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=config.app_id, client_secret=config.app_secret))
yt = YTMusic('oauth.json')
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/submit")
def submit():
    # get the data from the form
    url = request.args.get('spotify-url', None)
    if not url:
        return render_template('home.html')
    playlist_id = url.split('/')[-1].split('?')[0]
    #https://open.spotify.com/playlist/54ZA9LXFvvFujmOVWXpHga
    playlist = spotify.playlist(playlist_id, additional_types=('track', ))
    tracks = []
    for track in playlist['tracks']['items']:
        track_name = track['track']['name']
        track_artist = track['track']['artists'][0]['name']
        year = track['track']['album']['release_date'].split('-')[0]
        tracks.append({
            'name': track_name,
            'artist': track_artist,
            'year': year
        })

    yt_playlist = yt.create_playlist(playlist['name'], description=playlist['description'])
    print(yt_playlist)
    count = 0
    total = len(tracks)
    for track in tracks:
        search = yt.search(f'{track["name"]} {track["artist"]} {track["year"]}')
        if not search:
            continue
        try:
            yt.add_playlist_items(yt_playlist, [search[0]['videoId']])
        except KeyError:
            continue
        count += 1
        print(f"{count}/{total} songs added")
    description = f'Created by {playlist["owner"]["display_name"]} on Spotify. Link to original playlist: {url} . Added {count} out of {total} songs. ... {playlist["description"]}'
    yt.edit_playlist(
        yt_playlist, 
        privacyStatus='PUBLIC', 
        description=description)
    link = f"https://music.youtube.com/playlist?list={yt_playlist}"
    return redirect(link, code=302)

if __name__ == '__main__':
    app.run(debug=True)
