'''
@Author: meloming
@Date: 2019-12-22 04:19:00
@LastEditTime : 2019-12-27 01:12:21
@LastEditors  : Please set LastEditors
@Description: Serilizers
@FilePath: /ecust_annotation/api/serializer.py
'''
from rest_framework import serializers
from api.models import *


'''
@description: 用户角色的serializer
@param {type} 
@return: 返回用户的所有角色名称
'''
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['name']

'''
@description: 模板的serializer
@param {type} 
@return: 模板的基本信息
'''
class TemplateSerializer(serializers.HyperlinkedModelSerializer):
    #查询模板信息时，返回查询每个模板详细信息的hyperlink
    url = serializers.HyperlinkedIdentityField(view_name='api:template-detail',read_only=True)

    class Meta:
        model = Template
        fields = ['id','name','template_type','create_date','url']

'''
@description: 模板详情的serializer
@param {type} 
@return: 模板的详细信息
'''
class TemplateDeatilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id','name','template_type','create_date','in_use']

'''
@description: 实体组的Serializer
@param {type} 
@return: 实体组的信息
'''
class EntityGroupTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity_group_template
        fields = ['id','name','create_date','template']

'''
@description: 事件元组的serializer
@param {type} 
@return: 
'''
class EventGroupTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event_group_template
        fields = ['id','name','create_date','template']


'''
@description: 关系的serializer
@param {type} 
@return: 
'''
class RelationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation_template
        fields = ['id','name','create_date','template']

'''
@description: 分类标签的serializer
@param {type} 
@return: 
'''
class ClassificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classification_template
        fields = ['id','name','color','create_date','template']

'''
@description: 实体模板的serializer
@param {type} 
@return: 
'''
class EntityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity_template
        fields = ['id','name','color','create_date','entity_group_template','event_group_template']

'''
@description: 实体关系模板的serializer
@param {type} 
@return: 
'''
class RelationEntityTemplatelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation_entity_template
        fields = ['id','relation','start_entity','end_entity']

'''
@description: Project的serializer
@param {type} 
@return: 
'''
class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api:project-detail',lookup_field='id',lookup_url_kwarg='projectid')
    template = serializers.HyperlinkedRelatedField(view_name='api:template-detail',lookup_field='pk',lookup_url_kwarg='pk',queryset=Template.objects.all())
    class Meta:
        model = Project
        fields = ['id','name','project_type','template','ann_model','ann_num_per_epoch','url']

'''
@description: 任务详情的serializer，查看某一任务详情，以及更新某一任务in_use时使用
@param {type} 
@return: 
'''
class PorjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id','name','project_type','template','ann_model','ann_num_per_epoch','in_use']

'''
@description: 文本表的Serializer
@param {type} 
@return: 
'''
class DocSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doc
        fields = ['id','content','epoch','project']

class DicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dic
        fields = ['id','project','content','create_date','content','entity_template']