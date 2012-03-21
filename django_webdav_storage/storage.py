from httplib import HTTPConnection
from tempfile import TemporaryFile
from urllib2 import HTTPError
from urlparse import urlparse
from django.conf import settings
from django.core.files.storage import Storage

class WebDAVStorage(Storage):
    """
    WebDAV Storage class for Django pluggable storage system.

    >>> s = WebDAVStorage()
    """

    def __init__(self, location=settings.WEBDAV_STORAGE_LOCATION, base_url=settings.MEDIA_URL):
        self._location = location
        self._host = urlparse(location)[1]
        self._base_url = base_url

    def _get_connection(self):
        conn = HTTPConnection(self._host)
        conn.set_debuglevel(0)
        return conn

    def exists(self, name):
        conn = self._get_connection()
        conn.request('HEAD', self._location + name)
        is_exists = conn.getresponse().status == 200
        conn.close()
        return is_exists

    def _save(self, name, content):
        conn = self._get_connection()
        conn.putrequest('PUT', self._location + name)
        conn.putheader('Content-Length', len(content))
        conn.endheaders()
        content.seek(0)
        conn.send(content.read())
        res = conn.getresponse()
        conn.close()
        if res.status != 201:
            raise HTTPError(self._location + name, res.status, res.reason, res.msg, res.fp)
        return name

    def _open(self, name, mode):
        assert (mode == 'rb'), 'DAV storage accepts only rb mode'
        conn = self._get_connection()
        conn.request('GET', self._location + name)
        res = conn.getresponse()
        if res.status != 200:
            raise ValueError(res.reason)
        temp_file = TemporaryFile()
        while True:
            chunk = res.read(32768)
            if chunk:
                temp_file.write(chunk)
            else:
                break
        temp_file.seek(0)
        conn.close()
        return temp_file

    def delete(self, name):
        conn = self._get_connection()
        conn.request('DELETE', self._location + name)
        res = conn.getresponse()
        if res.status != 204:
            raise HTTPError(self._location + name, res.status, res.reason, res.msg, res.fp)
        conn.close()
        return res

    def url(self, name):
        return self._location + name

    def size(self, name):
        conn = self._get_connection()
        conn.request('HEAD', self._location + name)
        res = conn.getresponse()
        conn.close()
        if res.status != 200:
            raise HTTPError(self._location + name, res.status, res.reason, res.msg, res.fp)
        return res.getheader('Content-Length')