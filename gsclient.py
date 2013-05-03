import gs
import os.path
import shelve

class Album(object):
    def __init__(self, albumid, artist, title):
        self._id = albumid
        self.artist = artist
        self.title = title

class Artist(object):
    def __init__(self, artistid, name):
        self._id = artistid
        self.name = name

class Song(object):
    def __init__(self, songid, album, artist, track, title):
        self._id = songid
        self.album = album
        self.artist = artist
        self.track = track
        self.title = title

class Playlist(object):
    def __init__(self, uuid, name, description):
        self._id = uuid
        self.name = name
        self.description = description

class ClientWrapper(object):
    def __init__(self, config = '~/.pygsclient'):
        self._service = gs.Service()
        self._web = gs.WebClient(self._service)
        self._player = gs.PlayerClient(self._service)
        self._shelf = shelve.open(os.path.expanduser(config))
        if 'session' in self._shelf:
            self._service.session = self._shelf['session']
            if 'user_id' in self._shelf:
                self._web.user_id = self._shelf['user_id']
        else:
            self.new_session()

        self._web.get_comm_token()

    def _clear_user_id(self):
        self._web.user_id = None
        if 'user_id' in self._shelf:
            del self._shelf['user_id']

    def _munge_playlist(self, p):
        return Playlist(uuid = p['PlaylistID'],
                        name = p['Name'],
                        description = p.get('About',''))

    def get_favorite_songs(self, user_id=None):
        raw_result = self._web.get_favorites('Songs',user_id=user_id)
        return [self._munge_song(s) for s in raw_result]

    def get_playlists(self):
        playlist_data = self._web.get_playlists()
        return [self._munge_playlist(x) for x in playlist_data['Playlists']]

    def get_playlist_songs(self, playlist):
        raw_result = self._web.get_playlist_songs(playlist._id)
        return [self._munge_song(s) for s in raw_result['Songs']]

    def get_album_songs(self, album, verified=False):
        raw_result = self._web.get_album_songs(album._id, verified)
        return [self._munge_song(s) for s in raw_result['songs']]

    def get_artist_songs(self, artist, verified=False):
        raw_result = self._web.get_artist_songs(artist._id, verified)
        return [self._munge_song(s) for s in raw_result['songs']]

    def get_stream(self, song):
        stream_data = self._player.get_stream(song._id)
        return ("http://%s/stream.php" % stream_data['ip'],
                "streamKey=%s" % stream_data['streamKey'])

    def login(self, username, password):
        try:
            self._web.authenticate_user(username, password)
            self._shelf['user_id'] = self._web.user_id
        except:
            self._clear_user_id()
            raise

    def new_session(self):
        self._web.start_session()
        self._shelf['session'] = self._service.session
        self._clear_user_id()

    def _munge_album(self, a):
        return Album(albumid = a['AlbumID'],
                     artist = self._munge_artist(a),
                     title = a['AlbumName'])

    def search_album(self, query):
        raw_result = self._web.search(query, 'Albums')['result']
        return [self._munge_album(s) for s in raw_result]

    def _munge_artist(self, a):
        return Artist(artistid = a['ArtistID'],
                      name = a['ArtistName'])

    def search_artist(self, query):
        raw_result = self._web.search(query, 'Artists')['result']
        return [self._munge_artist(s) for s in raw_result]

    def _munge_song(self, s):
        return Song(songid = s['SongID'],
                    album = self._munge_album(s),
                    artist = self._munge_artist(s),
                    track = s['TrackNum'],
                    title = s.get('SongName',s.get('Name')))

    def search_song(self, query):
        raw_result = self._web.search(query, 'Songs')['result']
        return [self._munge_song(s) for s in raw_result]

    @property
    def user_id(self):
        return self._web.user_id
