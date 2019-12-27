# Generated by Django 2.2.5 on 2019-12-27 02:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ann_Model',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('api', models.URLField()),
                ('args', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Entity_annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_offset', models.IntegerField()),
                ('end_offset', models.IntegerField()),
                ('content', models.CharField(max_length=100)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_annotation', to='api.Doc')),
            ],
        ),
        migrations.CreateModel(
            name='Entity_group_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Entity_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('color', models.CharField(max_length=7)),
                ('entity_group_template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_template', to='api.Entity_group_template')),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('template_type', models.CharField(choices=[('NER', 'ner'), ('RE', 're'), ('EVENT', 'event'), ('CLASSIFICATION', 'classification')], max_length=15)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('in_use', models.IntegerField(default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('AMDIN', 'ADMIN'), ('ANNOTATOR', 'ANNOTATOR'), ('REVIEWER', 'REVIEWER')], max_length=15)),
                ('user', models.ManyToManyField(related_name='role', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Relation_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relation_template', to='api.Template')),
            ],
            options={
                'unique_together': {('name', 'template')},
            },
        ),
        migrations.CreateModel(
            name='Relation_entity_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('end_entity', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='end_entity_relation_entity_template', to='api.Entity_template')),
                ('relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='relation_entity_template', to='api.Relation_template')),
                ('start_entity', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='start_entity_relation_entity_template', to='api.Entity_template')),
            ],
            options={
                'unique_together': {('relation', 'start_entity', 'end_entity')},
            },
        ),
        migrations.CreateModel(
            name='Relation_annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relation_annotation', to='api.Doc')),
                ('end_entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='end_entity_relation_annotation', to='api.Entity_annotation')),
                ('relation_annotation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.Relation_entity_template')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='relation_annotation', to='api.Role')),
                ('start_entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='start_entity_relation_annotation', to='api.Entity_annotation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='relation_annotation', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('project_type', models.CharField(choices=[('ACTIVE_LEARNING', 'active_learning'), ('NON_ACTIVE_LEARNING', 'non_acitve_learning'), ('MINE', 'mine')], max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('in_use', models.IntegerField(default=0, null=True)),
                ('ann_num_per_epoch', models.IntegerField(null=True)),
                ('ann_model', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='project', to='api.Ann_Model')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='project', to='api.Template')),
            ],
        ),
        migrations.CreateModel(
            name='Event_group_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_group_template', to='api.Template')),
            ],
            options={
                'unique_together': {('name', 'template')},
            },
        ),
        migrations.CreateModel(
            name='Event_group_annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_group_anontation', to='api.Doc')),
                ('event_group_template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='event_group_annotation', to='api.Event_group_template')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='event_group_anontation', to='api.Role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='event_group_anontation', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Epoch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField()),
                ('state', models.CharField(choices=[('UNDO', 'UNDO'), ('ANNOTATING', 'ANNOTATING'), ('RE_ANNOTATING', 'RE_ANNOTAITNG'), ('REVIEWING', 'REVIEWING'), ('WAITING', 'WAITING'), ('FINISH', 'FINISH')], default='UNDO', max_length=15)),
                ('re_annotate_num', models.IntegerField()),
                ('annotator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='annotator_epoch', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='epoch', to='api.Project')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reviewer_epoch', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('num', 'project')},
            },
        ),
        migrations.AddField(
            model_name='entity_template',
            name='event_group_template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='entity_template', to='api.Event_group_template'),
        ),
        migrations.AddField(
            model_name='entity_group_template',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_group_template', to='api.Template'),
        ),
        migrations.AddField(
            model_name='entity_annotation',
            name='entity_template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_annotation', to='api.Entity_template'),
        ),
        migrations.AddField(
            model_name='entity_annotation',
            name='event_group_annotation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_annotation', to='api.Event_group_annotation'),
        ),
        migrations.AddField(
            model_name='entity_annotation',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_annotation', to='api.Role'),
        ),
        migrations.AddField(
            model_name='entity_annotation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_annotation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doc',
            name='epoch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='doc', to='api.Epoch'),
        ),
        migrations.AddField(
            model_name='doc',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doc', to='api.Project'),
        ),
        migrations.CreateModel(
            name='Dic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('content', models.CharField(max_length=100)),
                ('entity_template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dic', to='api.Entity_template')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dic', to='api.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Classification_template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=7)),
                ('name', models.CharField(max_length=20)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classification_template', to='api.Template')),
            ],
            options={
                'unique_together': {('name', 'template')},
            },
        ),
        migrations.CreateModel(
            name='Classification_annotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('classification_template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classification_annotation', to='api.Classification_template')),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classification_annotation', to='api.Doc')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classification_annotation', to='api.Role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='classification_annotation', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Review_allocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('UNDO', 'UNDO'), ('FINISH', 'FINISH')], default='UNDO', max_length=15)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_allocation', to='api.Doc')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='review_allocation', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('doc', 'reviewer')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='entity_template',
            unique_together={('name', 'entity_group_template', 'event_group_template')},
        ),
        migrations.AlterUniqueTogether(
            name='entity_group_template',
            unique_together={('name', 'template')},
        ),
        migrations.CreateModel(
            name='Annotate_allocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('UNDO', 'UNDO'), ('RE_ANNOTATING', 'RE_ANNOTATING'), ('WATING', 'WAITING'), ('FINISH', 'FINISH')], default='UNDO', max_length=15)),
                ('annotator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='annotate_allocation', to=settings.AUTH_USER_MODEL)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotate_allocation', to='api.Doc')),
            ],
            options={
                'unique_together': {('doc', 'annotator')},
            },
        ),
    ]
