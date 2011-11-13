#!/usr/bin/env python
import cmd
import getpass
import gsclient
import readline
import subprocess
import sys
import urllib

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

    def do_EOF(self, rest):
        print
        sys.exit(0)

    def _select_album(self, album):
        print "I don't know what to do with albums."

    def _show_albums(self, albums):
        i = self._results_idx + 1
        artist_max = max([len(a.artist.name) for a in albums])
        format = " [%%3d] %%%ds - %%s" % artist_max
        for a in albums:
            print format % (i, a.artist.name, a.title)
            i += 1

    def do_album(self, rest):
        """Search for albums with the given title."""
        self._more = self._show_albums
        self._results = self._client.search_album(rest)
        self._results_idx = 0
        self._select = self._select_album
        self.do_more(None)

    def _select_artist(self, artist):
        print "I don't know what to do with artists."

    def _show_artists(self, artists):
        i = self._results_idx + 1
        for a in artists:
            print " [%3d] %s" % (i, a.name)
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
            sys.stdout.write("Username: ")
            user = sys.stdin.readline().strip().rstrip()
            password = getpass.getpass()
            self._client.login(user, password)
        else:
            print "You are already logged in."

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
                print "No more search results."
        else:
            print "No search results."

    def do_select(self, rest):
        """Select the given index from the last search results."""
        index = int(rest.strip().rstrip())
        if self._select:
            if index >= 1 and index <= len(self._results):
                self._select(self._results[index - 1])
            else:
                print "Invalid index."
        else:
            print "No search results."

    def _select_song(self, song):
        (url, postdata) = self._client.get_stream(song)
        opener = urllib.URLopener()
        stream = opener.open(url, data = postdata)
        subprocess.call(['mplayer', '-cache', '2048', '-'], stdin = stream)

    def _show_songs(self, songs):
        i = self._results_idx + 1
        artist_max = max([len(s.artist.name) for s in songs])
        album_max = max([len(s.album.title) for s in songs])
        format = " [%%3d] %%%ds - %%%ds - %%s" % (artist_max, album_max)
        for s in songs:
            print format % (i, s.artist.name, s.album.title, s.title)
            i += 1

    def do_song(self, rest):
        """Search for songs with the given title."""
        self._more = self._show_songs
        self._results = self._client.search_song(rest)
        self._results_idx = 0
        self._select = self._select_song
        self.do_more(None)

if __name__ == '__main__':
    MainCmd().cmdloop()
