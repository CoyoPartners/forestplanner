# Generated by Django 2.1.7 on 2019-04-23 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discovery', '0007_auto_20190423_1048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standlistentry',
            name='size_class',
            field=models.CharField(max_length=255),
        ),
    ]
