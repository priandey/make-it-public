# Generated by Django 3.2.18 on 2023-02-18 16:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sync_youtube', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocalPlaylist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='youtubesong',
            name='is_synched',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='youtubesong',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='songs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='RemotePlaylist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255, unique=True)),
                ('third_party_id', models.CharField(max_length=255, null=True)),
                ('third_party_etag', models.CharField(max_length=255, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_synched', models.BooleanField(default=False)),
                ('local_playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remote_playlists', to='sync_youtube.localplaylist')),
            ],
        ),
        migrations.AddField(
            model_name='youtubesong',
            name='local_playlist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='songs', to='sync_youtube.localplaylist'),
        ),
        migrations.AddField(
            model_name='youtubesong',
            name='remote_playlist',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='songs', to='sync_youtube.remoteplaylist'),
        ),
    ]
