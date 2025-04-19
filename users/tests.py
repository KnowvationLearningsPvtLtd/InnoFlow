from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

User = get_user_model()

def create_test_image():
    image = Image.new('RGB', (100, 100), color='blue')
    image_file = io.BytesIO()
    image.save(image_file, 'JPEG')
    image_file.seek(0)
    return SimpleUploadedFile('test.jpg', image_file.read(), content_type='image/jpeg')

class UserRegistrationTests(APITestCase):
    def test_register_user(self):
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

class JWTAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jwtuser', email='jwt@example.com', password='jwtpass123'
        )

    def test_jwt_token_obtain(self):
        url = reverse('token_obtain_pair')
        data = {'username': 'jwtuser', 'password': 'jwtpass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_me_endpoint(self):
        url = reverse('token_obtain_pair')
        data = {'username': 'jwtuser', 'password': 'jwtpass123'}
        resp = self.client.post(url, data)
        token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_url = reverse('user-me')
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'jwtuser')

class UserProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser', email='profile@example.com', password='profilepass123'
        )

    def authenticate(self):
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'username': self.user.username, 'password': 'profilepass123'})
        token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_update_profile(self):
        self.authenticate()
        url = reverse('userprofile-detail', kwargs={'pk': self.user.id})
        data = {'bio': 'Updated bio', 'company': 'New Company'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Updated bio')

    def test_upload_profile_picture(self):
        self.authenticate()
        url = reverse('userprofile-detail', kwargs={'pk': self.user.id})
        img = create_test_image()
        response = self.client.patch(url, {'profile_picture': img}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name.startswith('profile_pictures/'))

class PermissionTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='pass1')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='pass2')

    def test_user_cannot_access_others(self):
        url = reverse('token_obtain_pair')
        resp = self.client.post(url, {'username': 'user1', 'password': 'pass1'})
        token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url2 = reverse('userprofile-detail', kwargs={'pk': self.user2.id})
        response = self.client.get(url2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class OAuthEndpointTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        site, _ = Site.objects.get_or_create(domain='example.com', name='example.com')
        # Google SocialApp
        google_app, _ = SocialApp.objects.get_or_create(
            provider='google',
            name='Google',
            client_id='dummy',
            secret='dummy'
        )
        google_app.sites.add(site)
        # GitHub SocialApp
        github_app, _ = SocialApp.objects.get_or_create(
            provider='github',
            name='GitHub',
            client_id='dummy',
            secret='dummy'
        )
        github_app.sites.add(site)

    def test_google_login_endpoint(self):
        url = '/api/auth/social/google/'
        response = self.client.post(
            url,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_github_login_endpoint(self):
        url = '/api/auth/social/github/'
        response = self.client.post(
            url,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)