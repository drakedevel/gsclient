#!/usr/bin/env python
import cmd
import getpass
import gsclient
import subprocess
import sys
import platform

# Python 3 compatibility
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

version = 0.0

def tr(s, l):
    if len(s) < l:
        return s
    return s[0:l-3] + '...'

class MainCmd(cmd.Cmd):
    intro = 'GS Command Line %s, type "help" or "?" for help' % version
    prompt = 'gscmd> '

    def __init__(self):
        cmd.Cmd.__init__(self)
        self._client = gsclient.ClientWrapper()
        self._more = None
        self._results = None
        self._results_idx = None
        self._select = None
        self._os = 'linux'
        if (platform.system() == "Darwin"):
            self._os = 'mac'

    def do_EOF(self, rest):
        print()
        sys.exit(0)

    def _select_album(self, album):
        self._more = self._show_songs
        verified = input("Show only verified songs in this album?: ") in ('y','yes')
        self._results = self._client.get_album_songs(album, verified)
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

    def _show_albums(self, albums):
        i = self._results_idx + 1
        artist_max = max([len(a.artist.name) for a in albums])
        format = " [%%3d] %%%ds - %%s" % artist_max
        for a in albums:
            print(format % (i, a.artist.name, a.title))
            i += 1

    def do_album(self, rest):
        """Search for albums with the given title."""
        self._more = self._show_albums
        self._results = self._client.search_album(rest)
        self._results_idx = 0
        self._select = self._select_album
        self.do_more(None)

    def _select_artist(self, artist):
        self._more = self._show_songs
        verified = input("Show only verified songs in this artist?: ") in ('y','yes')
        self._results = self._client.get_artist_songs(artist, verified)
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

    def _show_artists(self, artists):
        i = self._results_idx + 1
        for a in artists:
            print(" [%3d] %s" % (i, a.name))
            i += 1

    def do_artist(self, rest):
        """Search for artists with the given name."""
        self._more = self._show_artists
        self._results = self._client.search_artist(rest)
        self._results_idx = 0
        self._select = self._select_artist
        self.do_more(None)

    def do_login(self, rest):
        """Log in (prompts for username and password)."""
        if self._client.user_id is None:
            user = input("Username: ")
            password = getpass.getpass()
            self._client.login(user, password)
        else:
            print("You are already logged in.")

    def do_logout(self, rest):
        """Log out and clear current session."""
        self._client.new_session()

    def do_quit(self, rest):
        sys.exit(0)

    def do_more(self, rest):
        """Show more search results."""
        if self._more:
            if self._results_idx < len(self._results):
                self._more(self._results[self._results_idx:self._results_idx + 30])
                self._results_idx += 30
            else:
                print("No more search results.")
        else:
            print("No search results.")

    def _select_playlist(self, pl):
        self._more = self._show_songs
        self._results = self._client.get_playlist_songs(pl)
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

    def _show_playlists(self, pls):
        i = self._results_idx + 1
        for pl in pls:
            print(" [%3d] %s" % (i, pl.name))
            i += 1

    def do_playlists(self, rest):
        """Show user playlists."""
        self._more = self._show_playlists
        self._results = self._client.get_playlists()
        self._results_idx = 0
        self._select = self._select_playlist
        self.do_more(None)

    def do_select(self, rest):
        """Select the given index from the last search results."""
        try:
            index = int(rest.strip().rstrip())
        except ValueError:
            print("Use select <index>")
            return
        if self._select:
            if index >= 1 and index <= len(self._results):
                self._select(self._results[index - 1])
            else:
                print("Invalid index.")
        else:
            print("No search results.")

    def _select_song(self, song):
        (url, postdata) = self._client.get_stream(song)
        stream = urlopen(url, data = postdata.encode('utf-8'))
        command = ['mplayer', '-cache', '2048', '-']
        if (self._os == 'mac'):
            command = ['mpg123', '-']
        subprocess.call(command, stdin = stream)

    def _show_songs(self, songs):
        i = self._results_idx + 1
        artist_max = max([len(s.artist.name) for s in songs])
        album_max = max([len(s.album.title) for s in songs])
        format = " [%%3d] %%%ds - %%%ds - %%s" % (artist_max, album_max)
        for s in songs:
            print(format % (i, s.artist.name, s.album.title, s.title))
            i += 1

    def do_favorites(self, rest):
        """Show user favorites"""
        self._more = self._show_songs
        self._results = self._client.get_favorite_songs()
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

    def do_song(self, rest):
        """Search for songs with the given title."""
        self._more = self._show_songs
        self._results = self._client.search_song(rest)
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

if __name__ == '__main__':
    MainCmd().cmdloop()
