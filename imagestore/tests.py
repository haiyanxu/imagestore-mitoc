#!/usr/bin/env python
# vim:fileencoding=utf-8
from __future__ import unicode_literals
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
import swapper
import os
import random
from django.contrib.auth.models import Permission, User
from imagestore.templatetags.imagestore_tags import imagestore_alt
try:
    from lxml import html
except:
    raise ImportError('Imagestore require lxml for self-testing')

Image = swapper.load_model('imagestore', 'Image')
Album = swapper.load_model('imagestore', 'Album')


class ImagestoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('zeus', 'zeus@example.com', 'zeus')
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='imagestore'))
        self.client = Client()
        self.album = Album(name='test album', user=self.user)
        self.album.save()

    def _upload_test_image(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)
        self.image_file = open(os.path.join(os.path.dirname(__file__), 'test_img.jpg'), 'rb')
        album_id = Album.objects.filter(user=self.user)[0].id
        response = self.client.get(reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}),
            data={
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': 0,
                'form-0-image': self.image_file,
                'form-0-title': "title",
                'form-0-summary': "this is the summary",
                'form-0-order': 0,
            },
            follow=True,
        )
        self.image_file.close()
        return response

    def _create_test_album(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)
        response = self.client.get(reverse('imagestore:create-album'))
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['name'] = 'test album creation'
        response = self.client.post(reverse('imagestore:create-album'), values, follow=True)
        return response

    def test_empty_index(self):
        response = self.client.get(reverse('imagestore:index'))
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        response = self.client.get(reverse('imagestore:user', kwargs={'user_id': self.user.id}))
        self.assertEqual(response.status_code, 200)

    def test_album_creation(self):
        response = self._create_test_album()
        self.assertEqual(response.status_code, 200)

    def test_add_subalbum_to_album(self):
        self._create_test_album()
        parent_album = Album.objects.get(pk=1)
        response = self.client.get('/album/1/')
        self.assertContains(response, 'Upload Sub-Album to Album')
        response = self.client.get('/album/add/1/')
        self.assertContains(response, 'Create album')
        self.assertContains(response, '<option value="1" selected> test album</option>')
        number_of_sub_albums = len(Album.objects.filter(parent=1))
        #create subalbum
        response = self.client.post(reverse('imagestore:add-subalbum-to-album', kwargs={'album_id': 1}), {'name':'2OPb13', 'parent': '1'}, follow=True,)
        #test whether number of albums has increased by 1
        new_number_of_sub_albums = len(Album.objects.filter(parent=1))
        self.assertEqual(new_number_of_sub_albums, number_of_sub_albums+1)
        #test whether new sub-album name is correct
        response = self.client.get('/album/1/')
        self.assertEqual(Album.objects.get(parent=1).name, '2OPb13')

    def test_album_edit(self):
        response = self._create_test_album()
        album_id = Album.objects.get(name='test album creation').id
        self.client.login(username='zeus', password='zeus')
        response = self.client.get(reverse('imagestore:update-album', kwargs={'pk': album_id}))
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['name'] = 'test album update'
        self.client.post(reverse('imagestore:update-album', kwargs={'pk': album_id}), values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Album.objects.get(id=album_id).name == 'test album update')

    def test_album_delete(self):
        response = self._create_test_album()
        self.client.login(username='zeus', password='zeus')
        album_id = Album.objects.get(name='test album creation').id
        response = self.client.post(reverse('imagestore:delete-album', kwargs={'pk': album_id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(Album.objects.filter(id=album_id)) == 0)

    def test_image_upload(self):
        response = self._create_test_album()
        response = self._upload_test_image()
        self.assertEqual(response.status_code, 200)
        img = Image.objects.get(user__username='zeus')
        img_url = img.get_absolute_url()
        response = self.client.get(img_url)
        self.assertEqual(response.status_code, 200)
        self.test_user()
        self.assertIsNotNone(img.title)

    def test_invalid_image_upload(self):
        response = self._create_test_album()
        self.client.login(username='zeus', password='zeus')
        self.image_file = open(os.path.join(os.path.dirname(__file__), 'nonimg.jpg'), 'rb')
        album_id = Album.objects.filter(user=self.user)[0].id
        response = self.client.get(reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}),
            data={
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': 0,
                'form-0-image': self.image_file,
                'form-0-title': "title nonimg",
                'form-0-summary': "summary nonimg",
                'form-0-order': 0,
            },
            follow=True,
        )
        self.image_file.close()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There is 1 error in your submitted form.')
        self.assertContains(response, 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.')

    def test_tagging(self):
        response = self._create_test_album()
        self.client.login(username='zeus', password='zeus')
        album_id = Album.objects.filter(user=self.user)[0].id
        response = self.client.get(reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.image_file = open(os.path.join(os.path.dirname(__file__), 'test_img.jpg'), 'rb')
        response = self.client.post(
            reverse('imagestore:upload-image-to-album', kwargs={'album_id': album_id}),
            data={
                'form-TOTAL_FORMS': 1,
                'form-INITIAL_FORMS': 0,
                'form-0-image': self.image_file,
                'form-0-title': "title",
                'form-0-summary': "this is the summary",
                'form-0-tags': "one, two, three",
                'form-0-order': 0,
            },
            follow=True,
        )
        self.image_file.close()
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('imagestore:tag', kwargs={'tag': 'one'}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['image_list']) == 1)

    def test_delete(self):
        User.objects.create_user('bad', 'bad@example.com', 'bad')
        response = self._create_test_album()
        self._upload_test_image()
        self.client.login(username='bad', password='bad')
        image_id = Image.objects.get(user__username='zeus').id
        response = self.client.post(reverse('imagestore:delete-image', kwargs={'pk': image_id}), follow=True)
        self.assertEqual(response.status_code, 404)
        self.client.login(username='zeus', password='zeus')
        response = self.client.post(reverse('imagestore:delete-image', kwargs={'pk': image_id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Image.objects.all()), 0)

    def test_update_image(self):
        self._upload_test_image()
        self.client.login(username='zeus', password='zeus')
        image_id = Image.objects.get(user__username='zeus').id
        response = self.client.get(reverse('imagestore:update-image', kwargs={'pk': image_id}), follow=True)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['tags'] = 'one, tow, three'
        values['title'] = 'changed title'
        values['album'] = Album.objects.filter(user=self.user)[0].id
        self.client.post(reverse('imagestore:update-image', kwargs={'pk': image_id}), values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Image.objects.get(user__username='zeus').title == 'changed title')

    def test_prev_next_with_ordering(self):
        self.test_album_creation()
        for i in range(1, 6):
            self._upload_test_image()
            img = Image.objects.order_by('-id')[0]
            img.order = i
            img.save()
        # Swap two id's
        im1 = Image.objects.get(order=2)
        im2 = Image.objects.get(order=4)
        im1.order, im2.order = 4, 2
        im1.save()
        im2.save()
        response = self.client.get(Image.objects.get(order=3).get_absolute_url())
        self.assertEqual(response.context['next'], im1)
        self.assertEqual(response.context['previous'], im2)

    def test_album_order_created(self):
        self.album.delete()
        a1 = Album.objects.create(name='b2', user=self.user)
        a2 = Album.objects.create(name='a1', user=self.user)
        response = self.client.get(reverse('imagestore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'][0].name, 'b2')
        self.assertEqual(response.context['object_list'][1].name, 'a1')
        a2.created = '2018-12-31 19:00:00+00'
        a2.save()
        response = self.client.get(reverse('imagestore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'][0].name, 'a1')
        self.assertEqual(response.context['object_list'][1].name, 'b2')

    def test_imagestore_alt(self):
        self._upload_test_image()
        image = Image.objects.all()[0]
        image.album = None
        image.title = ''
        image.save()

        # empty title, empty brief = empty result
        result = imagestore_alt(image)
        self.assertEqual(result, 'alt=""')

        album = Album.objects.all()[0]
        album.brief = 'album brief'
        album.save()
        image.album = album
        image.save()
        counter = random.randint(0, 111)

        # empty title, not empty brief = brief in result
        result = imagestore_alt(image)
        self.assertIn(album.brief, result)
        self.assertNotIn(str(counter), result)  # insure next assertIn from mistake
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))

        # same behaviour plus counter
        result = imagestore_alt(image, counter)
        self.assertIn(album.brief, result)
        self.assertIn(str(counter), result)
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))

        # IMAGESTORE_BRIEF_TO_ALT_TEMPLATE affects on result format
        with self.settings(IMAGESTORE_BRIEF_TO_ALT_TEMPLATE='{1}_{0}'):
            result = imagestore_alt(image, counter)
            self.assertIn('{1}_{0}'.format(album.brief, counter), result)

        # but does not affect on single and double quotes
        with self.settings(IMAGESTORE_BRIEF_TO_ALT_TEMPLATE='{1}_\'_\"_{0}'):
            result = imagestore_alt(image, counter)
            self.assertIn(result.count('\''), (0, 2))
            self.assertIn(result.count('\"'), (0, 2))

        # quotes shall not pass
        album.brief = 'album \' \" brief'
        album.save()
        result = imagestore_alt(image, counter)
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))
        counter = '1 \'\" 2'
        result = imagestore_alt(image, counter)
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))

        # not empty title = title in result (only)
        image.title = 'image title'
        image.save()
        result = imagestore_alt(image, counter)
        self.assertIn(image.title, result)
        self.assertNotIn(album.brief, result)
        self.assertNotIn(str(counter), result)
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))

        # quotes escaped again
        image.title = 'image \' \" title'
        image.save()
        result = imagestore_alt(image, counter)
        self.assertIn(result.count('\''), (0, 2))
        self.assertIn(result.count('\"'), (0, 2))
