# Generated by Django 4.2.1 on 2023-05-10 13:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_phonenumber'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='phonenumber',
            name='confirmed',
        ),
        migrations.RemoveField(
            model_name='phonenumber',
            name='name',
        ),
        migrations.RemoveField(
            model_name='phonenumber',
            name='user',
        ),
    ]
