django-webdav-storage
=====================

Usage
-----

In your settings:

    WEBDAV_STORAGE_LOCATION = 'http://my-web-storage.com/upload/'

In your models:

    class Attachement(models.Model):
        object = models.ForeignKey(Object)
        content = WebDAVFileField(upload_to='storage', null=True)

    class Photo(models.Model):
        user = models.ForeignKey(User)
        content = WebDAVImageField(upload_to='photos')

