from django.contrib.auth.models import Permission, User
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
import allauth
import django.contrib.auth
import imagestore
import swapper
import os
try:
    from lxml import html
except:
    raise ImportError('requires lxml for testing')


Image = swapper.load_model('imagestore', 'Image')
Album = swapper.load_model('imagestore', 'Album')

from . import views

class PageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser1', 'testuser1@example.com', 'MitocGallery')
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='imagestore'))
        self.album = Album(name='testuser1Album1', user=self.user)
        self.album.save()
        self.album_id = Album.objects.filter(user=self.user)[0].id

    def _upload_test_image(self, username='testuser1', password='MitocGallery'):
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
                'form-0-title': "testuser1image1",
                'form-0-summary': "summary of image 1",
                'form-0-tags': "dogs",
                'form-0-order': 0,
            },
            follow=True,
        )
        return response

    def _navbar_options_guest(self, response):
        self.assertContains(response, 'Sign In')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'Sign Out')
        self.assertNotContains(response, 'New Album')

    def _navbar_options_user(self, response):
        self.assertContains(response, 'New Album')
        self.assertContains(response, 'Sign Out')
        self.assertNotContains(response, 'Sign Up')
        self.assertNotContains(response, 'Sign In')

    def _guest_login_required(self, response):
        self.assertEqual(response.resolver_match.func.__name__, django.contrib.auth.views.LoginView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'account/login.html')

    def test_homepage(self):
        #test base URL
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_list.html')
        self.assertContains(response, 'All albums')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_list.html')
        self.assertContains(response, 'All albums')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_list.html')
        self.assertContains(response, 'All albums')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_user(response)

    def test_icons_page(self):
        #test base URL
        response = self.client.get('/icons/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, 'icons')
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'mitocgallery/icons.html')
        self.assertContains(response, 'Camera')
        self.assertContains(response, 'Cross')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('icon-page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, 'icons')
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'mitocgallery/icons.html')
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('icon-page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, 'icons')
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'mitocgallery/icons.html')
        self._navbar_options_user(response)

    def test_create_album(self):
        #test base URL
        response = self.client.get('/album/add/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:create-album'), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        number_of_albums = len(Album.objects.all())
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:create-album'), follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.CreateAlbum.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/forms/album_form.html')
        self.assertContains(response, 'Create album')
        self._navbar_options_user(response)
        #invalid form content
        response = self.client.post(reverse('imagestore:create-album'), {'name':'', 'brief':'brief of invalid album', 'tripreport':'invalid trip report'})
        self.assertContains(response, '<p id="error_1_id_name" class="invalid-feedback"><strong>This field is required.</strong></p>')
        new_number_of_albums = len(Album.objects.all())
        self.assertEqual(number_of_albums, new_number_of_albums)
        #valid form content, only name and order required
        response = self.client.post(reverse('imagestore:create-album'), {'name':'Valid Album'})
        test_album_id = Album.objects.get(name='Valid Album').id
        new_number_of_albums = len(Album.objects.all())
        self.assertEqual(new_number_of_albums, number_of_albums+1)

    def test_album(self):
        #test base URL
        response = self.client.get('/album/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:album', kwargs={'album_id': self.album_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_guest(response)
        self.assertNotContains(response, 'Upload Image to Album')
        self.assertNotContains(response, 'Edit Album')
        self.assertNotContains(response, 'Delete Album')
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:album', kwargs={'album_id': self.album_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_user(response)
        self.assertContains(response, 'Upload Image to Album')
        self.assertContains(response, 'Edit Album')
        self.assertContains(response, 'Delete Album')

    def test_update_album(self):
        #test base URL
        response = self.client.get('/album/1/edit/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:update-album', kwargs={'pk': self.album_id}), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:update-album', kwargs={'pk': self.album_id}), follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit album')
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.UpdateAlbum.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/forms/album_form.html')
        initial_name = response.context['form'].initial['name']
        response = self.client.post(reverse('imagestore:update-album', kwargs={'pk': self.album_id}), {'name': initial_name, 'tripreport':'updated trip report'}, follow=True)
        self.assertEqual(Album.objects.get(id=1).tripreport, 'updated trip report')
        self._navbar_options_user(response)

    def test_delete_album(self):
        #test base URL
        response = self.client.get('/album/1/delete/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:delete-album', kwargs={'pk': self.album_id}), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:delete-album', kwargs={'pk': self.album_id}), follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.DeleteAlbum.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_delete.html')
        self._navbar_options_user(response)

    def test_tag(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertIsNotNone(img.title)
        self.client.logout()
        #test base URL
        response = self.client.get('/tag/dogs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'dogs')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:tag', kwargs={'tag': "dogs"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'dogs')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:tag', kwargs={'tag': "dogs"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'dogs')
        self._navbar_options_user(response)

    def test_user(self):
        #test base URL
        response = self.client.get('/user/testuser1/albums/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_list.html')
        self.assertContains(response, 'Albums for user testuser1')
        self.assertContains(response, 'testuser1Album1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:user', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/album_list.html')
        self.assertContains(response, 'Albums for user testuser1')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:user', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.AlbumListView.as_view().__name__)
        self._navbar_options_user(response)

    def test_user_images(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertTrue(img.title == 'testuser1image1')
        self.client.logout()
        #test base URL
        response = self.client.get('/user/testuser1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'User: testuser1')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:user-images', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_list.html')
        self.assertContains(response, 'User: testuser1')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:user-images', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(img.title)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageListView.as_view().__name__)
        self._navbar_options_user(response)

    def test_upload_image_to_album(self):
        #test base URL
        response = self.client.get('/upload/album/1/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:upload-image-to-album', kwargs={'album_id': self.album_id}), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        img_url = img.get_absolute_url()
        response = self.client.get(img_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(img.title)
        response = self.client.get(reverse('imagestore:upload-image-to-album', kwargs={'album_id': self.album_id}), follow = True)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.CreateImage.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/forms/image_form_album.html')
        self._navbar_options_user(response)

    def test_image(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertTrue(img.title == 'testuser1image1')
        self.client.logout()
        #test base URL
        response = self.client.get('/image/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image.html')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:image', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image.html')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:image', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_user(response)

    def test_image_album(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertTrue(img.title == 'testuser1image1')
        self.client.logout()
        #test base URL
        response = self.client.get('/album/1/image/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image.html')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:image-album', kwargs={'pk': 1, 'album_id':self.album_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image.html')
        self.assertContains(response, 'testuser1image1')
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:image-album', kwargs={'pk': 1, 'album_id':self.album_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.ImageView.as_view().__name__)
        self._navbar_options_user(response)

    # redirect to login page when guest tries to delete an image
    def test_delete_image(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertTrue(img.title == 'testuser1image1')
        self.client.logout()
        #test base URL
        response = self.client.get('/image/1/delete/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:delete-image', kwargs={'pk': 1}), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:delete-image', kwargs={'pk': 1}), follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.DeleteImage.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/image_delete.html')
        self._navbar_options_user(response)

    # redirect to login page when guest tries to update an image
    def test_update_image(self):
        response = self.client.login(username='testuser1', password='MitocGallery')
        response = self._upload_test_image()
        img = Image.objects.get(user__username='testuser1')
        self.assertTrue(img.title == 'testuser1image1')
        self.client.logout()
        #test base URL
        response = self.client.get('/image/1/update/', follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test reverse URL
        response = self.client.get(reverse('imagestore:update-image', kwargs={'pk': 1}), follow = True)
        self.assertEqual(response.status_code, 200)
        self._guest_login_required(response)
        self._navbar_options_guest(response)
        #test user logged in
        self.client.login(username='testuser1', password='MitocGallery')
        response = self.client.get(reverse('imagestore:update-image', kwargs={'pk': 1}), follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, imagestore.views.UpdateImage.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'imagestore/forms/image_form.html')

#base template tests?

class UserTests(TestCase):

    def test_user_signup_form(self):
        #test base URL
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, allauth.account.views.SignupView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertContains(response, '<h1>Sign Up</h1>')
        self.assertContains(response, 'Sign In')
        self.assertNotContains(response, 'Sign Out')
        self.assertNotContains(response, 'New Album')
        #test reverse URL
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, allauth.account.views.SignupView.as_view().__name__)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertContains(response, '<h1>Sign Up</h1>')
        self.assertContains(response, 'Sign In')
        self.assertNotContains(response, 'Sign Out')
        self.assertNotContains(response, 'New Album')
        #test form and validators
        #invalid form content
        response = self.client.post(reverse('account_signup'), {'email':'zpbt', 'email2':'zpbt', 'password1':'zpbt123', 'password2':'zpbt123'})
        self.assertContains(response, '<p id="error_1_id_email" class="invalid-feedback"><strong>Enter a valid email address.</strong></p>')
        self.assertContains(response, '<p id="error_1_id_email2" class="invalid-feedback"><strong>Enter a valid email address.</strong></p>')
        self.assertContains(response, '<p id="error_1_id_password1" class="invalid-feedback"><strong>This password is too short. It must contain at least 8 characters.</strong></p>')
        # response = self.client.post(reverse('account_signup'), {'email':'zpbt@gmail.com', 'email2':'zpbt@gmail.com', 'password1':'zpbt1234', 'password2':'zpbt1234'})
        # self.assertContains(response, 'The password is too similar to the email address.')
        response = self.client.post(reverse('account_signup'), {'email':'zpbt@gmail1.com', 'email2':'zpbt@gmail.com', 'password1':'12345678', 'password2':'12345678'})
        self.assertContains(response, 'You must type the same email each time.')
        self.assertContains(response, 'This password is too common.')
        self.assertContains(response, 'This password is entirely numeric.')
        #invalid recaptcha
        response = self.client.post(reverse('account_signup'), {'email':'zpbt@gmail.com', 'email2':'zpbt@gmail.com', 'password1':'MitocGallery1', 'password2':'MitocGallery1', 'g-recaptcha-response': 'FAILED'}, follow=True)
        self.assertContains(response, 'Error verifying reCAPTCHA')
        #valid form content
        # response = self.client.post(reverse('account_signup'), {'email':'zpbt@gmail.com', 'email2':'zpbt@gmail.com', 'password1':'MitocGallery1', 'password2':'MitocGallery1', "g-recaptcha-response": "PASSED"}, follow=True)
        # print(response.content)
        # self.assertContains(response, 'Confirmation e-mail sent to zpbt@gmail.com.')
