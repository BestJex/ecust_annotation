'''
@Author: meloming
@Date: 2019-12-22 04:19:00
<<<<<<< HEAD
@LastEditTime: 2020-03-04 21:03:18
@LastEditors: Please set LastEditors
=======
@LastEditTime : 2020-01-03 02:16:36
@LastEditors  : Please set LastEditors
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
@Description: Serilizers
@FilePath: /ecust_annotation/api/serializer.py
'''
from rest_framework import serializers
from api.models import *
from api import dao


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
        fields = ['id','content','project']

'''
@description: 字典表的serializer
@param {type} 
@return: 
'''
class DicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dic
        fields = ['id','project','content','create_date','content','entity_template']


'''
@description: 动态serializer的fields，继承该类的serializer可以在实例化时输入fields参数
@param {type} 用于动态显示fields
@return: 
'''
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

'''
@description: 查询epoch信息，包括该epoch的annotator进度和reviewer进度
@param {type} 动态变化，用于三个地方：project查看epoch信息；标注者查看epoch信息；审核者查看epoch
@return: 因此要求是需要动态决定fields
'''
class EpochSerializer(DynamicFieldsModelSerializer):
    annotate_progress = serializers.SerializerMethodField()
    review_progress = serializers.SerializerMethodField()

    class Meta:
        model = Epoch
        fields = ['id','num','state','re_annotate_num','annotator','reviewer','project','annotate_progress','review_progress']

    #obj是需要serialize的epoch对象，这里获得这个epoch该标注者的标注进度
    def get_annotate_progress(self,obj):
        data = {}
        #查询这个epoch下的ann_allocation对象
        ann_allocations = dao.get_ann_allocation_by_epoch(obj)
        data['total_num'] = len(ann_allocations)
        data['undo_num'] = len(ann_allocations.filter(state='UNDO'))
        data['re_annotating_num'] = len(ann_allocations.filter(state='RE_ANNOTATING'))
        data['waiting_num'] = len(ann_allocations.filter(state='WAITING'))
        data['finish_num'] = len(ann_allocations.filter(state='FINISH'))
        return data

    #obj是需要serialize的epoch对象，这里获得这个epoch的review进度
    def get_review_progress(self,obj):
        data = {}
        #查询这个epoch下的review_allocation对象
        review_allocations = dao.get_review_allocation_by_epoch(obj)
        data['total_num'] = len(review_allocations)
        data['undo_num'] = len(review_allocations.filter(state='UNDO'))
        data['finish_num'] = len(review_allocations.filter(state='FINISH'))
        return data

'''
@description: 实体标注的serializer
@param {type} 
@return: 
'''
class EntityAnnotationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Entity_annotation
        fields = ['id','doc','start_offset','end_offset','content','entity_template','user','role','event_group_annotation']

'''
@description: 关系标注的serializer，Relation这个
@param {type} 
@return: 
'''       
class RelationAnnotationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Relation_annotation
        fields = ['id','doc','user','role','relation_entity_template','start_entity','end_entity']

'''
@description: 事件标注的serializer
@param {type} 
@return: 
'''
class EventAnnotationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Event_group_annotation
        fields = ['id','doc','user','role','event_group_template']

'''
@description: 分类标注的serializer
@param {type} 
@return: 
'''
class ClassificationAnnotationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Classification_annotation
        fields = ['id','doc','user','role','classification_template']