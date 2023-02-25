import uuid
from django.db import models
from django.contrib.auth.models import User


class LocalPlaylist(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=True)

    should_update = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)


class RemotePlaylist(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    local_playlist = models.ForeignKey(
        LocalPlaylist,
        on_delete=models.CASCADE,
        related_name="remote_playlists"
    )
    title = models.CharField(max_length=255, null=False, unique=True)
    third_party_id = models.CharField(max_length=255, null=True)
    third_party_etag = models.CharField(max_length=255, null=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    is_synched = models.BooleanField(default=False)
