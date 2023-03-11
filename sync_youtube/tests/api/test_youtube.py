from datetime import timedelta
from unittest.mock import MagicMock, NonCallableMagicMock, call, patch
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.socialaccount.providers.google.provider import GoogleProvider
from google.oauth2.credentials import Credentials
from sync_youtube.api.youtube import (
    GOOGLE_OAUTH2_URI,
    GOOGLE_SERVICE_NAME_YOUTUBE,
    GOOGLE_SOCIAL_APP_NAME,
    GOOGLE_YOUTUBE_SERVICE_VERSION,
    DummyRequest,
    YoutubeAPI
)


class YoutubeAPITestCase(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(username="Test User", email="test_user@test.te")
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

    def test__get_user_credentials_success(self):
        expected_credentials = Credentials(
            token=self.social_token.token,
            refresh_token=self.social_token.token_secret,
            token_uri=GOOGLE_OAUTH2_URI,
            client_id=self.social_app.client_id,
            client_secret=self.social_app.secret,
        )

        credentials = YoutubeAPI._get_user_credentials(self.context)

        self.assertEqual(
            vars(expected_credentials),
            vars(credentials),
            "Unexpected credentials generated"
        )

    @patch.object(YoutubeAPI, "_get_user_credentials")
    @patch("sync_youtube.api.youtube.discovery")
    def test__get_youtube_service(
        self,
        mocked_discovery: NonCallableMagicMock,
        mocked__get_user_credentials: MagicMock,
    ):
        # ------------------------- #
        # Setting up data and mocks #
        # ------------------------- #

        mocked_build = MagicMock(
            spec=[],
        )
        mocked_discovery.spec = []
        mocked_discovery.build = mocked_build

        mocked__get_user_credentials.return_value = "FILLER"

        # --------------------- #
        # Executing tested code #
        # --------------------- #

        YoutubeAPI._get_youtube_service(context=self.context)

        # -------------------- #
        # Asserting mock calls #
        # -------------------- #

        mocked__get_user_credentials.assert_called_once_with(self.context)
        mocked_build.assert_called_once_with(
            GOOGLE_SERVICE_NAME_YOUTUBE,
            GOOGLE_YOUTUBE_SERVICE_VERSION,
            credentials="FILLER"
        )

    @patch.object(YoutubeAPI, "_get_youtube_service")
    def test_get_liked_videos_success(
        self,
        mocked__get_youtube_service: MagicMock,
    ):
        # ------------------------- #
        # Setting up data and mocks #
        # ------------------------- #

        mocked_request_execute = MagicMock(
            spec=[],
        )
        mocked_request_execute.side_effect = [
            {
                "items": [
                    "foo",
                    "bar",
                ],
                "nextPageToken": "next_page",
            },
            {
                "items": [
                    "fooBar",
                    "barFoo",
                ],
            },
            AssertionError("Unexpected call to youtube_service.videos().list()")
        ]
        mocked_request = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_execute,
        )
        mocked_youtube_service_videos_list_method = MagicMock(
            spec=[],
            return_value=mocked_request,
        )
        mocked_youtube_service_videos_object = NonCallableMagicMock(
            spec=[],
            list=mocked_youtube_service_videos_list_method,
        )
        mocked_youtube_service_videos_method = MagicMock(
            spec=[],
            return_value=mocked_youtube_service_videos_object,
        )
        mocked__get_youtube_service.return_value = NonCallableMagicMock(
            spec=[],
            videos=mocked_youtube_service_videos_method,
        )

        # --------------------- #
        # Executing tested code #
        # --------------------- #

        results = YoutubeAPI.get_liked_videos(context=self.context)

        # --------------------- #
        # Asserting mocks calls #
        # --------------------- #
        mocked__get_youtube_service.assert_called_once_with(self.context)

        expected_youtube_videos_method_call_args_list = [
            call(),
            call(),
        ]

        self.assertCountEqual(
            mocked_youtube_service_videos_method.call_args_list,
            expected_youtube_videos_method_call_args_list,
            "Unexpected call to youtube_service.videos method"
        )

        expected_youtube_videos_list_method_call_args_list = [
            call(
                part="snippet",
                maxResults=50,
                myRating="like",
                pageToken="",
            ),
            call(
                part="snippet",
                maxResults=50,
                myRating="like",
                pageToken="next_page",
            ),
        ]

        self.assertCountEqual(
            mocked_youtube_service_videos_list_method.call_args_list,
            expected_youtube_videos_list_method_call_args_list,
            "Unexpected call to youtube_service.videos.list method"
        )

        expected_request_execute_call_args_list = [
            call(),
            call(),
        ]

        self.assertCountEqual(
            mocked_request_execute.call_args_list,
            expected_request_execute_call_args_list,
            "Unexpected call to youtube_service.videos.list.execute method"
        )

        # ----------- #
        # Assert data #
        # ----------- #

        expected_results = [
            "foo",
            "bar",
            "fooBar",
            "barFoo",
        ]

        self.assertCountEqual(
            expected_results,
            results,
            "Unexpected results content"
        )

    @patch("sync_youtube.api.youtube.logger")
    @patch.object(YoutubeAPI, "_get_youtube_service")
    def test_get_liked_videos_error(
        self,
        mocked__get_youtube_service: MagicMock,
        mocked_logger: NonCallableMagicMock,
    ):
        # ------------------------- #
        # Setting up data and mocks #
        # ------------------------- #

        mocked_request_execute = MagicMock(
            spec=[],
        )
        mocked_request_execute.side_effect = [
            RuntimeError()
        ]
        mocked_request = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_execute,
        )
        mocked_youtube_service_videos_list_method = MagicMock(
            spec=[],
            return_value=mocked_request,
        )
        mocked_youtube_service_videos_object = NonCallableMagicMock(
            spec=[],
            list=mocked_youtube_service_videos_list_method,
        )
        mocked_youtube_service_videos_method = MagicMock(
            spec=[],
            return_value=mocked_youtube_service_videos_object,
        )
        mocked__get_youtube_service.return_value = NonCallableMagicMock(
            spec=[],
            videos=mocked_youtube_service_videos_method,
        )

        # --------------------- #
        # Executing tested code #
        # --------------------- #
        with self.assertRaises(RuntimeError):
            YoutubeAPI.get_liked_videos(context=self.context)

        # --------------------- #
        # Asserting mocks calls #
        # --------------------- #
        mocked__get_youtube_service.assert_called_once_with(self.context)

        mocked_youtube_service_videos_method.assert_called_once_with()

        mocked_youtube_service_videos_list_method.assert_called_once_with(
            part="snippet",
            maxResults=50,
            myRating="like",
            pageToken="",
        )

        mocked_request_execute.assert_called_once_with()

        mocked_logger.exception.assert_called_once_with(
            "Failed to fetch videos",
            exc_info=True,
        )
