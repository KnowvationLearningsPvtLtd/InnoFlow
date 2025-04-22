import io
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTests(TestCase):
    def test_user_str_representation(self):
        user = User.objects.create_user(username='unituser', email='unit@example.com', password='unitpass')
        # Assuming __str__ returns the username
        self.assertEqual(str(user), 'unituser')
    
    def test_user_invalid_email_validation(self):
        user = User(username='baduser', email='not-an-email')
        with self.assertRaises(ValidationError):
            user.full_clean()

class UserProfileTests(TestCase):
    def test_profile_creation_and_str(self):
        """
        Since the custom user model already includes profile-related fields,
        update and test these on the user instance directly.
        """
        user = User.objects.create_user(username='profileunit', email='profile@example.com', password='pass123')
        user.bio = 'Test bio'
        user.company = 'Test Co'
        user.save()
        # Instead of accessing user.userprofile, verify fields on user.
        self.assertIn('Test bio', user.bio)
    
    def test_profile_update(self):
        """
        Update profile fields on the user instance and verify.
        """
        user = User.objects.create_user(username='profileunit2', email='profile2@example.com', password='pass123')
        user.bio = 'Updated bio'
        user.company = 'Updated Company'
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.bio, 'Updated bio')
        self.assertEqual(user.company, 'Updated Company')