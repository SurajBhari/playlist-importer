from flask import Flask, render_template, request, redirect
from flask import Response, stream_with_context
import config
import json
from ytmusicapi import YTMusic


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

redirect_uri = 'http://localhost:5000/callback'
spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.app_id, 
    client_secret=config.app_secret, 
    redirect_uri=redirect_uri, 
    scope='playlist-modify-public, playlist-modify-private'
    ))
user_id = spotify.me()['id']

yt = YTMusic('oauth.json')
app = Flask(__name__)

empty = "<script>document.body.innerHTML = '';</script>"
@app.route('/')
def home():
    return render_template('home.html')

def get_playlist_tracks(playlist_id):
    results = spotify.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    return [track['track'] for track in tracks]

@app.route("/styt")
def styt():
    def gen():
        try:
            # get the data from the form
            url = request.args.get('spotify-url', None)
            if not url:
                return render_template('home.html')
            playlist_id = url.split('/')[-1].split('?')[0]
            #https://open.spotify.com/playlist/54ZA9LXFvvFujmOVWXpHga
            playlist = get_playlist_tracks(playlist_id)
            p = spotify.playlist(playlist_id)
            description = p['description']
            owner = p['owner']['display_name']
            name = p['name']
            tracks = []
            for track in playlist:
                track_name = track['name']
                track_artist = track['artists'][0]['name']
                year = track['album']['release_date'].split('-')[0]
                tracks.append({
                    'name': track_name,
                    'artist': track_artist,
                    'year': year
                })
            yt_playlist = yt.create_playlist(name, description=description)
            link = f"https://music.youtube.com/playlist?list={yt_playlist}"
            print(link)
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
                yield empty
                yield f"{count}/{total} songs added </br>"
            description = f'Created by {owner} on Spotify. Link to original playlist: {url} . Added {count} out of {total} songs. ... {description}'
            yt.edit_playlist(
                yt_playlist, 
                privacyStatus='PUBLIC', 
                description=description)
            print('done')
            # clear the html page
            yield "done"
            yield "<script>document.body.innerHTML = 'REDIRECTING';</script>"
            yield f"<script>window.location = '{link}';</script>"
        except GeneratorExit:
            print('closed')
            yt.delete_playlist(yt_playlist)

    return Response(stream_with_context(gen()))


@app.route("/ytts")
def ytts():
    def gen():
        try:
            # get the data from the form
            url = request.args.get('yt-url', None)
            if not url:
                return render_template('home.html')
            playlist_id = url.split("?list=")[-1]
            playlist = yt.get_playlist(playlist_id)
            with open('playlist.json', 'w') as f:
                json.dump(playlist, f, indent=4)
            tracks = []
            name = playlist['title']
            description = playlist['description'] if playlist['description'] else ''
            for track in playlist["tracks"]:
                track_name = track['title']
                track_artist = track['artists'][0]['name']
                tracks.append({
                    'name': track_name,
                    'artist': track_artist,
                })
            playlist = spotify.user_playlist_create(
                user=user_id,
                name=playlist['title'], 
                description=description,
                public=True)
            count = 0
            total = len(tracks)
            for track in tracks:
                search = spotify.search(f'{track["name"]} {track["artist"]}', limit=1)
                if not search:
                    continue
                try:
                    spotify.playlist_add_items(playlist['id'], [search['tracks']['items'][0]['uri']])
                except KeyError:
                    continue
                count += 1
                yield empty
                yield f"{count}/{total} songs added </br>"
            print('done')
            yield "<script>document.body.innerHTML = 'REDIRECTING';</script>"
            playlist_link = f"https://open.spotify.com/playlist/{playlist['id']}"

            yield f"<script>window.location = '{playlist_link}';</script>"
        except GeneratorExit:
            print('closed')
            spotify.user_playlist_unfollow(config.user_id, playlist['id'])

    return Response(stream_with_context(gen()))
        
if __name__ == '__main__':
    app.run(debug=True)
