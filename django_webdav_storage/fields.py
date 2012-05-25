from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FileField, ImageField, FieldFile, ImageFieldFile

from south.modelsinspector import add_introspection_rules

from django_webdav_storage.storage import WebDAVStorage

import re
import os

try:
    import magic
    import mimetypes
    import uuid

    mimetypes.add_type('application/epub+zip', '.epub') #Some extensions to make my code working
except ImportError:
    magic = None
    mimetypes = None
    uuid = None

#noinspection PyArgumentList,PyUnresolvedReferences
class WebDAVMixin(object):
    random_filename = False

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=WebDAVStorage(), **kwargs):
        if kwargs.get('random_filename', False):
            if magic is None or uuid is None or mimetypes is None:
                raise ImproperlyConfigured(
                    'You need to install magic, mimetypes and uuid module to use random_filename')
            self.magic = magic.Magic()
            self.random_filename = True
            del kwargs['random_filename']
        super(WebDAVMixin, self).__init__(verbose_name=verbose_name, name=name, upload_to=upload_to, storage=storage, **kwargs)

    def generate_filename(self, instance, filename):
        if not self.random_filename:
            return super(WebDAVMixin, self).generate_filename(instance, filename)
        uuid_string = unicode(uuid.uuid4())
        file = getattr(instance, self.attname)

        if hasattr(file._file, 'content_type'):
            content_type = file._file.content_type
        else:
            try:
                file._file.seek(0)
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

#noinspection PyUnresolvedReferences
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

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=WebDAVStorage(), **kwargs):
        super(WebDAVFileField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)


class WebDAVImageField(WebDAVMixin, ImageField):
    attr_class = WebDAVImageFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=WebDAVStorage(), **kwargs):
        super(WebDAVImageField, self).__init__(verbose_name, name, upload_to, storage, **kwargs)

add_introspection_rules([], ["^django_webdav_storage\.fields\.WebDAVFileField"])
add_introspection_rules([], ["^django_webdav_storage\.fields\.WebDAVImageField"])
