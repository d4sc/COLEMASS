# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-09 10:54
from __future__ import unicode_literals

import chores.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('assigned_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('nudges', models.SmallIntegerField(default=0)),
                ('last_nudge', models.DateTimeField(default=chores.models.a_long_time_ago)),
                ('active', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['nudges', '-assigned_time'],
            },
        ),
        migrations.CreateModel(
            name='CompletedChore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('nudges', models.SmallIntegerField()),
                ('confirmed', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Infraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='RefusedChore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('reason', models.CharField(max_length=140)),
                ('confirmed', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='RecurringChore',
            fields=[
                ('chore_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='chores.Chore')),
                ('round_robin', models.CharField(default=chores.models.random_order, max_length=50)),
            ],
            bases=('chores.chore',),
        ),
        migrations.AddField(
            model_name='refusedchore',
            name='chore',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chores.Chore'),
        ),
        migrations.AddField(
            model_name='refusedchore',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='infraction',
            name='chore',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chores.Chore'),
        ),
        migrations.AddField(
            model_name='infraction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='completedchore',
            name='chore',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chores.Chore'),
        ),
        migrations.AddField(
            model_name='completedchore',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chore',
            name='assignee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
