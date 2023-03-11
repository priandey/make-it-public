from django.test import TestCase
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.socialaccount.providers.google.provider import GoogleProvider, GoogleAccount

# Create your tests here.


class YoutubeAPITestCase(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(username="Test User", email="test_user@test.te")
        return super().setUpTestData()

    def test_foo(self):
        pass
