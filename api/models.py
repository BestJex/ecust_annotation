from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Template(models.Model):
    NER = 'NER'
    RE = 'RE'
    EVENT = 'EVENT'
    CLASSIFICATION = 'CLASSIFICATION'

    TYPE_CHOICES = (
        (NER,'ner'),
        (RE,'re'),
        (EVENT,'event'),
        (CLASSIFICATION,'classification')
    )

    name = models.CharField(max_length=20,unique=True)
    template_type = models.CharField(max_length=15,choices=TYPE_CHOICES)
    create_date = models.DateTimeField(auto_now_add=True)

class Classification_template(models.Model):
    color = models.CharField(max_length=7)
    name = models.CharField(max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(Template,related_name='classification_template',on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'template']

class Entity_group_template(models.Model):
    name = models.CharField(max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(Template,related_name='entity_group_template',on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'template']

class Event_group_template(models.Model):
    name = models.CharField(max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(Template,related_name='event_group_template',on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'template']

class Entity_template(models.Model):
    name = models.CharField(max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=7)
    entity_group_template = models.ForeignKey(Entity_group_template,related_name='entity_template',on_delete=models.CASCADE,null=True)
    event_group_template = models.ForeignKey(Event_group_template,related_name='entity_template',on_delete=models.CASCADE,null=True)

    class Meta:
        unique_together = ['name', 'entity_group_template','event_group_template']

class Relation_template(models.Model):
    name = models.CharField(max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(Template,related_name='relation_template',on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'template']

class Relation_entity_template(models.Model):
    relation = models.ForeignKey(Relation_template,related_name='relation_entity_template',on_delete=models.CASCADE,null=True)
    start_entity = models.ForeignKey(Entity_template,related_name='start_entity_relation_entity_template',on_delete=models.CASCADE,null=True)
    end_entity = models.ForeignKey(Entity_template,related_name='end_entity_relation_entity_template',on_delete=models.CASCADE,null=True)
    
    class Meta:
        unique_together = ['relation', 'start_entity', 'end_entity']

class Ann_Model(models.Model):
    name = models.CharField(max_length=20,unique=True)
    api = models.URLField()
    args = models.TextField()

class Project(models.Model):
    ACTIVE_LAERNING = 'ACTIVE_LEARNING'
    NON_ACTIVE_LEARNING = 'NON_ACTIVE_LEARNING'
    MINE = 'MINE'

    PROJECT_TYPE_CHOICES = (
        (ACTIVE_LAERNING,'active_learning'),
        (NON_ACTIVE_LEARNING,'non_acitve_learning'),
        (MINE,'mine')
    )

    name = models.CharField(max_length=20,unique=True)
    project_type = models.CharField(choices=PROJECT_TYPE_CHOICES,max_length=20)
    create_date = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(Template,related_name='project',on_delete=models.CASCADE)
    ann_model = models.ForeignKey(Ann_Model,related_name='project',on_delete=models.CASCADE)

class Epoch(models.Model):
    UNDO = 'UNDO'
    ANNOTATING = 'ANNOTATING'
    RE_ANNOTATING = 'RE_ANNOTATING'
    REVIEWING = 'REVIEWING'
    WAITING = 'WAITING'
    FINISH = 'FINISH'

    STATE_CHOICES = (
        (UNDO,'UNDO'),
        (ANNOTATING,'ANNOTATING'),
        (RE_ANNOTATING,'RE_ANNOTAITNG'),
        (REVIEWING,'REVIEWING'),
        (WAITING,'WAITING'),
        (FINISH,'FINISH')
    )

    num = models.IntegerField()
    state = models.CharField(max_length=15,choices=STATE_CHOICES,default='UNDO')
    re_annotate_num = models.IntegerField()
    annotator = models.ForeignKey(User,related_name='annotator_epoch',on_delete='models.CASECADE')
    reviewer =  models.ForeignKey(User,related_name='reviewer_epoch',on_delete='models.CASECADE')
    project = models.ForeignKey(Project,related_name='epoch',on_delete='models.CASECADE')

    class Meta:
        unique_together = ['num', 'project']

class Doc(models.Model):
    content = models.TextField()
    epoch = models.ForeignKey(Epoch, related_name='doc', on_delete=models.CASCADE,null=True)

class Dic(models.Model):
    project = models.ForeignKey(Project,related_name='dic',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=100)
    entity_template = models.ForeignKey(Entity_template,related_name='dic',on_delete=models.CASCADE)

class Annotate_allocation(models.Model):
    UNDO = 'UNDO'
    RE_ANNOTATING = 'RE_ANNOTATING'
    WAITING = 'WATING'
    FINISH = 'FINISH'

    STATE_CHOICES = (
        (UNDO,'UNDO'),
        (RE_ANNOTATING,'RE_ANNOTATING'),
        (WAITING,'WAITING'),
        (FINISH,'FINISH')
    )

    doc = models.ForeignKey(Doc,related_name='annotate_allocation',on_delete=models.CASCADE)
    annotator = models.ForeignKey(User,related_name='annotate_allocation',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=15,choices=STATE_CHOICES,default='UNDO')

    class Meta:
        unique_together = ['doc', 'annotator']
    
class Review_allocation(models.Model):
    UNDO = 'UNDO'
    FINISH = 'FINISH'

    STATE_CHOICES = (
        (UNDO,'UNDO'),
        (FINISH,'FINISH')
    )

    doc = models.ForeignKey(Doc,related_name='review_allocation',on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User,related_name='review_allocation',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=15,choices=STATE_CHOICES,default='UNDO')

    class Meta:
        unique_together = ['doc', 'reviewer']
    
class Role(models.Model):
    ADMIN = 'AMDIN'
    ANNOTATOR = 'ANNOTATOR'
    REVIEWER = 'REVIEWER'

    NAME_CHOICES = (
        (ADMIN,'ADMIN'),
        (ANNOTATOR,'ANNOTATOR'),
        (REVIEWER,'REVIEWER')
    )

    name = models.CharField(max_length=15,choices=NAME_CHOICES)
    user = models.ManyToManyField(User,related_name='role')


class Classification_annotation(models.Model):
    doc = models.ForeignKey(Doc,related_name='classification_annotation',on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name='classification_annotation',on_delete=models.CASCADE)
    role = models.ForeignKey(Role,related_name='classification_annotation',on_delete=models.CASCADE)
    classification_template = models.ForeignKey(Classification_template,related_name='classification_annotation',on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    create_date = models.DateTimeField(auto_now_add=True)


class Event_group_annotation(models.Model):
    event_group_template = models.ForeignKey(Event_group_template,related_name='event_group_annotation',on_delete=models.CASCADE)
    doc = models.ForeignKey(Doc,related_name='event_group_anontation',on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name='event_group_anontation',on_delete=models.CASCADE)
    role = models.ForeignKey(Role,related_name='event_group_anontation',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

class Entity_annotation(models.Model):
    doc = models.ForeignKey(Doc,related_name='entity_annotation',on_delete=models.CASCADE)
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()
    content = models.CharField(max_length=100)
    entity_template = models.ForeignKey(Entity_template,related_name='entity_annotation',on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name='entity_annotation',on_delete=models.CASCADE)
    role = models.ForeignKey(Role,related_name='entity_annotation',on_delete=models.CASCADE)
    event_group_annotation = models.ForeignKey(Event_group_annotation,related_name='entity_annotation',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

class Relation_annotation(models.Model):
    doc = models.ForeignKey(Doc,related_name='relation_annotation',on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name='relation_annotation',on_delete=models.CASCADE)
    role = models.ForeignKey(Role,related_name='relation_annotation',on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    relation_entity_template = models.ForeignKey(Relation_entity_template,name='relation_annotation',on_delete=models.CASCADE)
    start_entity = models.ForeignKey(Entity_annotation,related_name='start_entity_relation_annotation',on_delete=models.CASCADE)
    end_entity = models.ForeignKey(Entity_annotation,related_name='end_entity_relation_annotation',on_delete=models.CASCADE)
    