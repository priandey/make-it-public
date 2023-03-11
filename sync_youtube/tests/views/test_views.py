from unittest.mock import MagicMock, patch
from sync_youtube.models.playlist import RemotePlaylist
from sync_youtube.models.song import YoutubeSong
from sync_youtube.tests.shared import SyncYoutubeTestCase
from django.test import Client
from django.contrib.auth.models import User


class ViewsTestCase(SyncYoutubeTestCase):
    def setUp(self) -> None:
        self.anonymous_client = Client()
        self.logged_in_client = Client()
        self.logged_in_client.login(username=self.user.username, password=self.user_password)
        return super().setUp()

    def test_index_no_auth(self):
        response = self.anonymous_client.get("/")

        self.assertTemplateUsed(
            response,
            "sync_youtube/index.html"
        )

        self.assertCountEqual(
            [],
            response.context["liked_songs"],
            "Unexpectedly found 'liked_songs' in request context",
        )

        self.assertCountEqual(
            [],
            response.context["user_playlist_ids"],
            "Unexpectedly found 'liked_songs' in request context",
        )

        self.assertTrue(
            response.wsgi_request.user.is_anonymous,
            "User of anonymous request was not anonymous"
        )

    def test_index_with_auth(self):
        remote_playlist = RemotePlaylist.objects.create(
            title="foo",
            third_party_id="fooId",
            local_playlist=self.local_playlist,
            is_synched=True,
        )
        RemotePlaylist.objects.create(
            title="bar",
            local_playlist=self.local_playlist,
            is_synched=False,
        )
        youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            remote_playlist=remote_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
            is_synched=False,
            third_party_playlist_item_id=None,
        )

        response = self.logged_in_client.get("/")

        self.assertTemplateUsed(
            response,
            "sync_youtube/index.html"
        )

        # FIXME Also test ordering.
        self.assertCountEqual(
            [
                youtube_song,
            ],
            response.context["liked_songs"],
            "Unexpectedly found 'liked_songs' in request context",
        )

        self.assertCountEqual(
            [
                remote_playlist.third_party_id,
            ],
            response.context["user_playlist_ids"],
            "Unexpectedly found 'liked_songs' in request context",
        )

        self.assertEqual(
            self.user,
            response.wsgi_request.user,
            "Wrong user found in the response"
        )

    def test_policies_success(self):
        response = self.anonymous_client.get("/policies/")
        self.assertTemplateUsed(
            response,
            "sync_youtube/policies.html",
        )

    def test_terms_of_service_success(self):
        response = self.anonymous_client.get("/terms-of-service/")
        self.assertTemplateUsed(
            response,
            "sync_youtube/terms-of-service.html",
        )

    @patch("sync_youtube.views.YoutubeAPI.extract_liked_musics")
    @patch("sync_youtube.views.YoutubeAPI.make_playlists_split")
    def test_fetch_songs_success(
        self,
        mocked_make_playlist_split: MagicMock,
        mocked_extract_liked_musics: MagicMock,
    ):
        response = self.anonymous_client.get("/fetch-songs/")

        mocked_extract_liked_musics.assert_called_once_with(response.wsgi_request)
        mocked_make_playlist_split.assert_called_once_with(response.wsgi_request)

        self.assertRedirects(
            response,
            expected_url="/",
            status_code=301,
        )

    @patch("sync_youtube.views.YoutubeAPI.sync_remote_playlists")
    @patch("sync_youtube.views.YoutubeAPI.sync_remote_playlists_content")
    def test_publish_songs_success(
        self,
        mocked_sync_remote_playlists_content: MagicMock,
        mocked_sync_remote_playlists: MagicMock,
    ):
        response = self.anonymous_client.get("/publish-songs/")

        mocked_sync_remote_playlists_content.assert_called_once_with(response.wsgi_request)
        mocked_sync_remote_playlists.assert_called_once_with(response.wsgi_request)

        self.assertRedirects(
            response,
            expected_url="/",
            status_code=301,
        )

    def test_switch_song_get_error(self):
        response = self.anonymous_client.get('/switch-song/')
        self.assertEqual(
            404,
            response.status_code,
            "Response status was not 404"
        )

    def test_switch_song_post_success(self):
        youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
            is_synched=False,
            should_not_be_published=True,
        )

        response = self.logged_in_client.post(
            '/switch-song/',
            data={"id": str(youtube_song.id)},
            content_type="application/json"
        )

        self.assertEqual(
            200,
            response.status_code,
            "Response status was not 200"
        )

        youtube_song.refresh_from_db()
        self.assertFalse(
            youtube_song.should_not_be_published,
            "youtube_song.should_not_be_published has not been toggled"
        )

    def test_switch_song_post_error_malformed_input_id(self):
        youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
            is_synched=False,
            should_not_be_published=True,
        )

        response = self.logged_in_client.post(
            '/switch-song/',
            data={"malformed_id": str(youtube_song.id)},
            content_type="application/json"
        )

        self.assertEqual(
            404,
            response.status_code,
            "Response status was not 404"
        )

        youtube_song.refresh_from_db()
        self.assertTrue(
            youtube_song.should_not_be_published,
            "youtube_song.should_not_be_published has been toggled"
        )

    def test_switch_song_post_error_song_not_found(self):
        youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
            is_synched=False,
            should_not_be_published=True,
        )
        other_user = User.objects.create_user(username="foo", password="bar")
        client = Client()
        client.login(username="foo", password="bar")

        response = client.post(
            '/switch-song/',
            data={"id": str(youtube_song.id)},
            content_type="application/json"
        )

        self.assertEqual(
            404,
            response.status_code,
            "Response status was not 404"
        )

        youtube_song.refresh_from_db()
        self.assertTrue(
            youtube_song.should_not_be_published,
            "youtube_song.should_not_be_published has been toggled"
        )
