# Generated by Django 2.2.5 on 2020-05-09 01:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20200509_0112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dic',
            name='standard',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dic', to='api.Standard'),
        ),
    ]
