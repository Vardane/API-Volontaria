# Generated by Django 2.2.12 on 2021-03-31 01:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_auto_20210328_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apitoken',
            name='purpose',
            field=models.CharField(max_length=200, verbose_name='Purpose'),
        ),
    ]
