# Generated by Django 2.2.6 on 2021-06-18 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20210618_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(blank=True, unique=True, verbose_name='Адрес страницы'),
        ),
    ]
