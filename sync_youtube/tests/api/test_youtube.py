from typing import Any, Dict
from unittest.mock import MagicMock, NonCallableMagicMock, call, patch
from sync_youtube.tests.shared import SyncYoutubeTestCase
from google.oauth2.credentials import Credentials
from sync_youtube.api.youtube import (
    GOOGLE_OAUTH2_URI,
    GOOGLE_SERVICE_NAME_YOUTUBE,
    GOOGLE_YOUTUBE_SERVICE_VERSION,
    YOUTUBE_CATEGORY_ID_MUSIC,
    YoutubeAPI
)
from sync_youtube.models.playlist import RemotePlaylist
from sync_youtube.models.song import YoutubeSong


class YoutubeAPITestCase(SyncYoutubeTestCase):
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

    @patch.object(YoutubeAPI, "get_liked_videos")
    def test_extract_liked_musics_success(
        self,
        mocked_get_liked_videos: MagicMock,
    ):
        # -------------------- #
        # Setup mocks and data #
        # -------------------- #

        existing_youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
        )

        deleted_youtube_song = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 3",
            description="Description for music 3",
            image_url="https://music.com/img3.jpg",
            third_party_id="Music3OnYoutubeID",
            third_party_etag="Music3OnYoutubeEtag",
        )

        new_song_created_remote_data: Dict[str, Any] = {
            "id": "Music2OnYoutubeID",
            "etag": "Music2OnYoutubeEtag",
            "snippet": {
                    "title": "Music 2",
                    "description": "Description for music 2",
                    "categoryId": YOUTUBE_CATEGORY_ID_MUSIC,
                    "thumbnails": {
                        "default": {
                            "url": "https://music.com/img2.jpg",
                        },
                    },
            }
        }
        remote_liked_videos = [
            {
                "id": existing_youtube_song.third_party_id,
                "etag": existing_youtube_song.third_party_etag,
                "snippet": {
                    "title": existing_youtube_song.title,
                    "description": existing_youtube_song.description,
                    "categoryId": YOUTUBE_CATEGORY_ID_MUSIC,
                    "thumbnails": {
                        "default": {
                            "url": existing_youtube_song.image_url,
                        },
                    },
                }
            },
            new_song_created_remote_data,
            {
                "id": "ComedyOnYoutubeID",
                "etag": "ComedyOnYoutubeEtag",
                "snippet": {
                    "title": "Comedy video 1",
                    "description": "Description for comedy video 2",
                    "categoryId": "9",
                    "thumbnails": {
                        "default": {
                            "url": "https://video.com/img1.jpg",
                        },
                    },
                }
            },
        ]

        mocked_get_liked_videos.return_value = remote_liked_videos

        # ------------------- #
        # Execute tested code #
        # ------------------- #

        created_youtube_songs, removed_songs_third_party_ids = YoutubeAPI.extract_liked_musics(context=self.context)

        # ----------------- #
        # Assert mock calls #
        # ----------------- #

        mocked_get_liked_videos.assert_called_once_with(self.context)

        # ----------- #
        # Assert data #
        # ----------- #

        expected_removed_songs_third_party_ids = {deleted_youtube_song.third_party_id}
        self.assertCountEqual(
            expected_removed_songs_third_party_ids,
            removed_songs_third_party_ids,
            "Unexpected songs were removed"
        )

        self.assertEqual(
            1,
            len(created_youtube_songs),
            "Unexpected songs were created"
        )

        [created_song] = created_youtube_songs

        self.assertEqual(
            created_song.user,
            self.user,
            "Unexpected YoutubeSong.user value"
        )

        self.assertEqual(
            created_song.local_playlist,
            self.local_playlist,
            "Unexpected YoutubeSong.local_playlist value"
        )

        self.assertEqual(
            created_song.title,
            new_song_created_remote_data["snippet"]["title"],
            "Unexpected YoutubeSong.title value"
        )

        self.assertEqual(
            created_song.description,
            new_song_created_remote_data["snippet"]["description"],
            "Unexpected YoutubeSong.description value"
        )

        self.assertEqual(
            created_song.image_url,
            new_song_created_remote_data["snippet"]["thumbnails"]["default"]["url"],
            "Unexpected YoutubeSong.image_url value"
        )

        self.assertEqual(
            created_song.third_party_id,
            new_song_created_remote_data["id"],
            "Unexpected YoutubeSong.third_party_id value"
        )

        self.assertEqual(
            created_song.third_party_etag,
            new_song_created_remote_data["etag"],
            "Unexpected YoutubeSong.third_party_etag value"
        )

        self.assertEqual(
            2,
            YoutubeSong.objects.filter(user=self.user).count(),
            "Unexpected amount of youtube songs found for user"
        )

        self.assertEqual(
            0,
            YoutubeSong.objects.filter(user=self.user, third_party_id=deleted_youtube_song.third_party_id).count(),
            "Unexpectedly found a song that should have been deleted"
        )

    @patch("sync_youtube.api.youtube.YOUTUBE_MAX_VIDEO_PER_PLAYLIST", 2)
    def test_make_playlists_split_success(self):
        # -------------------- #
        # Setup data #
        # -------------------- #

        existing_remote_playlist = RemotePlaylist.objects.create(
            local_playlist=self.local_playlist,
            title=f"{self.user.username}'shared - 1",
            third_party_id="remote_playlist_id",
            third_party_etag="remote_playlist_etag",
            is_synched=True,
        )

        song_in_remote_playlist = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            remote_playlist=existing_remote_playlist,
            title="Music 1",
            description="Description for music 1",
            image_url="https://music.com/img1.jpg",
            third_party_id="Music1OnYoutubeID",
            third_party_etag="Music1OnYoutubeEtag",
        )

        YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 2",
            description="Description for music 2",
            image_url="https://music.com/img2.jpg",
            third_party_id="Music2OnYoutubeID",
            third_party_etag="Music2OnYoutubeEtag",
        )

        YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            title="Music 3",
            description="Description for music 3",
            image_url="https://music.com/img3.jpg",
            third_party_id="Music3OnYoutubeID",
            third_party_etag="Music3OnYoutubeEtag",
        )

        # ------------------- #
        # Execute tested code #
        # ------------------- #

        YoutubeAPI.make_playlists_split(self.context)

        # ----------- #
        # Assert data #
        # ----------- #

        self.assertEqual(
            2,
            self.local_playlist.remote_playlists.count(),
            "Unexpected count of remote playlists",
        )

        existing_remote_playlist.refresh_from_db()
        self.assertEqual(
            2,
            existing_remote_playlist.songs.count(),
            "Unexpected count of songs in existing_remote_playlist",
        )

        created_remote_playlist = RemotePlaylist.objects.filter(
            local_playlist=self.local_playlist
        ).exclude(id=existing_remote_playlist.id).get()
        self.assertEqual(
            1,
            created_remote_playlist.songs.count(),
            "Unexpected count of songs in existing_remote_playlist",
        )

    @patch.object(YoutubeAPI, "_get_youtube_service")
    def test_sync_remote_playlist_success(
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
                "id": "remote_playlist_id",
                "etag": "remote_playlist_etag",
            },
            AssertionError("Unexpected call to youtube_service.playlist().insert()")
        ]
        mocked_request = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_execute,
        )
        mocked_youtube_service_playlists_insert_method = MagicMock(
            spec=[],
            return_value=mocked_request,
        )
        mocked_youtube_service_playlists_object = NonCallableMagicMock(
            spec=[],
            insert=mocked_youtube_service_playlists_insert_method,
        )
        mocked_youtube_service_playlists_method = MagicMock(
            spec=[],
            return_value=mocked_youtube_service_playlists_object,
        )
        mocked__get_youtube_service.return_value = NonCallableMagicMock(
            spec=[],
            playlists=mocked_youtube_service_playlists_method,
        )

        remote_playlist_to_sync = RemotePlaylist.objects.create(
            local_playlist=self.local_playlist,
            title="foo",
        )

        # ------------------- #
        # Execute tested code #
        # ------------------- #

        YoutubeAPI.sync_remote_playlists(context=self.context)

        # ------------------- #
        # Assert mocked calls #
        # ------------------- #

        mocked__get_youtube_service.assert_called_once_with(context=self.context)

        mocked_youtube_service_playlists_method.assert_called_once_with()

        mocked_youtube_service_playlists_insert_method.assert_called_once_with(
            part="snippet, status",
            body={
                "snippet": {
                    "title": remote_playlist_to_sync.title,
                },
                "status": {
                    "privacyStatus": "public",
                }
            }
        )

        mocked_request_execute.assert_called_once_with()

        # ----------- #
        # Assert data #
        # ----------- #

        remote_playlist_to_sync.refresh_from_db()
        self.assertTrue(
            remote_playlist_to_sync.is_synched,
            "remote_playlist_to_sync was not flagged as synched"
        )

        self.assertEqual(
            "remote_playlist_id",
            remote_playlist_to_sync.third_party_id,
            "Incorrect remote_playlist_to_sync.third_party_id"
        )

        self.assertEqual(
            "remote_playlist_etag",
            remote_playlist_to_sync.third_party_etag,
            "Incorrect remote_playlist_to_sync.third_party_etag"
        )

    @patch("sync_youtube.api.youtube.logger")
    @patch.object(YoutubeAPI, "_get_youtube_service")
    def test_sync_remote_playlist_error(
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
            RuntimeError(),
        ]
        mocked_request = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_execute,
        )
        mocked_youtube_service_playlists_insert_method = MagicMock(
            spec=[],
            return_value=mocked_request,
        )
        mocked_youtube_service_playlists_object = NonCallableMagicMock(
            spec=[],
            insert=mocked_youtube_service_playlists_insert_method,
        )
        mocked_youtube_service_playlists_method = MagicMock(
            spec=[],
            return_value=mocked_youtube_service_playlists_object,
        )
        mocked__get_youtube_service.return_value = NonCallableMagicMock(
            spec=[],
            playlists=mocked_youtube_service_playlists_method,
        )

        remote_playlist_to_sync = RemotePlaylist.objects.create(
            local_playlist=self.local_playlist,
            title="foo",
        )

        # ------------------- #
        # Execute tested code #
        # ------------------- #

        YoutubeAPI.sync_remote_playlists(context=self.context)

        # ------------------- #
        # Assert mocked calls #
        # ------------------- #

        mocked__get_youtube_service.assert_called_once_with(context=self.context)

        mocked_youtube_service_playlists_method.assert_called_once_with()

        mocked_youtube_service_playlists_insert_method.assert_called_once_with(
            part="snippet, status",
            body={
                "snippet": {
                    "title": remote_playlist_to_sync.title,
                },
                "status": {
                    "privacyStatus": "public",
                }
            }
        )

        mocked_request_execute.assert_called_once_with()

        mocked_logger.exception.assert_called_once_with(
            "Failed to sync RemotePlaylist %s",
            remote_playlist_to_sync.id,
            exc_info=True,
        )

        # ----------- #
        # Assert data #
        # ----------- #

        remote_playlist_to_sync.refresh_from_db()
        self.assertFalse(
            remote_playlist_to_sync.is_synched,
            "remote_playlist_to_sync was inadequately flagged as synched"
        )

        self.assertIsNone(
            remote_playlist_to_sync.third_party_id,
            "Incorrect remote_playlist_to_sync.third_party_id, expected None"
        )

        self.assertIsNone(
            remote_playlist_to_sync.third_party_etag,
            "Incorrect remote_playlist_to_sync.third_party_etag, expected None"
        )

    @patch.object(YoutubeAPI, "_get_youtube_service")
    def test_sync_remote_playlists_content_success(
        self,
        mocked__get_youtube_service: MagicMock,
    ):
        # ------------------------- #
        # Setting up data and mocks #
        # ------------------------- #

        mocked_request_insert_execute = MagicMock(
            spec=[],
        )
        mocked_request_insert_execute.side_effect = [
            {
                "id": "remote_playlist_item_id",
            },
            AssertionError("Unexpected call to youtube_service.playlistItems().insert()")
        ]
        mocked_request_insert = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_insert_execute,
        )
        mocked_youtube_service_playlistItems_insert_method = MagicMock(
            spec=[],
            return_value=mocked_request_insert,
        )

        mocked_request_delete_execute = MagicMock(
            spec=[],
        )
        mocked_request_delete_execute.side_effect = [
            None,
            None,
            AssertionError("Unexpected call to youtube_service.playlistItems().delete()")
        ]
        mocked_request_delete = NonCallableMagicMock(
            spec=[],
            execute=mocked_request_delete_execute,
        )
        mocked_youtube_service_playlistItems_delete_method = MagicMock(
            spec=[],
            return_value=mocked_request_delete,
        )
        mocked_youtube_service_playlistItems_object = NonCallableMagicMock(
            spec=[],
            insert=mocked_youtube_service_playlistItems_insert_method,
            delete=mocked_youtube_service_playlistItems_delete_method,
        )
        mocked_youtube_service_playlistItems_method = MagicMock(
            spec=[],
            return_value=mocked_youtube_service_playlistItems_object,
        )
        mocked__get_youtube_service.return_value = NonCallableMagicMock(
            spec=[],
            playlistItems=mocked_youtube_service_playlistItems_method,
        )

        remote_playlist = RemotePlaylist.objects.create(
            local_playlist=self.local_playlist,
            title="foo",
            third_party_id="remote_playlist_id",
            is_synched=True,
        )

        song_to_add = YoutubeSong.objects.create(
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

        song_to_remove = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            remote_playlist=remote_playlist,
            title="Music 2",
            description="Description for music 2",
            image_url="https://music.com/img2.jpg",
            third_party_id="Music2OnYoutubeID",
            third_party_etag="Music2OnYoutubeEtag",
            third_party_playlist_item_id="Music2InPlaylistID",
            is_synched=True,
            should_not_exist=True,
        )

        song_to_unpublish = YoutubeSong.objects.create(
            user=self.user,
            local_playlist=self.local_playlist,
            remote_playlist=remote_playlist,
            title="Music 3",
            description="Description for music 3",
            image_url="https://music.com/img3.jpg",
            third_party_id="Music3OnYoutubeID",
            third_party_playlist_item_id="Music3InPlaylistID",
            third_party_etag="Music3OnYoutubeEtag",
            is_synched=True,
            should_not_be_published=True,
        )

        # ------------------- #
        # Execute tested code #
        # ------------------- #

        YoutubeAPI.sync_remote_playlists_content(context=self.context)

        # ------------------- #
        # Assert mocked calls #
        # ------------------- #

        mocked__get_youtube_service.assert_called_once_with(context=self.context)
        expected_mocked_youtube_service_playlistItems_method_calls = [
            call(),
            call(),
            call(),
        ]

        self.assertCountEqual(
            expected_mocked_youtube_service_playlistItems_method_calls,
            mocked_youtube_service_playlistItems_method.call_args_list,
            "unexpected calls to mocked_youtube_service_playlistItems_method",
        )

        mocked_youtube_service_playlistItems_insert_method.assert_called_once_with(
            part="snippet,id",
            body={
                "snippet": {
                    "playlistId": remote_playlist.third_party_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": song_to_add.third_party_id,
                    }
                },
            }
        )

        mocked_request_insert_execute.assert_called_once_with()

        expected_mocked_youtube_service_playlistItems_delete_method_calls = [
            call(id=song_to_remove.third_party_playlist_item_id),
            call(id=song_to_unpublish.third_party_playlist_item_id),
        ]
        self.assertCountEqual(
            expected_mocked_youtube_service_playlistItems_delete_method_calls,
            mocked_youtube_service_playlistItems_delete_method.call_args_list,
            "Unexpected calls to mocked_youtube_service_playlistItems_delete_method"
        )

        expected_mocked_request_delete_execute_calls = [
            call(),
            call(),
        ]
        self.assertCountEqual(
            expected_mocked_request_delete_execute_calls,
            mocked_request_delete_execute.call_args_list,
            "unexpected calls to mocked_request_delete_execute"
        )

        # ----------- #
        # Assert data #
        # ----------- #
        song_to_add.refresh_from_db()
        self.assertEqual(
            "remote_playlist_item_id",
            song_to_add.third_party_playlist_item_id,
            "Unexpected third_party_playlist_item_id for song_to_add",
        )
        self.assertTrue(
            song_to_add.is_synched,
            "Songs to add was not flagged as synched"
        )

        self.assertIsNone(
            YoutubeSong.objects.filter(id=song_to_remove.id, user=self.user).first(),
            "song_to_remove was not properly deleted from DB"
        )

        song_to_unpublish.refresh_from_db()
        self.assertFalse(
            song_to_unpublish.is_synched,
            "song_to_unpublish is inadequatly flagged as synched"
        )
