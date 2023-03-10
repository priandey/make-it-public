from django.db import models
from django.contrib.auth.models import User
from sync_youtube.models.playlist import RemotePlaylist, LocalPlaylist
import uuid


class YoutubeSong(models.Model):
    class Meta:
        unique_together = [
            ("user_id", "third_party_id")
        ]
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="songs")

    local_playlist = models.ForeignKey(
        LocalPlaylist,
        on_delete=models.SET_DEFAULT,
        related_name="songs",
        null=True,
        default=None,
    )
    remote_playlist = models.ForeignKey(
        RemotePlaylist,
        on_delete=models.SET_DEFAULT,
        related_name="songs",
        null=True,
        default=None,
    )

    title = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)

    image_url = models.URLField()
    third_party_id = models.CharField(max_length=255, null=False)
    third_party_etag = models.CharField(max_length=255, null=False)
    third_party_playlist_item_id = models.CharField(max_length=255, null=True)

    created = models.DateField(auto_now_add=True, editable=False)
    is_synched = models.BooleanField(default=False)
    should_not_exist = models.BooleanField(default=False)
    should_not_be_published = models.BooleanField(default=False)

    def __repr__(self) -> str:
        return (
            f"{self.user.username} - {self.title!r}"
        )

    def __str__(self) -> str:
        return (
            f"{self.user.username} - {self.title!r}"
        )
