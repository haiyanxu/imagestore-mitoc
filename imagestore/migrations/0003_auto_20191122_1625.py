# Generated by Django 2.1.14 on 2019-11-22 21:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('imagestore', '0002_album_brief'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='album',
            name='is_public',
        ),
        migrations.RemoveField(
            model_name='image',
            name='description',
        ),
        migrations.AddField(
            model_name='album',
            name='level',
            field=models.PositiveIntegerField(default=1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='album',
            name='lft',
            field=models.PositiveIntegerField(default=1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='album',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subalbums', to=settings.IMAGESTORE_ALBUM_MODEL, verbose_name='Parent Album'),
        ),
        migrations.AddField(
            model_name='album',
            name='rght',
            field=models.PositiveIntegerField(default=1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='album',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True, default=1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='album',
            name='tripreport',
            field=models.TextField(blank=True, null=True, verbose_name='Trip Report'),
        ),
        migrations.AddField(
            model_name='image',
            name='summary',
            field=models.TextField(blank=True, null=True, verbose_name='Summary'),
        ),
        migrations.AlterField(
            model_name='albumupload',
            name='zip_file',
            field=models.FileField(help_text='Select a .zip file of images to upload into a new Gallery.', upload_to='temp/', verbose_name='images file (.zip)'),
        ),
    ]