# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-29 16:38
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projectroles', '0006_add_remote_projects'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JSONCacheItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_name', models.CharField(help_text='App name', max_length=255)),
                ('name', models.CharField(help_text='Name or title of the item given by the data setting app', max_length=255)),
                ('date_modified', models.DateTimeField(auto_now_add=True, help_text='DateTime of the update')),
                ('sodar_uuid', models.UUIDField(default=uuid.uuid4, help_text='Item SODAR UUID', unique=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='Cached data as JSON')),
                ('project', models.ForeignKey(blank=True, help_text='Project in which the item belongs (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cached_items', to='projectroles.Project')),
                ('user', models.ForeignKey(help_text='User who updated the item', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='jsoncacheitem',
            unique_together=set([('project', 'app_name', 'name')]),
        ),
    ]