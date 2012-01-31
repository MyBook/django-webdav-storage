"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import random
from django.core.files.base import  ContentFile

from django.test import TestCase
from django.db import models
from django_webdav_storage.fields import WebDAVFileField

class TestModel(models.Model):
    file = WebDAVFileField(upload_to='test')


class SimpleTest(TestCase):
    def test_upload(self):
        t = TestModel()
        f = ContentFile('hello world')
        f.name = str(random.random())
        t.file = f
        t.save()
        t = TestModel.objects.all()[0]
        self.assertEqual(t.file.read(), 'hello world')
        self.assertEqual(t.file.size, '11', 'Size is not changed')
        self.assertEqual(t.file.url, 'http://knigla.com/storage/test/'+f.name)
        t.file.delete()
        self.assertFalse(t.file)
        t.delete()
