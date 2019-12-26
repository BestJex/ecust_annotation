'''
@Author: your name
@Date: 2019-12-22 04:32:38
@LastEditTime : 2019-12-25 23:00:33
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

        #根据urls上的信息完善serializer.data
        data = self.enrich_serializer_data(many,request)

        #如果是Response类型，说明里面出错，抛出
        if isinstance(data,Response):
            return data

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #将url上的template信息注入到data中，同时检验数据的一致性
    #例如templateid为2的template为NER任务，则templateclass不应该为eventgroups
    def enrich_serializer_data(self,many,request):
        data = request.data if many == True else [request.data]
        template_id = self.kwargs['pk']
        template_class = self.kwargs['templateclass']

        for data_item in data:
            #首先验证template的type和templateclass是否对应
            try:
                template_type = Template.objects.get(pk=template_id).template_type
            except:
                content = {'type':'error','message':'there is no template with pk = {}'.format(template_id)}
                return Response(content,status=status.HTTP_400_BAD_REQUEST)

            #再验证template_type和templateclass是否能够对应
            if template_type not in TemplateClassTemplateTypeDic[template_class]:
                content = {'type':'error','message':'this assembly is not supported by the template'}
                return Response(content,status=status.HTTP_400_BAD_REQUEST)

            #如果验证没有问题，data_item中添加template信息
            data_item['template'] = template_id
        
        return data if many == True else data[0]
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
        #将实体组和事件组信息加入data中
        data = self.enrich_validated_data(many,request)
        
        serializer = self.serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #创建实体时，验证url上的templateclass和上传数据是否一致,例如templateclass是entitygroups,则数据中entity_group_template不能为空，且event_group_template应该为空
    def enrich_validated_data(self,many,request):
        data = request.data if many == True else [request.data]
        template_class = self.kwargs['templateclass']
        template_class_id = self.kwargs['templateclassid']

        event_group_template = template_class_id
        entity_group_template = None

        if template_class == 'entitygroups':
            event_group_template, entity_group_template = entity_group_template, event_group_template

        for data_item in data:
            #直接将数据加进去，不用验证是否存在，反正后面is_validated要再检验一次
            data_item['entity_group_template'] = entity_group_template
            data_item['event_group_template'] = event_group_template

        return data
                        


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

        #返回修正后的data，如果修正过程中发现错误，data是一个Responce实例，应返回
        data = self.enrich_validated_data(many,request)
        if isinstance(data,Response):
            return data

        serializer = self.serializer_class(data=data,many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    #校验关系两端的实体是不是属于关系模板，同时补充relation信息
    def enrich_validated_data(self,many,request):
        data = request.data if many == True else [request.data] 
        relation_id = self.kwargs['relationid']

        for data_item in data:
            start_entity_id = data_item['start_entity']
            end_entity_id = data_item['end_entity']
            #首先验证start_entity是否存在，并判断其所属模板类型是否为RE
            start_entity = self.get_entity_tempalte_by_id(start_entity_id)
            #如果404或实体所属模板不是RE返回异常
            if isinstance(start_entity,Response):
                return start_entity
            end_entity = self.get_entity_tempalte_by_id(end_entity_id)
            #如果404或实体所属模板不是RE返回异常
            if isinstance(end_entity,Response):
                return end_entity
            #如果验证没有问题，data加上relation属性
            data_item['relation'] = relation_id
            
        return data if many == True else data[0]
        
    #根据entity_template_id返回entity_template
    def get_entity_tempalte_by_id(self,id):
        try:
            entity = Entity_template.objects.get(pk=id)
            template_type = self.get_template_type_by_entity(entity)
            #如果实体所属模板不是RE，返回错误
            if template_type != 'RE':
                content = {'type':'error','message':'could not add a relation on entity with pk={}, which is not an entity of relation template'.format(id)}
                return Response(content,status=status.HTTP_400_BAD_REQUEST)  
            return entity 
        except:
            content = {'type':'error','message':'there is no entity_template with pk = {}'.format(id)}
            return Response(content,status=status.HTTP_400_BAD_REQUEST)        

    #输入一个entitytemplate实例，返回这个entity所属的template的type
    def get_template_type_by_entity(self,entity):
        if entity.event_group_template is None:
            return entity.entity_group_template.template.template_type
        return entity.event_group_template.template.template_type        