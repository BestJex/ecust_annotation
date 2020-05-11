# Generated by Django 2.2.5 on 2020-04-22 01:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_remove_classification_annotation_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Standard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('standard_name', models.CharField(max_length=20, unique=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('entity_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='standard', to='api.Entity_template')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='standard', to='api.Project')),
            ],
        ),
        migrations.AddField(
            model_name='entity_annotation',
            name='standard',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_annotation', to='api.Standard'),
        ),
    ]
