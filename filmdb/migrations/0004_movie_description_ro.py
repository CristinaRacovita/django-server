# Generated by Django 3.1.7 on 2021-04-17 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('filmdb', '0003_auto_20210417_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='description_ro',
            field=models.CharField(max_length=1000, null=True),
        ),
    ]