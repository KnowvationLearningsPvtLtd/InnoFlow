from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()

class UserIntegrationTests(APITestCase):

    def test_registration_and_login(self):
        # Register a new user
        url = reverse('register')
        reg_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
            'first_name': 'Integration',
            'last_name': 'User'
        }
        reg_resp = self.client.post(url, reg_data)
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)
        # Login to obtain JWT tokens
        token_url = reverse('token_obtain_pair')
        token_resp = self.client.post(token_url, {'username': 'integrationuser', 'password': 'StrongPass123'})
        self.assertEqual(token_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', token_resp.data)
        access = token_resp.data['access']
        # Get profile via "me" endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me_url = reverse('user-me')
        me_resp = self.client.get(me_url)
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(me_resp.data['username'], 'integrationuser')

    def test_profile_update(self):
        # Create and login user
        user = User.objects.create_user(username='profileuser', email='profile@ex.com', password='pass1234')
        token_url = reverse('token_obtain_pair')
        token_resp = self.client.post(token_url, {'username': user.username, 'password': 'pass1234'})
        access = token_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        # Update profile using the "profiles" endpoint (router name 'userprofile-detail')
        update_url = reverse('userprofile-detail', kwargs={'pk': user.id})
        patch_data = {'bio': 'Updated bio', 'company': 'Awesome Inc.'}
        update_resp = self.client.patch(update_url, patch_data)
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.bio, 'Updated bio')
        self.assertEqual(user.company, 'Awesome Inc.')

    def test_password_reset_flow(self):
        # Create user and request password reset
        user = User.objects.create_user(username='resetuser', email='resetuser@ex.com', password='oldpass123')
        reset_url = reverse('password-reset')
        resp = self.client.post(reset_url, {'email': 'resetuser@ex.com'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # An email should be sent
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        # Extract uid and token from URL in email (assuming URL format from settings)
        # For testing, we generate uid and token directly.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # Reset confirm
        reset_confirm_url = reverse('password-reset-confirm')
        confirm_resp = self.client.post(reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': 'newpass123'
        })
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))

    def test_email_verification_flow(self):
        # Create inactive user
        user = User.objects.create_user(username='verifyuser', email='verify@ex.com', password='verifypass', is_active=False)
        # Request verification
        verify_req_url = reverse('email-verify')
        req_resp = self.client.post(verify_req_url, {'email': 'verify@ex.com'})
        self.assertEqual(req_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        # Generate uid and token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # Confirm verification
        verify_conf_url = reverse('email-verify-confirm')
        conf_resp = self.client.post(verify_conf_url, {'uid': uid, 'token': token})
        self.assertEqual(conf_resp.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_full_user_flow_integration(self):
        # Full integration test: registration -> login -> profile update -> password reset -> email verify
        # Register
        reg_url = reverse('register')
        reg_data = {
            'username': 'fullflowuser',
            'email': 'fullflow@ex.com',
            'password': 'FullFlowPass1',
            'password2': 'FullFlowPass1',
            'first_name': 'Full',
            'last_name': 'Flow'
        }
        reg_resp = self.client.post(reg_url, reg_data)
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)
        # Login
        token_url = reverse('token_obtain_pair')
        token_resp = self.client.post(token_url, {'username': 'fullflowuser', 'password': 'FullFlowPass1'})
        access = token_resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        # Update profile
        user = User.objects.get(username='fullflowuser')
        profile_update_url = reverse('userprofile-detail', kwargs={'pk': user.id})
        update_data = {'bio': 'Integration bio', 'company': 'Integration Co.'}
        upd_resp = self.client.patch(profile_update_url, update_data)
        self.assertEqual(upd_resp.status_code, status.HTTP_200_OK)
        # Request password reset
        reset_url = reverse('password-reset')
        reset_resp = self.client.post(reset_url, {'email': 'fullflow@ex.com'})
        self.assertEqual(reset_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(mail.outbox) >= 1)
        # Email verification (simulate by manually generating token)
        user.is_active = False
        user.save()
        # Clear authentication to access email verification anonymously.
        self.client.credentials()
        verify_req_url = reverse('email-verify')
        ver_req_resp = self.client.post(verify_req_url, {'email': 'fullflow@ex.com'})
        self.assertEqual(ver_req_resp.status_code, status.HTTP_200_OK)
        # Confirm email
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_conf_url = reverse('email-verify-confirm')
        ver_conf_resp = self.client.post(verify_conf_url, {'uid': uid, 'token': token})
        self.assertEqual(ver_conf_resp.status_code, status.HTTP_200_OK)
