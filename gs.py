import hashlib
import json
import random

# Python 3 compatibility
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

class Request(dict):
    def __init__(self, method):
        self.method = method

class ServiceException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def __repr__(self):
        return 'ServiceException("%s", %d)' % (self.message, self.code)

    def __str__(self):
        return 'Server returned:%s (code %d)' % (self.message, self.code)

class Service(object):
    endpoint_host = "grooveshark.com"
    endpoint_path = "/more.php"

    def __init__(self):
        self.session = None
        self.token = None

    def send(self, req, header):
        blob = {}
        blob['method'] = req.method
        blob['parameters'] = req
        blob['header'] = header
        request = urllib2.Request('https://%s%s' % (self.endpoint_host, self.endpoint_path),
                                  data = json.dumps(blob).encode('utf-8'),
                                  headers = { 'Content-Type': 'application/json' })
        response = urllib2.urlopen(request).read()
        response = response.decode('utf-8')
        try:
            data = json.loads(response)
        except:
            print('Received garbage: "%s"' % response)
            raise

        if 'result' in data:
            return data['result']
        if 'fault' in data:
            raise ServiceException(data['fault']['message'],
                                   data['fault']['code'])
        raise Exception("We sent a bad request")

class Client(object):
    def __init__(self, service):
        self._last_salt = 0
        self._random = random.Random()
        self._service = service

    def _send(self, req):
        header = {}
        header['client'] = self.client_name
        header['clientRevision'] = self.client_rev
        header['country'] = {}
        if self._service.session:
            header['session'] = self._service.session
        if self._service.token:
            header['token'] = self._next_call_token(req.method)

        return self._service.send(req, header)

    def _next_call_token(self, method):
        old = self._last_salt
        while old == self._last_salt:
            self._last_salt = self._random.randint(0, 0xffffff)
        sha1 = hashlib.sha1()
        sha1.update("{}:{}:{}:{:0^6x}".format(method,
                                              self._service.token,
                                              self.client_rev_key,
                                              self._last_salt).encode('utf-8'))
        #print("{}:{}:{}:{:0^6x}".format(method,
        #                               self._service.token,
        #                               self.client_rev_key,
        #                               self._last_salt))
        return "%06x%s" % (self._last_salt, sha1.hexdigest())

class WebClient(Client):
    client_name = 'htmlshark'
    client_rev = '20130520'
    client_rev_key = 'nuggetsOfBaller'

    def __init__(self, service):
        super(WebClient, self).__init__(service)
        self.user_id = None

    def start_session(self):
        req = Request('initiateSession')
        self._service.session = self._send(req)

    def get_comm_token(self):
        req = Request('getCommunicationToken')

        md5 = hashlib.md5()
        md5.update(self._service.session.encode('utf-8'))
        req['secretKey'] = md5.hexdigest()

        self._service.token = self._send(req)

    def authenticate_user(self, user, password):
        req = Request('authenticateUser')
        req['username'] = user
        req['password'] = password

        response = self._send(req)
        if response['userID']:
            self.user_id = response['userID']
        else:
            raise Exception("Invalid username or password")

    def get_favorites(self, what, user_id = None):
        if not user_id:
            if self.user_id:
                user_id = self.user_id
            else:
                raise Exception('Must have user_id')
        req = Request('getFavorites')
        req['userID'] = user_id
        req['ofWhat'] = what
        return self._send(req)

    def get_album_songs(self, album_id = None, verified=False):
        if not album_id:
            raise Exception('Must have album_id')
        req = Request('albumGetSongs')
        req['albumID'] = album_id
        req['isVerified'] = verified
        req['offset'] = 0
        return self._send(req)

    def get_artist_songs(self, artist_id = None, verified=False):
        if not artist_id:
            raise Exception('Must have artist_id')
        req = Request('artistGetSongs')
        req['artistID'] = artist_id
        req['isVerified'] = verified
        req['offset'] = 0
        return self._send(req)

    def get_playlists(self, user_id = None):
        if not user_id:
            if self.user_id:
                user_id = self.user_id
            else:
                raise Exception('Must have user_id')
        req = Request('userGetPlaylists')
        req['userID'] = user_id
        return self._send(req)

    def get_playlist_songs(self, playlist_id = None):
        if not playlist_id:
            raise Exception('Must have playlist_id')
        req = Request('playlistGetSongs')
        req['playlistID'] = playlist_id
        return self._send(req)

    def search(self, query, what):
        req = Request('getResultsFromSearch')
        req['query'] = query
        req['type'] = what
        return self._send(req)
        
class PlayerClient(Client):
    client_name = 'jsqueue'
    client_rev = '20130520'
    client_rev_key = 'chickenFingers'

    def __init__(self, service):
        super(PlayerClient, self).__init__(service)

    def get_stream(self, song):
        req = Request('getStreamKeyFromSongIDEx')
        req['songID'] = song
        req['prefetch'] = False
        req['country'] = {}
        return self._send(req)
