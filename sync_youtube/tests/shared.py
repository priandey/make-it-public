from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.socialaccount.providers.google.provider import GoogleProvider
from sync_youtube.models.playlist import LocalPlaylist
from sync_youtube.api.youtube import GOOGLE_SOCIAL_APP_NAME, DummyRequest
from datetime import timedelta


class SyncYoutubeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user_password = "astrongpassword"
        cls.user = User.objects.create_user(username="Test User", email="test_user@test.te", password=cls.user_password)
        cls.local_playlist = LocalPlaylist.objects.create(user=cls.user)
        cls.social_account = SocialAccount.objects.create(
            user=cls.user,
            provider=GoogleProvider.id,
            uid="0123456789",
            extra_data={
                'at_hash': 'GyMEAKNRJ4nSNACXiOILpg',
                'aud': '987654321.apps.googleusercontent.com',
                'azp': '987654321.apps.googleusercontent.com',
                'email': 'testuser-1234@pages.plusgoogle.com',
                'email_verified': True,
                'exp': 1678380246,
                'given_name': 'Test User',
                'iat': 1678376646,
                'iss': 'https://accounts.google.com',
                'locale': 'fr',
                'name': 'Test User',
                'picture': 'http://example.com/img.jpg',
                'sub': '0123456789'
            }
        )
        cls.social_app = SocialApp.objects.create(
            provider=GoogleProvider.id,
            name=GOOGLE_SOCIAL_APP_NAME,
            client_id="123123123",
            secret="iamthesecret",
            key="iamthekey",
        )
        cls.social_token = SocialToken.objects.create(
            account=cls.social_account,
            app=cls.social_app,
            expires_at=timezone.now() + timedelta(hours=2),
            token="1234567890987654321",
            token_secret="AZERTYUIOP"
        )
        cls.context = DummyRequest(user=cls.user)
        return super().setUpTestData()
