'''
@Author: your name
@Date: 2019-12-22 04:32:38
@LastEditTime: 2020-05-10 06:50:32
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/views.py
'''
from django.shortcuts import render
from rest_framework import generics
from api.models import Template
from api.serializer import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from api import utils
from django.db import transaction
from django.shortcuts import get_object_or_404
from api import dao
from django.views.decorators.csrf import csrf_exempt

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
    #只筛选in_use=1的template
    queryset = Template.objects.filter(in_use=1)
    serializer_class = TemplateSerializer


'''
@description: 查询模板详情,更新模板的in_use
@param {type} 
@return: 返回模板详细信息
'''
class TemplateDetail(generics.RetrieveUpdateDestroyAPIView):
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
                return utils.return_Response('errors','there is no template with pk = {}'.format(template_id),status.HTTP_400_BAD_REQUEST)

            #再验证template_type和templateclass是否能够对应
            if template_type not in TemplateClassTemplateTypeDic[template_class]:
                return utils.return_Response('errors','this assembly is not supported by the template',status.HTTP_400_BAD_REQUEST)

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
                return utils.return_Response('errors','could not add a relation on entity with pk={}, \
                                            which is not an entity of relation template'.format(id), \
                                            status.HTTP_400_BAD_REQUEST)
            return entity 
        except:
            return utils.return_Response('errors','there is no entity_template with pk = {}'.format(id),status.HTTP_400_BAD_REQUEST)      

    #输入一个entitytemplate实例，返回这个entity所属的template的type
    def get_template_type_by_entity(self,entity):
        if entity.event_group_template is None:
            return entity.entity_group_template.template.template_type
        return entity.event_group_template.template.template_type        


'''
@description: 任务的总览接口
@param {type} 
@return: 
'''
class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.filter(in_use=1)
    serializer_class = ProjectSerializer


'''
@description: 查询任务详情，更新某一任务的in_use
@param {type} 
@return: 
'''
class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = PorjectDetailSerializer
    lookup_url_kwarg = 'projectid'


'''
@description: 负责上传文本，且更新ann_num_per_epoch信息
@param {type} 
@return: 
'''
class ProjectDoc(APIView):
    def post(self,request,*args, **kwargs):
        project_id = self.kwargs['projectid']
        #查看project是否存在
        try:
            project = Project.objects.get(pk=project_id)
        except:
            return utils.return_Response('errors','project not found',status.HTTP_404_NOT_FOUND)

        
        #验证文件格式的准确性，令ann_num_per_epoch等于文件长度，变成1个epoch
        docs = utils.validate_files(request.FILES)
        ann_num_per_epoch = len(docs)

        if isinstance(docs,Response):
            return docs
        
        #如果没有问题，serialize docs
        serialize_doc_data = utils.serialize_doc(docs,project_id)
        serializer = DocSerializer(data=serialize_doc_data,many=True)
        print(serializer.is_valid())
        
        try:
            #加一个事务，doc表和project保持原子性
            with transaction.atomic():
                serializer.save()
                #同时更新project的ann_num_per_epoch
                project.ann_num_per_epoch = ann_num_per_epoch
                project.save()
        except Exception as e:
            return Response(str(e),status=status.HTTP_400_BAD_REQUEST)
        return utils.return_Response('message','create successfully!',status.HTTP_201_CREATED)
        
'''
@description: 负责上传字典信息，不符合规范的会报错
@param {type} 
@return: 
'''       
class ProjectDic(APIView):
    #手动方式和文件方式上传字典
    def post(self,request,*args, **kwargs):
        upload_type = self.request.data['type']
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project, pk=project_id)

        #对于上传的dic文件做验证，如果成功返回serialize好的data，如果出错返回Respone类型
        if upload_type == 'file':
            serialized_dic_data = utils.validate_dic(request.FILES,project)
            if isinstance(serialized_dic_data,Response):
                return serialized_dic_data

        elif upload_type == 'manual':
            data = self.request.data['data']
            content, entity_template_id, standard_id = data.split(',')
            entity_template_id = int(entity_template_id)
            standard_id = int(standard_id)
            serialized_dic_data = {'content':content, 'project':project_id, 'entity_template':entity_template_id, 'standard':standard_id}
            print(serialized_dic_data)
            if isinstance(serialized_dic_data,Response):
                return serialized_dic_data
        else:
            return utils.return_Response('errro', 'invalid upload type', status.HTTP_400_BAD_REQUEST)
            
        serialized_dic_data = [serialized_dic_data] if isinstance(serialized_dic_data, dict) else serialized_dic_data
        serializer = DicSerializer(data=serialized_dic_data,many=True)
        if serializer.is_valid():
            serializer.save()
        else:
            return utils.return_Response('error','invalid data!',status.HTTP_400_BAD_REQUEST)

        return Response(serialized_dic_data, status.HTTP_201_CREATED)

    #返回该任务所属字典下有那些entity_template
    def get(self,request,*args, **kwargs):
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project, pk=project_id)

        entity_template_queryset = dao.get_project_dic_entity_template(project)
        serialized_entity_template_data = EntityTemplateSerializer(entity_template_queryset,many=True).data
        
        return Response(serialized_entity_template_data, status.HTTP_200_OK)

'''
@description: 上传正则，查询正则
@param {type} 
@return: 
'''  
class ProjectRe(APIView):
    #通过文件和手动方式上传正则
    def post(self,request,*args, **kwargs):
        upload_type = self.request.data['type']
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project, pk=project_id)

        if upload_type == 'file':
            serialize_re_data = utils.validate_re(request.FILES, project)
            if isinstance(serialize_re_data,Response):
                return serialize_re_data
        elif upload_type == 'manual':
            content = self.request.data['content']
            entity_template_id_list = self.request.data['entity_template_id_list'].split(',')
            entity_template_id_list = [int(x) for x in entity_template_id_list]
            #验证括号长度
            bracket_number = utils.validate_bracket_number(content)
            if not((bracket_number == len(entity_template_id_list)) or (bracket_number == 0 and len(entity_template_id_list) == 1)):
                print(bracket_number, len(entity_template_id_list))
                return utils.return_Response('error','the number of bracket is not equal to the number of entity_template',status.HTTP_404_NOT_FOUND)

            serialize_re_data = [{'content':content, 'project':project_id, 'entity_template_list':entity_template_id_list}]
        else:
            return utils.Response('error', 'not valid upload type', status.HTTP_400_BAD_REQUEST)

        save_result = utils.save_re_and_entity_template(serialize_re_data)

        if isinstance(save_result, Response):
            return save_result

        return Response(save_result, status.HTTP_201_CREATED)

    #查询某任务下某实体类型下的正则表达式
    def get(self,request,*args, **kwargs):
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project, pk=project_id)
        re_queryset = dao.get_re_by_project(project)
        serialize = ReEntityTemplateSerializer(re_queryset, many=True)

        #手动和并每个正则
        return_data = {}
        print(serialize.data)
        for item in serialize.data:
            re_id = item['re']
            entity_template_id = item['entity_template']
            re_obj = get_object_or_404(Re, pk=re_id)
            entity_template_obj = get_object_or_404(Entity_template, pk=entity_template_id)
            re_data = ReSerializer(re_obj).data
            entity_template_data = EntityTemplateSerializer(entity_template_obj).data
            if re_id not in return_data:
                
                return_data[re_id] = {'re':re_data}
                return_data[re_id]['entity_template_list'] = [entity_template_data]
            else:
                return_data[re_id]['entity_template_list'].append(entity_template_data)

        return Response(list(return_data.values()), status.HTTP_200_OK)
        
'''
@description: 某条文本的正则匹配，每次匹配一种正则
@param {type} 
@return: 
''' 
class ProjectReMatch(APIView):
    def post(self, request, *args, **kwargs):
        doc_id = int(self.request.data['doc_id'])
        re_id = int(self.request.data['re_id'])

        doc = get_object_or_404(Doc, pk=doc_id)
        project = doc.project

        re_ = get_object_or_404(Re, pk=re_id)

        #验证下一致性
        if re_.project != doc.project:
            return Response({'error':'this doc and re not match'}, status.HTTP_400_BAD_REQUEST)
        
        #查询返回的queryset内对象并不是entity_template的object，而是一个只包含id的dict，因为用了values
        entity_template_list = dao.get_re_entity_template_by_order(re_)

        match_list = utils.re_match(doc, project, re_, entity_template_list)

        return Response(match_list, status.HTTP_200_OK)
        

'''
@description: 在某条文本处采用字典匹配，且只选择 某一实体模板的 字典（例如只匹配地点的字典）
@param {type} 
@return: 
'''   
class ProjectDicMatch(APIView):
    def post(self, request, *args, **kwargs):
        doc_id = int(self.request.data['doc_id'])
        entity_template_id = int(self.request.data['entity_template_id'])
        print(doc_id, entity_template_id)
        doc = get_object_or_404(Doc, pk=doc_id)
        project = doc.project
        entity_template = get_object_or_404(Entity_template, pk=entity_template_id) 

        #验证下一致性
        project_entity_template = dao.get_entity_template_by_project(project)
        project_entity_template = project_entity_template.all()
        if entity_template not in project_entity_template:
            return utils.return_Response('error', 'project, doc and entity_template is not consist!', status.HTTP_400_BAD_REQUEST)       

        #获取该实体类型下的所有字典
        dic_queryset = dao.get_dic_by_entity_template_and_project(entity_template, project)
        
        #匹配返回结果list
        match_list = utils.dic_match(doc, dic_queryset, entity_template)

        return Response(match_list, status.HTTP_200_OK)


'''
@description: 任务epoches的创建和对应进度查询
@param {type} 
@return: 
'''       
class ProjectEpoch(APIView):
    #get请求用于查询该任务下的epoch信息，以及每一个epoch的进度
    def get(self,request,*args, **kwargs):
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project,pk=project_id)

        #查询该project下的epoch
        epoches = dao.get_epoch_by_project(project)

        #serialize epoch
        serializer = EpochSerializer(epoches,many=True)

        #查询出来的data是一个epoch_num对应多个epoch，合并，减轻前端压力
        merge_data = utils.merge_epoch_data(serializer.data)

        return Response(merge_data,status=status.HTTP_200_OK)

    #post请求用于确定epoch的分配和ann_allocation以及review_allocation的创建,如果用户上传了答案，则将答案写入库中
    def post(self,request,*args, **kwargs):
        #epoch表的分配
        project_id = self.kwargs['projectid']
        annotators_id = [int(x) for x in request.data['annotators'].split(',')]
        reviewers_id = [int(x) for x in request.data['reviewers'].split(',')]
        answer_file = request.FILES
        # print(list(annotators_id),type(annotators_id))
        answer_list = utils.resolve_answer_file(answer_file)

        validate_data = self.validate(project_id,annotators_id,reviewers_id)
        if isinstance(validate_data,Response):
            return validate_data
        project,annotators,reviewers = validate_data[0],validate_data[1],validate_data[2]

        #验证ann_per_epoch_num是否大于annotator的数量
        print(project.ann_num_per_epoch)
        if project.ann_num_per_epoch < len(annotators):
            return utils.return_Response('error','ann_per_epoch_num should be bigger than annotator nums!',status.HTTP_400_BAD_REQUEST)

        #创建epoch表
        serialize_data,total_epoches = utils.get_epoch_serializer_data(project,annotators,reviewers)
        serializer = EpochSerializer(data=serialize_data,many=True)
        serializer.is_valid(raise_exception=True)

        try:
            #加一个事务，doc表和project保持原子性
            with transaction.atomic():
                serializer.save()
                #如果是主动学习，待分配的epoch数为1，其他为total_epoches
                total_allocate_epoch = 1 if project.project_type == 'ACTIVE_LEARNING' else total_epoches        
                #ann_allocation的分配,review_allocation的分配
                utils.get_annotation_review_allocation(project,total_allocate_epoch,annotators,reviewers,answer_list)
        except Exception as e:
            return Response(str(e),status=status.HTTP_400_BAD_REQUEST)
        
        return utils.return_Response('message','create successfully!',status.HTTP_201_CREATED)  
        

    def validate(self,project_id,annotators_id,reviewers_id):
        #数据有效性做验证
        project = get_object_or_404(Project,pk=project_id)

        annotators = User.objects.filter(pk__in=annotators_id)
        reviewers = User.objects.filter(pk__in=reviewers_id)
        print(annotators, reviewers)

        #验证annotators和reviewers的身份
        annotator_role = get_object_or_404(Role,name='annotator')
        reviewer_role = get_object_or_404(Role,name='reviewer')
        for annotator in annotators:
            if annotator_role not in annotator.role.all():
                return utils.return_Response('errors','invalid annotator of id = {}'.format(annotator.id),status.HTTP_404_NOT_FOUND)
        for reviewer in reviewers:
            if reviewer_role not in reviewer.role.all():
                return utils.return_Response('errors','invalid reviewer of id = {}'.format(reviewer.id),status.HTTP_404_NOT_FOUND)
        if len(annotators) != len(annotators_id) or len(reviewers) != len(reviewers_id):
            return utils.return_Response('errors','has invalid user id',status.HTTP_404_NOT_FOUND)
        
        return [project,annotators,reviewers]

'''
@description: annotator查询自己所有的epoches及进度
@param {type} 
@return: 
'''
class AnnotatorEpoch(generics.ListAPIView):
    serializer_class = EpochSerializer
    def get_queryset(self):
        annotator_id = self.kwargs['annotatorid']
        annotator = get_object_or_404(User,pk=annotator_id)

        # #判断是否存在标注者身份
        # if not utils.is_annotator(annotator):
        #     return utils.return_Response('errors','no annotator with pk = {}'.format(annotator_id),status.HTTP_404_NOT_FOUND)

        #查询该user所有epoch
        epoches = dao.get_epoch_by_annotator(annotator)

        return epoches

    def get_serializer(self, instance=None, data=None, many=False, partial=False):
        fields =  ['id','num','state','re_annotate_num','annotator','project','annotate_progress']
        return self.serializer_class(instance,many=True,fields=fields)

'''
@description: reviewer查询自己所有epoches及进度
@param {type} 
@return: 
'''
class ReviewerEpoch(generics.ListAPIView):
    serializer_class = EpochSerializer
    def get_queryset(self):
        reviewer_id = self.kwargs['reviewerid']
        reviewer = get_object_or_404(User,pk=reviewer_id)

        #判断是否存在标注者身份
        if not utils.is_reviewer(reviewer):
            return utils.return_Response('errors','no reviewer with pk = {}'.format(reviewer_id),status.HTTP_404_NOT_FOUND)

        #查询该user所有epoch
        epoches = dao.get_epoch_by_reviewer(reviewer)

        return epoches

    def get_serializer(self, instance=None, data=None, many=False, partial=False):
        fields =   ['id','num','state','reviewer','project','review_progress']
        return self.serializer_class(instance,many=True,fields=fields)

    #对于reviewer的epoches搜索要做处理，因为一个真实epoch在Epoch表中对应多个epoch，但只对应一个reviewer
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        merge_data = utils.merge_reviewer_epoch(serializer.data)
        
        return Response(merge_data)

'''
@description: 查询某epoches下的doc
@param {type} 
@return: 
'''
class EpochDoc(generics.ListAPIView):
    serializer_class = DocSerializer

    #查询该epoch的doc
    def get_queryset(self):
        epoch_id = self.kwargs['epochid']
        epoch = get_object_or_404(Epoch,pk=epoch_id)
        print(epoch.doc.all())
        return epoch.doc.all()
        

'''
@description: 创建一个实体标注，（NER RE EVENT）会用到
@param {type} 
@return: 
'''
class AnnotationEntity(generics.ListCreateAPIView):
    serializer_class = EntityAnnotationSerializer

    #由于perform_create执行时已经获取了serializer，这里重写create方法
    def create(self,request, *args, **kwargs):
        #根据上传的data是否为list决定实例化serializer是many是否为True
        many = isinstance(self.request.data,list)

        validate_result = self.validate_entity_annotation()
        if validate_result is not None:
            return validate_result

        serializer = self.serializer_class(data=request.data,many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def validate_entity_annotation(self):
        #如果是事件标注,event_group_annotation不能为null
        doc_id = self.kwargs['docid']
        doc = get_object_or_404(Doc, pk=doc_id)
        project_type = doc.project.template.template_type
        if project_type == 'EVENT':
            data = self.request.data
            data = [data] if isinstance(data, dict) else data
            for item in data:
                if 'event_group_annotation' not in item or item['event_group_annotation'] == 'null':
                    return Response('event_group_annotation not found!', status.HTTP_400_BAC_REQUEST)
'''
@description: 删除一个doc下的entity标注
@param {type} 
@return: 
'''
class AnnotationEntityDelete(generics.DestroyAPIView):
    serializer_class = EntityAnnotationSerializer
    queryset = Entity_annotation
    lookup_url_kwarg = 'entityid'

'''
@description: 创建一个关系标注，RE时会用
@param {type} 
@return: 
'''
class AnnotationRelation(generics.CreateAPIView):
    serializer_class = RelationAnnotationSerializer

'''
@description: 删除doc下的关系标注
@param {type} 
@return: 
'''
class AnnotationRelationDelete(generics.DestroyAPIView):
    serializer_class = RelationAnnotationSerializer
    queryset = Relation_annotation
    lookup_url_kwarg = 'relationid'

'''
@description: 创建一个事件标注
@param {type} 
@return: 
'''
class AnnotationEvent(generics.CreateAPIView):
    serializer_class = EventAnnotationSerializer

'''
@description: 删除事件组标注
@param {type} 
@return: 
'''
class AnnotationEventDelete(generics.DestroyAPIView):
    serializer_class = EventAnnotationSerializer
    queryset = Event_group_annotation
    lookup_url_kwarg = 'eventid'

'''
@description: 创建一个分类标注
@param {type} 
@return: 
'''
class AnotationClassification(generics.CreateAPIView):
    serializer_class = ClassificationAnnotationSerializer

'''
@description: 删除分类标注
@param {type} 
@return: 
'''
class AnotationClassificationDelete(generics.DestroyAPIView):
    serializer_class = ClassificationAnnotationSerializer
    queryset = Classification_annotation
    lookup_url_kwarg = 'classificationid'

'''
@description: 查看某一个doc的标注结果
@param {type} 
@return: 
'''
class AnnotationList(APIView):
    '''
    @description: 查询某一条doc的标注结果（根据任务类型）
    @param {type} 
    @return: 
    '''
    def get(self,request,*args, **kwargs):
        doc_id = self.kwargs['docid']
        user_id = self.kwargs['userid']
        role_name = self.kwargs['role']

        #获取doc和user对象
        doc = get_object_or_404(Doc,pk=doc_id)
        user = get_object_or_404(User,pk=user_id)
        role = get_object_or_404(Role,name=role_name)
        
        #获取标注类型
        annotation_type = dao.get_annotation_type_by_doc(doc)

        #根据标注类型返回标注数据
        if annotation_type == 'NER':
            data = utils.get_ner_annotation(doc,user,role)
        elif annotation_type == 'RE':
            data = utils.get_re_annotation(doc,user,role)
        elif annotation_type == 'EVENT':
            data = utils.get_event_annotation(doc,user,role)
        else:
            data = utils.get_classification_annotation(doc,user,role)

        return Response(data,status=status.HTTP_200_OK)

class AnnotationConfirmation(generics.CreateAPIView):
    def post(self,request,*args, **kwargs):
        user_id = self.request.data['user']
        role_id = self.request.data['role']
        doc_id = self.kwargs['docid']

        #获取user、role和doc
        doc = get_object_or_404(Doc,pk=doc_id)
        user = get_object_or_404(User,pk=user_id)
        role = get_object_or_404(Role,pk=role_id)

        #annotation_allocation的状态改变
        annotation_allocation = dao.get_annotation_allocation_by_doc_user(doc,user)
        dao.update_annotation_allocation_state(annotation_allocation,'WAITING')
        
        # #检测当前user在当前epoch是否全部标注完成
        # if utils.has_user_finish_epoch(doc,user,role):
        #     #查询该doc该user该role下的epoch
        #     annotator_epoch = dao.get_epoch_of_annotator_by_doc(doc,user,role)

        #     #改变当前epoch的状态
        #     dao.update_epoch_state(annotator_epoch,'WAITING')

        #     #判断该epoch所有的user是否都完成标注
        #     if utils.has_finish_epoch(doc,user,role):
        #         waiting_epoch = dao.get_waiting_epoch(doc)

        #         #机器进行一致性校验，不通过直接打回重标    
        #         consistency_result,consistency_annotation_list = utils.get_consistency_result(doc)
        #         #如果consistency_result的长度为0，说明通过一致性校验，可以进入审核阶段
        #         if len(consistency_result) == 0:        
        #             dao.update_epoch_state(waiting_epoch,'REVIEWING')
        #             #保存二者的并集标注，以审核者的身份保存
        #             has_saved = utils.save_union_annotations(consistency_annotation_list,annotator_epoch)
                    
        #             if not has_saved:
        #                 return utils.return_Response('error','invalid_deserialize_data',status=status.HTTP_400_BAD_REQUEST)
        #         else:
        #             utils.re_annotation(consistency_result)

        #         project = dao.get_project_by_doc(doc)

        #         #是否为普通任务的最后一个epoch,如果不是则将下一个epoch激活
        #         if not dao.is_last_epoch(project,doc):
        #             if project.project_type == 'NON_ACTIVE_LEARNING':
        #                 #如果不是ACITVE_LEARNING,则将下一个epoch的state改为ANNOTATING
        #                 next_epoch_num = annotator_epoch.num + 1
        #                 next_epoches = dao.get_epoch_by_num_and_project(next_epoch_num,project)
        #                 dao.update_epoch_state(next_epoches,'ANNOTATING')
                    
        #             if project.project_type == 'ACITVE_LEARNING':
        #                 #如果是主动学习，调用接口选择下一个epoch的doc并分配
        #                 pass

        return utils.return_Response('message','confirm successfully',status.HTTP_200_OK)

'''
@description: 根据project,epoch,user,role得到对应一轮的标注结果并传给前端,role是reviewer时为最终标注结果 [lyp]
@param {project,epoch,user,role} 
@return: 
'''
class AnnotationResult(generics.CreateAPIView):
    def post(self,request,*args, **kwargs):
        project_id = self.request.data['project']

        project = get_object_or_404(Project,pk=project_id)

        #获取project的type
        project_type = dao.get_project_type_by_project(project)

        #获取该project下所有doc
        project_doc = dao.get_doc_by_project(project)
        
        result_list = []
        
        #role直接是标注者
        role = Role.objects.get(pk=2)
        for epoch_doc in project_doc:
            #查询每条文本的标注者
            user = dao.get_annotator_by_doc(epoch_doc)

            if project_type == 'NER':
                entity_list = utils.get_entity_annotation_list(epoch_doc, user, role)
                dic = {'doc_content':epoch_doc.content,'entity':entity_list}
                result_list.append(dic)
            elif project_type == 'RE':
                entity_list = utils.get_entity_annotation_list(epoch_doc, user, role)
                relation_list = utils.get_relation_annotation_list(epoch_doc, user, role)
                dic = {'doc_content':epoch_doc.content,'entity':entity_list,'relation':relation_list}
                result_list.append(dic)
            elif project_type == 'EVENT':
                entity_list = utils.get_entity_annotation_list(epoch_doc, user, role)
                event_group_list = utils.get_event_group_annotation_list(epoch_doc, user, role)
                new_event_group_list = []
                for event_group in event_group_list:
                    event_group_dic = {}
                    event_group_dic['event_group_template'] = event_group['event_group_template_name']
                    event_group_entity_list = []
                    for entity in entity_list:
                        if 'event_group' in entity.keys() and entity['event_group'] == event_group['event_group_annotation_id']:
                            event_group_entity_list.append(entity)
                            entity.pop('event_group')
                    
                    event_group_dic['entity'] = event_group_entity_list
                    new_event_group_list.append(event_group_dic)
                
                dic = {'doc_content':epoch_doc.content, 'event_group': new_event_group_list}
                result_list.append(dic)
                        
            else:
                class_name = utils.get_classification_annotation_list(epoch_doc, user, role)
                dic = {'doc_content':epoch_doc.content, 'class': class_name}
                result_list.append(dic)    
                     
        return utils.return_Response('result_file',result_list,status.HTTP_200_OK)

'''
@description: 查询user的role
@param {type} 
@return: 
'''   
@csrf_exempt  
class RoleList(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        try:
            role = Role.objects.filter(user=self.request.user)
        except:
            return utils.return_Response('error','user not found',status.HTTP_404_NOT_FOUND)
        role_serializer = RoleSerializer(role,many=True)
        role_list = utils.serialize_user_role(role_serializer.data)

        return utils.return_Response('roles',role_list,status.HTTP_200_OK)    

'''
@description: Reviewer查询epoch下的doc，需查询epoch_num下的所有的doc
@param {type} 
@return: 
'''
class ReviewerEpochDoc(generics.ListAPIView):
    serializer_class = DocSerializer

    #查询该epoch的doc
    def get_queryset(self):
        epoch_id = self.kwargs['epochid']
        epoch = get_object_or_404(Epoch,pk=epoch_id)
        return dao.get_reviewer_epoch_doc(epoch)

'''
@description: 创建project下的标准名称表，可通过文件和手动上传两种方式
@param {type} 
@return: 
'''
class ProjectStandard(generics.ListCreateAPIView):
    serializer_class = StandardSerializer
    def post(self, request, *args, **kwargs):
        project_id = self.kwargs['projectid']
        project = get_object_or_404(Project,pk=project_id)
        create_type = self.request.data['type']
        #根据上传类型获取上传的数据，转成dic返回
        serialize_data = self._get_upload_data(create_type,project)
        if not isinstance(serialize_data,list):
            return serialize_data
        
        serializer = self.serializer_class(data=serialize_data,many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return utils.return_Response('msg',"upload success!",status.HTTP_200_OK)

    def _get_upload_data(self,create_type,project):
        #文件上传
        if create_type == 'file':
            files = self.request.FILES
            if len(files) == 0:
                return utils.return_Response("error","no valid file",status.HTTP_400_BAD_REQUEST)
            else:
                data = utils.resolve_standard_file(files)
                if data is None:
                    return utils.return_Response("error","using utf-8",status.HTTP_400_BAD_REQUEST)
        #手动上传
        else:
            data =  self.request.data['data']

        serialize_data = []
        entity_template_queryset = dao.get_entity_template_by_project(project)
        print(entity_template_queryset)

        for k,v in data.items():
            #获取entity_template的id
            try:
                entity_template = entity_template_queryset.get(name=k)
            except:
                return Response('no entity template called ' + k, status.HTTP_400_BAD_REQUEST)
            print(k, entity_template)
            for standard_name in v:
                dic = {}
                dic['entity_template'] = entity_template.id
                dic['project'] = project.id
                dic['standard_name'] = standard_name
                serialize_data.append(dic)

        return serialize_data                

'''
@description: 输入entity_template的id，查询对应的standard_name
@param {type} 
@return: 
'''
class EntityTemplateStandard(generics.ListAPIView):
    serializer_class = StandardSerializer
    def get_queryset(self):
        entity_template_id = self.kwargs['entitytemplateid']
        project_id = self.kwargs['projectid']
        return dao.get_standard_by_entity_template_id(entity_template_id, project_id)

'''
@description: 更新一条实体标注的standard名称
@param {type} 
@return: 
'''
class AnnotationStandard(generics.UpdateAPIView):
    def partial_update(self, request, *args, **kwargs):
        annotation_id = self.kwargs['annotationid']
        standard_name_id = self.request.data['standard_name_id']

        annotation = get_object_or_404(Entity_annotation,pk=annotation_id)
        standard = get_object_or_404(Standard,pk=standard_name_id)
        
        annotation.standard = standard
        annotation.save()
        
        return utils.return_Response('msg','create standard success!',status.HTTP_200_OK)

class UserList(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    
    def get_queryset(self):
        role_id = self.request.GET['role_id']
        return dao.get_user_list_by_role_id(role_id)

    def post(self, request, *args, **kwargs):
        user_name = self.request.data['user_name']
        password_word = self.request.data['password']
        role_list = [int(x) for x in self.request.data['role_list'].split(',')]
        is_active = True

        try:
            user = User.objects.create_user(username=user_name, password=password_word, is_active=is_active)
        except:
            return utils.return_Response('error', 'this username has existed!', status.HTTP_400_BAD_REQUEST)  # 已经创建，无法重复创建

        #创建user和role的关系
        if user is not None:
            for role in role_list:
                r = get_object_or_404(Role, pk=role)
                user.role.add(r)
        
        return utils.return_Response('msg', 'create successful', status.HTTP_200_OK)



    