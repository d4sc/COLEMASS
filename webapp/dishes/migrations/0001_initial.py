# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-10 08:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hardware', '0001_initial'),
        ('chores', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=30, null=True)),
                ('tag', models.CharField(max_length=20, unique=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'dishes',
            },
        ),
        migrations.CreateModel(
            name='DishChore',
            fields=[
                ('chore_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='chores.Chore')),
                ('solved_time', models.DateTimeField(blank=True, null=True)),
                ('reply', models.TextField(blank=True, null=True)),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chores', to='dishes.Dish')),
                ('initiator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiated_dish_chores', to=settings.AUTH_USER_MODEL)),
                ('solver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solved_dish_chores', to=settings.AUTH_USER_MODEL)),
            ],
            bases=('chores.chore',),
        ),
        migrations.CreateModel(
            name='DishLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taken_time', models.DateTimeField()),
                ('returned_time', models.DateTimeField(blank=True, null=True)),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_log', to='dishes.Dish')),
                ('returned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='returned_dishes_log', to=settings.AUTH_USER_MODEL)),
                ('taken_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taken_dishes_log', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ItemTracker',
            fields=[
                ('hardware_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='hardware.Hardware')),
            ],
            bases=('hardware.hardware',),
        ),
        migrations.CreateModel(
            name='UnregisteredDish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=30, null=True)),
                ('tag', models.CharField(max_length=20, unique=True)),
                ('detectionTime', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name_plural': 'unregistered dishes',
            },
        ),
    ]
