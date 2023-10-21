from flask import Flask, render_template, request, redirect
from flask import Response, stream_with_context
import config
import json
from ytmusicapi import YTMusic
import pprint

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

pp = pprint.PrettyPrinter(indent=4).pprint
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

try:
    f = open("playlist.json", "r")
except FileNotFoundError:
    with open("playlist.json", "w") as f:
        f.write(json.dumps({
            "yt": {},
            "spotify": {}
        }))
    all_playlist = {
        "yt": {},
        "spotify": {}
    }
else:
    all_playlist = json.loads(f.read())

@app.route('/')
def home():
    return render_template('home.html')

def get_spotify_playlist_items(playlist_id):
    results = spotify.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    return [track['track'] for track in tracks]

def get_playlist_id(pid):
    return spotify.playlist(pid)['id']


"""
Spotify to Youtube converer
"""
@app.route("/styt")
def styt():
    def gen():
        # get the data from the form
        url = request.args.get('spotify-url', None)
        if not url:
            return render_template('home.html')
        playlist_id = get_playlist_id(url.split('/')[-1].split('?')[0]) # make sure we sanitize the id
        #https://open.spotify.com/playlist/54ZA9LXFvvFujmOVWXpHga
        spotify_tracks = get_spotify_playlist_items(playlist_id)
        spotify_playlist = spotify.playlist(playlist_id)
        spotify_description = spotify_playlist['description']
        spotify_owner = spotify_playlist['owner']['display_name']
        spotify_name = spotify_playlist['name']
        if playlist_id in all_playlist['yt']:
            yt_playlist =yt.get_playlist(all_playlist['yt'][playlist_id])
            if yt_playlist['tracks']:
                print(yt_playlist['tracks'])
                yt.remove_playlist_items(yt_playlist['id'], yt_playlist['tracks'])
        else:
            yt_playlist = yt.create_playlist(title=spotify_name, description=spotify_description)
        to_add_tracks = []
        for track in spotify_tracks:
            track_name = track['name']
            track_artist = track['artists'][0]['name']
            year = track['album']['release_date'].split('-')[0]
            to_add_tracks.append({
                'name': track_name,
                'artist': track_artist,
                'year': year
            })
        
        link = f"https://music.youtube.com/playlist?list={yt_playlist['id']}"
        print(link)
        total = len(to_add_tracks)
        try:
            count = 0
            for track in to_add_tracks:
                search = yt.search(f'{track["name"]} {track["artist"]} {track["year"]}')
                if not search:
                    continue
                try:
                    yt.add_playlist_items(yt_playlist['id'], [search[0]['videoId']])
                except KeyError:
                    continue
                count += 1
                yield empty
                yield f"{count}/{total} songs added </br>"
            description = f'Created by {spotify_owner} on Spotify. Link to original playlist: {url} . Added {count} out of {total} songs. ... {spotify_description}'
            yt.edit_playlist(
                yt_playlist['id'], 
                privacyStatus='PUBLIC', 
                description=description
            )
            print('done')
            # clear the html page
            yield "done"
            yield "<script>document.body.innerHTML = 'REDIRECTING';</script>"
            yield f"<script>window.location = '{link}';</script>"
            all_playlist['yt'][playlist_id] = yt_playlist['id']
            with open("playlist.json", "w") as f:
                f.write(json.dumps(all_playlist, indent=4))
        except Exception as e:
            raise e
            print('closed')
            yt.delete_playlist(yt_playlist)

    return Response(stream_with_context(gen()))


@app.route("/ytts")
def ytts():
    def gen():
        url = request.args.get('yt-url', None)
        if not url:
            return render_template('home.html')
        playlist_id = url.split("?list=")[-1]
        playlist = yt.get_playlist(playlist_id)
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
        if playlist_id in playlist['spotify']:
            playlist = spotify.playlist(playlist['spotify'][playlist_id])
            # clear the playlist 
            spotify.user_playlist_remove_all_occurrences_of_tracks(
                user_id, 
                playlist['id'], 
                [track['uri'] for track in playlist['tracks']['items']])
        else:
            playlist = spotify.user_playlist_create(
                user=user_id,
                name=playlist['title'], 
                description=description,
                public=True)
        total = len(tracks)
        try:   
            count = 0
         
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
            all_playlist['spotify'][playlist_id] = playlist['id']
            with open("playlist.json", "w") as f:
                f.write(json.dumps(all_playlist, indent=4))
        except Exception as e:
            print('closed')
            spotify.user_playlist_unfollow(config.user_id, playlist['id'])

    return Response(stream_with_context(gen()))
        
if __name__ == '__main__':
    app.run(port=666, host="0.0.0.0")
