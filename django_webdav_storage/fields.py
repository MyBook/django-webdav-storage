from django.core.files.base import ContentFile, File
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FileField, ImageField, FieldFile, ImageFieldFile
from StringIO import StringIO

from django_webdav_storage.storage import WebDAVStorage, default_webdav_storage

import re
import os

VALID_CONTENT_TYPES = (
    'application/epub+zip',
    'application/x-fictionbook+xml',
    'application/x-fb2',
    'application/x-fb2+zip',
)

try:
    import magic
    import mimetypes
    import uuid

    # Some extensions to make my code working
    mimetypes.add_type('application/epub+zip', '.epub')
    mimetypes.add_type('application/x-fictionbook+xml', '.fb2')
    mimetypes.add_type('application/x-fb2', '.fb2')
    mimetypes.add_type('application/x-fb2+zip', '.fb2.zip')
except ImportError:
    magic = None
    mimetypes = None
    uuid = None


# noinspection PyArgumentList,PyUnresolvedReferences
class WebDAVMixin(object):
    random_filename = False

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=default_webdav_storage,
                 custom_magic_file=None, **kwargs):
        if kwargs.get('random_filename', False):
            if magic is None or uuid is None or mimetypes is None:
                raise ImproperlyConfigured(
                    'You need to install magic, mimetypes and uuid module to use random_filename')
            self.custom_magic_file = custom_magic_file
            self.valid_content_types = VALID_CONTENT_TYPES
            if kwargs.get('valid_content_types'):
                self.valid_content_types = kwargs['valid_content_types']
            self.random_filename = True
            del kwargs['random_filename']
        super(WebDAVMixin, self).__init__(verbose_name=verbose_name, name=name, upload_to=upload_to,
                                          storage=storage, **kwargs)

    def generate_filename(self, instance, filename):
        if not self.random_filename:
            return super(WebDAVMixin, self).generate_filename(instance, filename)
        uuid_string = unicode(uuid.uuid4())
        file = getattr(instance, self.attname)
        if hasattr(file._file, 'content_type') and file._file.content_type in self.valid_content_types:
            content_type = file._file.content_type
        else:
            try:
                file._file.seek(0)
                if self.custom_magic_file:
                    content_type = magic.Magic(mime=True,
                                               magic_file=self.custom_magic_file).from_buffer(file._file.read(1024))
                else:
                    content_type = magic.from_buffer(file._file.read(1024), mime=True)
            except TypeError as e:
                print e
                content_type = 'application/x-unknown'

        #Receiving all extensions and checking if file extension matches MIME Type
        extensions = mimetypes.guess_all_extensions(content_type)
        try:
            file_ext = re.findall(r'\.[^.]+$', filename)[0]
        except IndexError:
            file_ext = None
        if file_ext in extensions:
            ext = file_ext
        elif extensions:
            ext = extensions[0]
        else:
            ext = '.bin'

        return os.path.join(self.upload_to, uuid_string[:2], uuid_string[2:4], '%s%s' % (uuid_string, ext))


# noinspection PyUnresolvedReferences
class WebDAVFile(File):
    def __init__(self, name, storage, mode):
        self._name = name
        self._storage = storage
        self._mode = mode
        self._is_dirty = False
        self.file = StringIO()
        self._is_read = False

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        if not hasattr(self, '_size'):
            self._size = self._storage.size(self._name)
        return self._size

    def read(self, num_bytes=None):
        if not self._is_read:
            self.file = self._storage._read(self._name)
            self._is_read = True

        return self.file.read(num_bytes)

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")
        self.file = StringIO(content)
        self._is_dirty = True
        self._is_read = True

    def close(self):
        self.file.close()


class WebDAVFieldFileMixin(object):
    def save(self, name, content, save=True):
        file = getattr(self.instance, self.field.attname)
        if not hasattr(file, '_file') or not file._file:
            file._file = ContentFile(content) if not hasattr(content, 'read') else content
        return super(WebDAVFieldFileMixin, self).save(name, content, save)


class WebDAVFieldFile(WebDAVFieldFileMixin, FieldFile):
    pass


class WebDAVImageFieldFile(WebDAVFieldFileMixin, ImageFieldFile):
    pass


class WebDAVFileField(WebDAVMixin, FileField):
    attr_class = WebDAVFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=default_webdav_storage, **kwargs):
        super(WebDAVFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(WebDAVFileField, self).deconstruct()
        kwargs.pop('storage', None)
        return name, path, args, kwargs


class WebDAVImageField(WebDAVMixin, ImageField):
    attr_class = WebDAVImageFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=default_webdav_storage, **kwargs):
        super(WebDAVImageField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(WebDAVImageField, self).deconstruct()
        kwargs.pop('storage', None)
        return name, path, args, kwargs


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^django_webdav_storage\.fields\.WebDAVFileField"])
    add_introspection_rules([], ["^django_webdav_storage\.fields\.WebDAVImageField"])
except ImportError:
    pass
