import logging
from typing import Any, Dict, List, NamedTuple, Optional, Set, Union
from django.http import HttpRequest
from django.contrib.auth.models import User
from math import ceil
from django.db.models import Count
from googleapiclient import discovery
from googleapiclient.discovery import Resource
from google.oauth2.credentials import Credentials
from allauth.socialaccount.models import SocialToken, SocialApp
from sync_youtube.models.playlist import LocalPlaylist, RemotePlaylist

from sync_youtube.models.song import YoutubeSong

GOOGLE_ACCOUNT_PROVIDER = "google"
GOOGLE_SOCIAL_APP_NAME = "google_social_app"
GOOGLE_SERVICE_NAME_YOUTUBE = "youtube"
YOUTUBE_CATEGORY_ID_MUSIC = "10"
YOUTUBE_MAX_VIDEO_PER_PLAYLIST = 200

logger = logging.getLogger("app")


class DummyRequest(NamedTuple):
    user: User


class YoutubeAPI:
    @staticmethod
    def _get_user_credentials(
        context: Union[HttpRequest, DummyRequest],
    ) -> Credentials:
        token = SocialToken.objects.get(account__user=context.user, account__provider=GOOGLE_ACCOUNT_PROVIDER)
        social_app = SocialApp.objects.get(name=GOOGLE_SOCIAL_APP_NAME)
        credentials = Credentials(
            token=token.token,
            refresh_token=token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=social_app.client_id,
            client_secret=social_app.secret,
        )
        return credentials

    @staticmethod
    def _get_youtube_service(
        context: Union[HttpRequest, DummyRequest],
    ) -> Resource:
        credentials = YoutubeAPI._get_user_credentials(context)
        return discovery.build(GOOGLE_SERVICE_NAME_YOUTUBE, 'v3', credentials=credentials)

    @staticmethod
    def _get_videos(
        youtube_service: Resource,
        **kwargs
    ) -> Dict[str, Any]:
        request = youtube_service.videos().list(
            part="snippet",
            maxResults=50,
            **kwargs
        )
        return request.execute()

    @staticmethod
    def get_liked_videos(
        context: Union[HttpRequest, DummyRequest]
    ) -> List[Dict[str, Any]]:
        youtube_service = YoutubeAPI._get_youtube_service(context)

        all_items: List[Dict[str, Any]] = []
        page_token: Optional[str] = ""
        while True:
            response = YoutubeAPI._get_videos(
                youtube_service=youtube_service,
                myRating="like",
                pageToken=page_token,
            )
            all_items.extend(response["items"])
            page_token = response.get("nextPageToken")

            if page_token is None:
                break

        return all_items

    @staticmethod
    def extract_liked_musics(
        context: Union[HttpRequest, DummyRequest],
    ) -> List[YoutubeSong]:
        all_liked_videos = YoutubeAPI.get_liked_videos(context)
        all_likeds_music = [
            video
            for video in all_liked_videos
            if video["snippet"]["categoryId"] == YOUTUBE_CATEGORY_ID_MUSIC
        ]

        existing_youtube_song_third_party_ids = set(
            YoutubeSong.objects.filter(
                user=context.user
            ).values_list("third_party_id", flat=True)
        )

        local_playlist, _ = LocalPlaylist.objects.get_or_create(user=context.user)

        youtube_songs_to_create: List[YoutubeSong] = [
            YoutubeSong(
                user=context.user,
                title=music["snippet"]["title"],
                description=music["snippet"]["description"],
                image_url=music["snippet"]["thumbnails"]["default"]["url"],
                third_party_id=music["id"],
                third_party_etag=music["etag"],
                local_playlist=local_playlist,
            )
            for music in all_likeds_music
            if music["id"] not in existing_youtube_song_third_party_ids
        ]

        created_youtube_songs = YoutubeSong.objects.bulk_create(youtube_songs_to_create)

        logger.info(
            "Created %s youtube songs (%s)",
            len(created_youtube_songs),
            ",".join(created_youtube_song.third_party_id for created_youtube_song in created_youtube_songs)
        )

        existing_youtube_song_third_party_ids.update(
            {song.third_party_id for song in created_youtube_songs}
        )

        songs_to_remove_third_party_ids = {
            third_party_id
            for third_party_id in existing_youtube_song_third_party_ids
            if third_party_id not in {
                music["id"]
                for music in all_likeds_music
            }
        }

        YoutubeSong.objects.filter(
            user=context.user,
            third_party_id__in=songs_to_remove_third_party_ids
        ).delete()

        logger.info(
            "Deleted %s youtube songs (%s)",
            len(songs_to_remove_third_party_ids),
            ",".join(songs_to_remove_third_party_ids)
        )
        return created_youtube_songs

    @staticmethod
    def make_playlists_split(
        context: Union[HttpRequest, DummyRequest],
    ) -> None:
        YoutubeSong.objects.filter(
            local_playlist__user=context.user,
            is_synched=False,
            should_not_exist=True,
        ).delete()  # Remove non-synched songs that should not be synched

        local_playlist = LocalPlaylist.objects.prefetch_related('songs', 'remote_playlists').get(user=context.user)
        non_full_remote_playlists = list(
            local_playlist.remote_playlists.annotate(
                num_songs=Count("songs", distinct=True)
            ).filter(
                num_songs__lt=YOUTUBE_MAX_VIDEO_PER_PLAYLIST,
            ).order_by(
                "created"
            )
        )

        unassigned_songs = set(local_playlist.songs.filter(remote_playlist__isnull=True))
        songs_to_update: Set[YoutubeSong] = set()
        for remote_playlist in non_full_remote_playlists:
            remaining_seats = YOUTUBE_MAX_VIDEO_PER_PLAYLIST - remote_playlist.num_songs

            for song in unassigned_songs:
                remaining_seats -= 1

                song.remote_playlist = remote_playlist
                songs_to_update.add(song)
                if remaining_seats == 0:
                    break

            unassigned_songs -= songs_to_update

        remaining_unassigned_songs_count = len(unassigned_songs)

        if remaining_unassigned_songs_count > 0:
            num_remote_playlist_to_create = ceil(remaining_unassigned_songs_count / YOUTUBE_MAX_VIDEO_PER_PLAYLIST)
            new_remote_playlists = YoutubeAPI._create_remote_playlists(
                context=context,
                num_playlists=num_remote_playlist_to_create,
                local_playlist=local_playlist,
            )
            for remote_playlist in new_remote_playlists:
                remaining_seats = YOUTUBE_MAX_VIDEO_PER_PLAYLIST
                for song in unassigned_songs:
                    remaining_seats -= 1

                    song.remote_playlist = remote_playlist
                    songs_to_update.add(song)
                    if remaining_seats == 0:
                        break

                unassigned_songs -= songs_to_update

        YoutubeSong.objects.bulk_update(
            songs_to_update,
            fields=["remote_playlist"],
        )

    def _create_remote_playlists(
        context: Union[HttpRequest, DummyRequest],
        num_playlists: int,
        local_playlist: LocalPlaylist,
    ) -> List[RemotePlaylist]:
        remote_playlist_to_create: List[RemotePlaylist] = []
        existing_playlists_count = local_playlist.remote_playlists.count()

        for i in range(num_playlists):
            remote_playlist_to_create.append(
                RemotePlaylist(
                    local_playlist=local_playlist,
                    title=f"{context.user.username}'s shared - {existing_playlists_count + i + 1}"
                )
            )

        RemotePlaylist.objects.bulk_create(remote_playlist_to_create)

        return remote_playlist_to_create

    @staticmethod
    def sync_remote_playlists(
        context: Union[HttpRequest, DummyRequest],
    ) -> None:
        youtube_service = YoutubeAPI._get_youtube_service(context=context)
        for remote_playlist in RemotePlaylist.objects.filter(is_synched=False, local_playlist__user=context.user):
            try:
                request = youtube_service.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": remote_playlist.title,
                        },
                        "status": {
                            "privacyStatus": "public"
                        }
                    }
                )
                response = request.execute()
                remote_playlist.third_party_id = response["id"]
                remote_playlist.third_party_etag = response["etag"]
                remote_playlist.is_synched = True
                remote_playlist.save()
                logger.info(
                    "Created youtube playlist: %s",
                    remote_playlist.third_party_id
                )
            except Exception as exc:
                logger.error("Failed to sync RemotePlaylist %s", remote_playlist.id, exc_info=True)

    @staticmethod
    def sync_remote_playlists_content(
        context: Union[HttpRequest, DummyRequest],
    ) -> None:
        youtube_service = YoutubeAPI._get_youtube_service(context=context)
        remote_playlist_ids = RemotePlaylist.objects.filter(
            local_playlist__user=context.user,
            is_synched=True,
        ).values_list("id", flat=True)

        # -------------------------------- #
        # Add new songs to remote playlist #
        # -------------------------------- #

        songs_to_add = YoutubeSong.objects.filter(
            is_synched=False,
            should_not_exist=False,
            remote_playlist_id__in=remote_playlist_ids,
        ).select_related("remote_playlist")

        songs_to_save: List[YoutubeSong] = []
        for song in songs_to_add:
            try:
                request = youtube_service.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": song.remote_playlist.third_party_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": song.third_party_id
                            }
                        }
                    }
                )
                request.execute()
                song.is_synched = True
                songs_to_save.append(song)
            except Exception as exc:
                logger.error("Failed to sync song {}", song.id, exc_info=True)

        logger.info(
            "Added %s youtube songs (%s) to remote playlists ",
            len(songs_to_save),
            ",".join(song.third_party_id for song in songs_to_save)
        )
        YoutubeSong.objects.bulk_update(songs_to_save, fields=["is_synched"])

        # -------------------------- #
        # Remove songs from playlist #
        # -------------------------- #

        songs_to_remove = YoutubeSong.objects.filter(
            is_synched=True,
            should_not_exist=True,
            remote_playlist_id__in=remote_playlist_ids,
        ).select_related("remote_playlist")

        songs_to_remove = []
        for song in songs_to_remove:
            try:
                request = youtube_service.playlistItems().delete(
                    id=song.third_party_playlist_item_id
                )
                request.execute()
                songs_to_remove.append(song)
            except Exception as exc:
                logger.error("Failed to remove song {}", song.id, exc_info=True)

        logger.info(
            "Removed %s youtube songs (%s) from remote playlists ",
            len(songs_to_remove),
            ",".join(song.third_party_id for song in songs_to_remove)
        )

        YoutubeSong.objects.filter(id__in={song.id for song in songs_to_remove}).delete()
