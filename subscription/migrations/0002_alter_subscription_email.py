# Generated by Django 5.1.6 on 2025-03-11 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='email',
            field=models.EmailField(default=1, max_length=254),
            preserve_default=False,
        ),
    ]
