'''
@Author: your name
@Date: 2019-12-22 04:32:38
@LastEditTime : 2019-12-25 03:02:13
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/views.py
'''
from django.shortcuts import render
from rest_framework import generics
from api.models import Template
from api.serializer import *
from rest_framework import status
from rest_framework.response import Response

'''
@description: 模板类型对应Serializer字典
@param {type} 
@return: 
'''
TemplateClassSerializerDic = {}
TemplateClassSerializerDic['entitygroups'] = EntityGroupTemplateSerializer
TemplateClassSerializerDic['relations'] = RelationTemplateSerializer
TemplateClassSerializerDic['eventgroups'] = EventGroupTemplateSerializer
TemplateClassSerializerDic['classifications'] = ClassificationTemplateSerializer

'''
@description: 模板类型对应Model字典
@param {type} 
@return: 
'''
TemplateClassModelDic = {}
TemplateClassModelDic['entitygroups'] = Entity_group_template
TemplateClassModelDic['eventgroups'] = Event_group_template
TemplateClassModelDic['relations'] = Relation_template
TemplateClassModelDic['classifications'] = Classification_template

'''
@description: templateclass对应templatetype的字典
@param {type} 
@return: 
'''
TemplateClassTemplateTypeDic = {}
TemplateClassTemplateTypeDic['entitygroups'] = ['NER','RE']
TemplateClassTemplateTypeDic['eventgroups'] = ['EVENT']
TemplateClassTemplateTypeDic['relations'] = ['RE']
TemplateClassTemplateTypeDic['classifications'] = ['CLASSIFICATION']


'''
@description: 模板的搜索和新建
@param {type} 
@return: 
    GET方法搜索所有模板，返回模板信息
    POST方法创建一个新的模板信息，并返回创建的模板信息
'''
# Create your views here.
class TemplateList(generics.ListCreateAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

'''
@description: 查询模板详情
@param {type} 
@return: 返回模板详细信息
'''
class TemplateDetail(generics.RetrieveAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateDeatilSerializer



'''
@description:  对模板内部的组件进行创建和查询，包括实体组、关系、事件组和分类标签
@param {type} 
@return: 返回查询信息或创建的模板内部组件（代码命名中为template_class）
'''
class TemplateClassList(generics.ListCreateAPIView):
    #返回对应组件的serializer
    def get_serializer_class(self):
        #根据url上的templateclass确定是template中的哪一个组件，包括entitygroups,eventgroups,relation,classfication
        template_class = self.kwargs['templateclass']
        return TemplateClassSerializerDic[template_class]

    def get_model(self):
        #根据url上的templateclass确定是template中的哪一个组件，包括entitygroups,eventgroups,relation,classfication
        template_class = self.kwargs['templateclass']
        return TemplateClassModelDic[template_class]
    
    def get_queryset(self):
        #获得template的id
        template_id = self.kwargs['pk']

        #获得template_class的model
        model = self.get_model()

        #根据template的id查询该template对应的entity_group_template
        queryset = model.objects.filter(template__id=template_id)
        return queryset

    #由于perform_create执行时已经获取了serializer，这里重写create方法
    def create(self,request, *args, **kwargs):
        #根据上传的data是否为list决定实例化serializer是many是否为True
        many = isinstance(self.request.data,list)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)

        #验证类型的一致性,如果一致性不正确，返回错误信息
        if not self.validate_data_type(many,serializer):
            content = {'type':'error','message':'this assembly is not supported by the template'}
            return Response(content,status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #对于上传的数据类型一致性做验证，比如创建classification标签，对应的template的类型一定要是CLASSIFICATION
    def validate_data_type(self,many,serializer):
        #由于再serializer执行save()方法之前，不能直接访问serializer.data,因此访问serializer的validated_data
        data = serializer.validated_data if many == True else [serializer.validated_data]
        template_class = self.kwargs['templateclass']
        
        for data_item in data:
            #且validated_data会直接把外键链接的field直接变成template对象
            template_type = data_item['template'].template_type
            #如果存在某一个模板类型和template_class不对应，返回false；例如给一个NERtemplate创建CLASSIFICATION标签
            if template_type not in  TemplateClassTemplateTypeDic[template_class]:
                return False
        return True
                
'''
@description: 根据实体组或事件组创建实体
@param {type} 
@return: 
'''         
class EntityTemplateList(generics.ListCreateAPIView):
    serializer_class = EntityTemplateSerializer

    def get_queryset(self):
        #获得templateclass的id（事件组或者实体组的id）
        template_class_id = self.kwargs['templateclassid']
        templat_class = self.kwargs['templateclass']

        #根据事件组或者实体组的id查询下面对应的实体
        if templat_class == 'entitygroups':
            queryset = Entity_template.objects.filter(entity_group_template__id=template_class_id)
        else:
            queryset = Entity_template.objects.filter(event_group_template__id=template_class_id)
        return queryset

    #创建实体组或者事件组下的实体
    def create(self,request, *args, **kwargs):
        #根据上传的data是否为list决定实例化serializer是many是否为True
        many = isinstance(self.request.data,list)
        serializer = self.serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)

        if not self.validated_data_consistency(many,serializer):
            content = {'type':'error','message':'the group in url and data is not consistent!'}
            return Response(content,status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #创建实体时，验证url上的templateclass和上传数据是否一致,例如templateclass是entitygroups,则数据中entity_group_template不能为空，且event_group_template应该为空
    def validated_data_consistency(self,many,serializer):
        data = serializer.validated_data if many == True else [serializer.validated_data]
        template_class = self.kwargs['templateclass']

        for data_item in data:
            if template_class == 'entitygroups' and data_item['entity_group_template'] is not None and data_item['event_group_template'] is None:
                continue
            if template_class == 'eventgroups' and data_item['event_group_template'] is not None and data_item['entity_group_template'] is None:
                continue
            return False
        return True

'''
@description: 建立实体和关系之间的联系，此时实体和关系已经全部建立完成
@param {type} 
@return: 
'''
class RelationEntityList(generics.ListCreateAPIView):
    serializer_class = RelationEntityTemplatelSerializer
    
    #根据relation查询relation_entity中的所有记录，返回
    def get_queryset(self):
        #获取relation的id
        relation_id = self.kwargs['relationid']

        return Relation_entity_template.objects.filter(relation__id = relation_id)

    #创建某关系下的所有实体模板对
    def create(self,request, *args, **kwargs):
        #根据上传的data是否为list决定实例化serializer是many是否为True
        many = isinstance(self.request.data,list)
        serializer = self.serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)

        #检验关系两边实体所属的template是否为RE任务
        if not self.validate_data_type(many,serializer):
            content = {'type':'error','message':'this assembly is not supported by the template'}
            return Response(content,status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def validate_data_type(many,serializer):
        data = serializer.validated_data if many == True else [serializer.validated_data]

        for data_item in data:
            start_entity_template_type = self.get_template_type_by_entity(data_item['start_entity'])
            end_entity_template_type = self.get_template_type_by_entity(data_item['end_entity'])
            template_type = data_item['relation'].template.template_type

            if not (start_entity_template_type == template_type and end_entity_template_type == template_type):
                return False
        return True                

    #输入一个entitytemplate实例，返回这个entity所属的template的type
    def get_template_type_by_entity(entity):
        if entity.event_group_template is None:
            return entity.entity_group_template.template.template_type
        return entity.event_group_template.template.template_type        