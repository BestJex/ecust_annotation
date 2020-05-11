'''
@Author: liangming
@Date: 2019-12-26 08:28:23
@LastEditTime: 2020-05-10 06:05:17
@LastEditors: Please set LastEditors
@Description: 各种工具方法
@FilePath: /ecust_annotation/api/utils.py
'''
import chardet
from rest_framework.response import Response
from rest_framework import status
from api.models import *
from api.serializer import *
from django.db import transaction
from api import dao
from django.shortcuts import get_object_or_404
import math
import random
import re
from api import consistency
import pickle
import json
import pandas as pd

'''
@description: 验证上传文件是否符合要求，读取所有的文件，并保存在一个list中返回
@param {file} 
@return: file中每行的list，如果出错，返回报错信息
'''
def validate_files(files):
    docs = []
    #迭代每个文件
    for f in files.getlist('file'):
        # #迭代文件中的每一行
        # for line in f:
        #     #如果不为utf-8则跳过改行
        #     if chardet.detect(line)['encoding'] not in ['utf-8','ascii']:
        #         continue 
        #     doc_line = line.decode('utf-8').strip().replace('\r','').replace('\n','')
        #     #如果该行为空
        #     if doc_line == "":
        #         continue
        #     docs.append(doc_line)

        #每个文件就是一份数据
        doc = f.read().decode()
        #如果是windows上传的,把\r\n替换成\n 
        doc = doc.replace('\r\n','\n')
        docs.append(doc)
        

    #如果没有上传文件或者文件格式不正确，报错
    if len(docs) == 0:
        return return_Response('error','not valid file format!',status.HTTP_400_BAD_REQUEST)

    return docs

#将doc序列化成DocSerializer可接受的格式
def serialize_doc(docs,project_id):
    data = []
    for doc in docs:
        data.append({"content":doc,"project":project_id})
    return data

'''
@description: 验证字典内容，格式要求为一行中间\t分隔符，左边是文本内容，右边是对应的实体标签；
            需要检查实体标签是否存在与该任务的模板中，同时要检测格式是否正确
@param {type} 
@return: 如果中途出现问题，返回Respone类型；如果没有出错，返回dic的list，里面是serialize好的字典数据，可直接save
'''
def validate_dic(file_list,project):
    dic = []
    #得到project下所有的queryset
    entity_template_query_set = dao.get_entity_template_by_project(project)

    #如果为空直接返回494
    if len(entity_template_query_set) == 0:
        return return_Response('error','the template of this project does not have any entity template',status.HTTP_404_NOT_FOUND)
        
    for f in file_list.getlist('file'):
        df = pd.read_excel(f)
        #将df中的nan改为''
        df = df.fillna('')
        for index, row in df.iterrows():
            content = row['content']
            entity_name = row['entity_name']
            standard_name = row['standard_name']
            dic_dict = validate_dic_data(content, entity_name, standard_name, project)
            if isinstance(dic_dict, Response):
                return dic_dict

            dic.append(dic_dict)

    if len(dic) == 0:
        return return_Response('error','no valid data in uploaded dic file! may be input wrong entity name',status.HTTP_400_BAD_REQUEST)
    
    return dic

'''
@description: 验证手动上传的字典
@param {type} 
@return: 
'''
def validate_dic_data(content, entity_name, standard_name, project):
    dic_dict = {}
    dic_dict['project'] = project.id
    dic_dict['content'] = content

    #得到project下所有的queryset
    entity_template_query_set = dao.get_entity_template_by_project(project)

    entity_template = has_entity_template_by_entity_name(entity_template_query_set,entity_name)
    #如果没找到就读下一行, 如果有查看标准是否存在
    if entity_template is None:
        return return_Response('error', 'no entity_template called ' + entity_name, status.HTTP_400_BAD_REQUEST)
    else:
        dic_dict['entity_template'] = entity_template.id
        if standard_name != '':
            standard_queryset = has_standard_template_by_standard_name(entity_template, standard_name)
            if len(standard_queryset) == 0:
                print(entity_name, standard_name)
                resp_content = entity_name + ' has no standard called ' + standard_name 
                return return_Response('error', resp_content, status.HTTP_400_BAD_REQUEST)
            else:
                standard = standard_queryset[0]
                dic_dict['standard'] = standard.id
        return dic_dict


'''
@description: 返回message
@param {type} 
@return: 
'''
def return_Response(msg_type,msg_content,status):
    content = {msg_type:msg_content}
    return Response(content,status=status)


'''
@description: 根据名字判断query_set中是否存在这样一个model，
@param {type} 
@return: 如果不存在返回None，存在的话返回这个model对象
'''
def has_entity_template_by_entity_name(query_set,name):
    for item in query_set:
        if name == item.name:
            return item
    return None
        

'''
@description: 得到epoch的serializer的data
@param {type} 
@return: 
'''
def get_epoch_serializer_data(project,annotators,reviewers):
    serialize_data = []
    #得到project的type
    project_type = project.project_type

    ann_num_per_epoch = project.ann_num_per_epoch
    docs_num = dao.get_doc_num_by_project(project)

    total_epoches = math.ceil(docs_num/ann_num_per_epoch)

    #每个epoch分配所有的标注者，选择一个审核者
    #且把第一个epoch的state设置为ANNOTATING
    for epoch_num in range(total_epoches):
        for annotator in annotators:
            data = {}
            data['num'] = epoch_num + 1
            data['re_annotate_num'] = 0
            data['project'] = project.id
            data['reviewer'] = reviewers[epoch_num%len(reviewers)].id
            data['annotator'] = annotator.id

            #每一个epoch都是annotating
            data['state'] = 'ANNOTATING'
            serialize_data.append(data)
            print(data,'\n')
    return serialize_data,total_epoches

'''
@description: 分配ann_allocation和review_allocation,如果上传了答案，对答案需要做解析
@param {type} 
@return: 
'''
def get_annotation_review_allocation(project,total_allocate_epoch,annotators,reviewers,answer_list):
    #查询所有project的doc
    project_doc_list = dao.get_doc_by_project(project)
    project_doc_id_list = [x.id for x in project_doc_list]
    for epoch_num in range(total_allocate_epoch):
        #获得该epoch_num的所有epoch（每个annotator一个）
        epoches = dao.get_epoch_by_num_and_project(epoch_num+1,project)

        #获取待分配的doc，其中地雷任务会返回全部
        docs = get_random_unallocated_docs_by_project(project)

        #每一个doc分配给一个annotator及一个reviewer
        for doc_index in range(len(docs)):
            doc = docs[doc_index]
            epoch = epoches[doc_index%len(epoches)]

            #更新doc的epoch
            dao.update_doc_epoch(doc,epoch)

            #创建annotation_allocation
            dao.create_annotation_allocation(doc,epoch)

            #创建reviewr_allocation
            dao.create_review_allocation(doc,epoch)

            #如果answer_list不为零，则要预先写入答案
            if len(answer_list) != 0:
                success = pre_save_answer(doc,epoch,answer_list,project_doc_id_list,project)
                if not success:
                    print('false')
                

        #对每一条文本进行分配,每一个doc分配两个annotator一个reviewer
        #即每个doc分配和两个epoch做分配
        # for doc_index in range(2*len(docs)):
        #     doc = docs[doc_index//2]
        #     epoch = epoches[doc_index%len(epoches)]

        #     #更新doc的epoch
        #     dao.update_doc_epoch(doc,epoch)

        #     #创建annotation_allocation
        #     dao.create_annotation_allocation(doc,epoch)

        #     #如果answer_list不为零，则要预先写入答案
        #     if len(answer_list) != 0:
        #         success = pre_save_answer(doc,epoch,answer_list,project_doc_id_list,project)
        #         if not success:
        #             print('false')

        #     #每一个doc两个annotator一个reviewer
        #     if doc_index%2 == 0:
        #         dao.create_review_allocation(doc,epoch)
            


'''
@description: 根据任务，随机选择一个epoch数量的doc
@param {type} 
@return: 
'''
def get_random_unallocated_docs_by_project(project):
    docs = dao.get_unallocated_docs_by_project(project)
    ann_num_per_epoch = project.ann_num_per_epoch

    #如果剩余数量比ann_num_per_epoch小，直接返回（地雷任务会直接返回全部）
    if len(docs) <= ann_num_per_epoch:
        #这里返回的是queryset
        return docs

    index_list = range(len(docs))
    random_index = random.sample(index_list, ann_num_per_epoch) 

    random_docs = [docs[i] for i in random_index]

    #懒得组装成queryset，这里就是list返回
    return random_docs

'''
@description: 因为实际一个epoch在Epoch表中对应多条记录（取决于标注者的个数）
@param {type} 
@return: list，个数等于实际epoch个数
'''
def merge_epoch_data(serialize_data):
    data = []
    for epoch_data in serialize_data:
        #如果是一个新的epoch_num
        if epoch_data['num'] > len(data):
            data_item = {}
            data_item['num'] = epoch_data['num']
            data_item['state'] = ''
            # data_item['state'] = epoch_data['state']
            data_item['annotators'] = []
            data_item['reviewers'] = {'reviewer':epoch_data['reviewer'],'progress':epoch_data['review_progress']}
            data.append(data_item)
        data_item['annotators'].append({'annotator':epoch_data['annotator'],'progress':epoch_data['annotate_progress'],'annotator_state':epoch_data['state']})
        data_item['state'] = get_epoch_state(data_item)
    return data

'''
@description: 由一个epoch_num里面每一个epoch的状态得到epoch_num的状态
@param {type} 
@return: 
'''
def get_epoch_state(data_item):
    state_list = [x['annotator_state'] for x in data_item['annotators']]
    #如果存在正在标注的，则整个epoch_num处于正在标注
    if 'UNDO' in state_list:
        return 'UNDO'
    if 'ANNOTATING' in state_list:
        return 'ANNOTATING'
    #如果存在一个重复标注的的，整个epoch_num处于重复标注
    if 'RE_ANNOTATING' in state_list:
        return 'RE_ANNOTATING'
    #此时要么是正在审核，要么是完成
    if 'REVIEWING' in state_list:
        return 'REVIEWING'
    else:
        return 'FINISH'


'''
@description: 判断user是否为annotator
@param {type} 
@return: 
'''
def is_annotator(user):
    for role in user.role.all():
        if role.name == 'annotator':
            return True
    return False

'''
@description: 判断user是不是为reviewer
@param {type} 
@return: 
'''
def is_reviewer(user):
    for role in user.role.all():
        if role.name == 'reviewer':
            return True
    return False

'''
@description: 合并reviewer查询到的epoch数据，例如某一project的第一个epoch，
在Epoch表中可能有项（=标注者个数），但是根据设计，一个真实epoch只对应一个reviewer
@param {type} 
@return: 
'''
def merge_reviewer_epoch(data):
    merge_data = []
    project_epoch_list = []
    for epoch_data in data:
        project_epoch = str(epoch_data['project']) + '-' + str(epoch_data['num'])
        if project_epoch not in project_epoch_list:
            project_epoch_list.append(project_epoch)
            epoch_data['id'] = [epoch_data['id']]
            merge_data.append(epoch_data)
        else:
            merge_data[project_epoch_list.index(project_epoch)]['id'].append(epoch_data['id'])
    
    return merge_data

'''
@description: 返回ner的标注结果
@param {type} 
@return: 
'''
def get_ner_annotation(doc,user,role):
    #首先获取entity_annotation的queryset
    entity_annotation = dao.get_entity_annotation_by_doc(doc,user,role)
    serializer = EntityAnnotationSerializer(entity_annotation,many=True)
    data = []
    for item in serializer.data:
        dic = item
        entity_template_id = item['entity_template']
        entity_group_template = dao.get_entity_group_template_by_entity_template(entity_template_id)
        event_group_template = dao.get_event_group_template_by_entity_template(entity_template_id)
        if entity_group_template is not None:
            dic['entity_group_template_name'] = entity_group_template.name
        else:
            dic['entity_group_template_name'] = ''

        if event_group_template is not None:
            dic['event_group_tempalte_name'] = event_group_template.name
        else:  
            dic['event_group_template_name'] = ''

            
        data.append(dic)

    return data

'''
@description: 返回re的标注结果
@param {type} 
@return: 
'''
def get_re_annotation(doc,user,role):
    #先获得实体标注的结果
    entity_annotation_data = get_ner_annotation(doc,user,role)

    #再返回关系标注的结果
    relation_annotation = dao.get_relation_annotation_by_doc(doc,user,role)
    serializer = RelationAnnotationSerializer(relation_annotation,many=True)

    return {'entities':entity_annotation_data,'relations':serializer.data}


'''
@description: 返回事件标注的结果
@param {type} 
@return: 
'''
def get_event_annotation(doc,user,role):
    data = []
    #先获得实体标注的结果
    entity_annotation_data = get_ner_annotation(doc,user,role)

    #再返回事件元组的标注
    event_annotation = dao.get_event_annotation_by_doc(doc,user,role)
    serializer = EventAnnotationSerializer(event_annotation,many=True)
    event_annotation_data = serializer.data
    #把entity和event整合一下
    for event in event_annotation_data:
        event_id = event['id']
        event_entity = []
        for entity in entity_annotation_data:
            if entity['event_group_annotation'] == event_id:
                event_entity.append(entity)
        event['entities'] = event_entity
        data.append(event)
    
    return data

'''
@description: 返回分类标注的结果
@param {type} 
@return: 
'''
def get_classification_annotation(doc,user,role):
    classification_annotation = dao.get_classification_by_doc(doc,user,role)
    serializer = ClassificationAnnotationSerializer(classification_annotation,many=True)
    return serializer.data

'''
@description: 用于检测user是否完成了这个epoch的任务
@param {type} 具体来讲：annotator是否完成标注或重标，reviewer是否完成了审核
@return: 
'''
def has_user_finish_epoch(doc,user,role):
    epoch = dao.get_epoch_of_annotator_by_doc(doc,user,role)
    doc = dao.get_doc_by_epoch(epoch)
    #通过查询ann_allocation表中处于undo状态或re_annotation状态的，
    #如果不存在，说明这个epoch标注完成
    if role.name == 'annotator':
        #查询当前doc的epoch        
        finish_situation = Annotate_allocation.objects.filter(annotator=user).filter(doc__in=doc).filter(state__in=['UNDO','RE_ANNOTATION'])
    else:
        finish_situation = Review_allocation.objects.filter(reviewer=user).filter(doc__in=doc).filter(state='UNDO')
    return True if len(finish_situation)==0 else False

'''
@description: 查看这个doc所属epoch是否真的完成了
@param {type} 用于第一次标注检查其他epoch是否标注完成；或重新标注时其他人是否重标完成
@return: 
'''
def has_finish_epoch(doc,user,role):
    #第一次标注，判断条件是所有epoch都处于waiting状态
    #重标时，存在部分epoch已经finish，但是有一些epoch是re_annotation
    #因此判断处于waiting和finish状态的epoch是否等于该Epoch所对应的总epoch数
    # epoch = doc.epoch.all().filter(state__in=['WAITING','FINISH'])

    # #查询doc对应proejct的epoch的总数
    # return True if len(epoch) == len(dao.get_epoch_by_doc(doc)) else False
    #代表当前doc所对应的project的epoch_num下的所有epoch
    epoch_of_num = dao.get_epoch_by_doc(doc)
    for epoch in epoch_of_num:
        if epoch.state != 'WAITING':
            return False
    return True

'''
@description: 主动学习进行下一个epoch的筛选
@param {type} 
@return: 
'''
def active_learning_allocation(project):
    pass

    
'''
@description: 对该doc所属Epoch的所有doc做一致性校验
@param {type} 
@return: 
'''
def get_consistency_result(doc):
    annotation_data_list = []
    #查询该doc所对应projcet epoch_Num下的所有epoch
    epoches = dao.get_epoch_by_doc(doc)

    #查询该Epoch所对应的所有doc
    doces = dao.get_doc_by_epoch(epoches)
    
    for doc in doces:
        annotation_data = {}
        annotation_data['doc_id'] = doc.pk
        annotation_data['content'] = doc.content
        annotation_data['annotation_type'] = dao.get_project_type_by_doc(doc)
        #查询每一条doc对应的标注
        annotation_one,annotation_two = dao.get_annotation_of_doc(doc,annotation_data['annotation_type'])
        annotation_data['annotation_one'],annotation_data['annotation_two'] = serialize_annotation_data(annotation_one,annotation_two,annotation_data['annotation_type'])
        annotation_data_list.append(annotation_data)
    print(annotation_data_list)
    #进行一致性校验,consistency_result应该为一个list，里面记录需要重新标注的doc_id
    score_list = consistency.Consistency(annotation_data_list).getSimScore()
    consistency_result = consistency.Consistency(annotation_data_list).refusedDocList(score_list,accept=0)
    

    #如果没有需要重写的，得到每条doc的二者标注并集，并返回
    consistency_annotation_list = consistency.Consistency(annotation_data_list).getUnion()
    print(consistency_annotation_list)
    #真实应该返回consistency_result
    return consistency_result,consistency_annotation_list

'''
@description: 输入一致性不通过的doc的id，将其annotation_allcation的对应记录state改为re_annotation，
同时将对应epoch的state改为re_annotation，并记录该epoch的re_annotation_num
@param {type} 
@return: 
'''
def re_annotation(consistency_result):
    epoches = {}
    doces = Doc.objects.filter(id__in=consistency_result)
    print(consistency_result)

    for doc in doces:
        #更新doc的annotate_allocation状态
        annotation_allocation = Annotate_allocation.objects.filter(doc=doc)
        dao.update_annotation_allocation_state(annotation_allocation,'RE_ANNOTATION')

        #获得doc对应的epoch的id
        doc_epoch = dao.get_doc_epoch(doc)
        epoch_one_id,epoch_two_id = doc_epoch[0].pk,doc_epoch[1].pk
        epoches = add_re_annotation_num_of_epoch(epoches,epoch_one_id)
        epoches = add_re_annotation_num_of_epoch(epoches,epoch_two_id)
    print(epoches)
    for epoch_id,re_annotate_num in epoches.items():
        epoch = get_object_or_404(Epoch,pk=epoch_id)
        #先将epoch的状态改为RE_annotation
        dao.update_epoch_state(epoch,'RE_ANNOTATION')
        #更新epoch的re_annotation_num
        dao.update_epoch_re_annotate_num(epoch,re_annotate_num)
       

'''
@description: 将doc_epoch中对应的re_annotation_num+1,存在epoches这个dic中，key是epoch的pk，value是re_annotation_num
@param {type} 
@return: 
'''    
def add_re_annotation_num_of_epoch(epoches,epoch_id):
    if epoch_id not in epoches.keys():
        epoches[epoch_id] = 1
    else:
        epoches[epoch_id] += 1
    return epoches

'''
@description: 将user_role的serizlier改一下，前端要求，变成['admin','annotator']这种形式
@param {type} 
@return: 
'''
def serialize_user_role(role_data):
    data = []
    for item in role_data:
        data.append(item['name'])
    return data

'''
@description: 一个epoch_num中所有doc的标注结果（进入此说明每一个doc的一致性校验都通过），这里保存每个doc两个标注者
标注的并集,并且要根据project的type来进行保存
@param {type} consistency_annotation_list为doc的标注结果，annotator_epoch为进行标注确认的标注者该条文本所在的epoch
用于获得其对应的审核者
@return: 
'''
def save_union_annotations(consistency_annotation_list,annotator_epoch):
    reviewer = annotator_epoch.reviewer.id
    role = Role.objects.get(name='reviewer').id
    template_type = annotator_epoch.project.template.template_type
    if template_type == 'NER':
        #序列化union的对象，并保存，如果出错返回False
        entity_objects = serialize_union_entity(consistency_annotation_list,reviewer,role,template_type)
        if isinstance(entity_objects,bool):
            return False

    elif template_type == 'RE':
        #先保存实体
        entity_objects = serialize_union_entity(consistency_annotation_list,reviewer,role,template_type)
        if isinstance(entity_objects,bool):
            return False
        print('entity_saved')
        #再保存关系
        relation_objects = serialize_union_relation(entity_objects,consistency_annotation_list,reviewer,role,template_type)
        if isinstance(relation_objects,bool):
            print()
            return False
        print('relation_saved')

    elif template_type == 'CLASSIFICATION':
        pass
    else:
        pass
    return True

'''
@description: 序列化通过一致性校验的关系的并集，需要先保存实体，如果成功返回对象，否则返回False
@param {type} 
@return: 
'''
def serialize_union_relation(entity_objects,consistency_annotation_list,reviewer,role,template_type):
    relatino_annotation_list = []
    for doc_annotation in consistency_annotation_list:
        for doc_relation_annotation in doc_annotation['relation']:
            relation_annotation_dic = doc_relation_annotation
            relation_annotation_dic['start_entity'] = entity_objects[relation_annotation_dic['start_entity']].id
            relation_annotation_dic['end_entity'] = entity_objects[relation_annotation_dic['end_entity']].id
            relation_annotation_dic['user'] = reviewer
            relation_annotation_dic['role'] = role
            relation_annotation_dic['doc'] = doc_annotation['doc_id']
            relatino_annotation_list.append(relation_annotation_dic)
    relation_serializer = RelationAnnotationSerializer(data=relatino_annotation_list,many=True)
    #如果数据无误保存并返回entity对象
    if relation_serializer.is_valid():
        relation_objects = relation_serializer.save()
        return relation_objects
    else:
        print('-'*10)
        print(relatino_annotation_list)
        return False

'''
@description: 序列化通过一致性校验的实体的并集，并以审核者的身份保存，如果成功返回保存对象，如果错误返回FALSE
@param {type} 
@return: 
'''
def serialize_union_entity(consistency_annotation_list,reviewer,role,template_type):
    #解析数据组装后并保存
    entity_annotation_list = []
    for doc_annotation in consistency_annotation_list:
        for doc_entity_annotation in doc_annotation['entity']:
            entity_annotation_dic = doc_entity_annotation
            entity_annotation_dic['user'] = reviewer
            entity_annotation_dic['role'] = role
            entity_annotation_dic['doc'] = doc_annotation['doc_id']
            entity_annotation_list.append(entity_annotation_dic)
    print(entity_annotation_list)
    entity_serializer = EntityAnnotationSerializer(data=entity_annotation_list,many=True)
    #如果数据无误保存并返回entity对象
    if entity_serializer.is_valid():
        entity_objects = entity_serializer.save()
        return entity_objects
    else:
        return False



'''
@description: 序列化两个标注者对一个文本的标注内容，根据其标注类型决定
@param {type} 
@return: 
'''    
def serialize_annotation_data(annotation_one,annotation_two,annotation_type):
    serialize_annotation_one,serialize_annotation_two = {},{}
    entity_fields = ['id','start_offset','end_offset','content','entity_template','event_group_annotation']
    relation_fields = ['id','relation_entity_template','start_entity','end_entity']
    event_fields = ['id','event_group_template']
    classification_fields = ['id','classification_template']
    
    if annotation_type == 'NER':
        #查询annotator_one的标注结果
        serialize_annotation_one['entity'] = EntityAnnotationSerializer(annotation_one['entity'],fields=entity_fields,many=True).data
        serialize_annotation_two['entity'] = EntityAnnotationSerializer(annotation_two['entity'],fields=entity_fields,many=True).data
    elif annotation_type == 'RE':
        #查询annotator_one的标注结果
        serialize_annotation_one['entity'] = EntityAnnotationSerializer(annotation_one['entity'],fields=entity_fields,many=True).data
        serialize_annotation_two['entity'] = EntityAnnotationSerializer(annotation_two['entity'],fields=entity_fields,many=True).data
        serialize_annotation_one['relation'] = RelationAnnotationSerializer(annotation_one['relation'],fields=relation_fields,many=True).data
        serialize_annotation_two['relation'] = RelationAnnotationSerializer(annotation_two['relation'],fields=relation_fields,many=True).data
    elif annotation_type == 'CLASSIFICATION':
        serialize_annotation_one['classification'] = ClassificationAnnotationSerializer(annotation_one['classification'],fields=classification_fields,many=True).data
        serialize_annotation_two['classification'] = ClassificationAnnotationSerializer(annotation_two['classification'],fields=classification_fields,many=True).data
    else:
        serialize_annotation_one['entity'] = EntityAnnotationSerializer(annotation_one['entity'],fields=entity_fields,many=True).data
        serialize_annotation_two['entity'] = EntityAnnotationSerializer(annotation_two['entity'],fields=entity_fields,many=True).data
        serialize_annotation_one['event'] = EventAnnotationSerializer(annotation_one['event'],fields=event_fields,many=True).data
        serialize_annotation_two['event'] = EventAnnotationSerializer(annotation_two['event'],fields=event_fields,many=True).data
    return serialize_annotation_one,serialize_annotation_two

'''
@description: 解析上传的answer文件
@param {type} 
@return: 
'''
def resolve_answer_file(answer_file):
    if len(answer_file) == 0:
        return []
    else:
        for f in answer_file.getlist('file'):
            print(f, type(f))
            data = f.read()
            return json.loads(data.decode())

'''
@description: 存储answer文件
@param {type} 
@return: 
'''
def pre_save_answer(doc,epoch,answer_list,project_doc_id_list,project):
    print(answer_list)
    #得到该doc在之前上传的doc的index，是按顺序来的，以此找到其答案index
    answer_index = project_doc_id_list.index(doc.id)
    answer = answer_list[answer_index]
    annotation_type = dao.get_annotation_type_by_doc(doc)
    if annotation_type == 'NER':
        entity_list = answer['entity']
        serialize_entity_list = serialize_answer_entity_list(entity_list,project,epoch,doc)
        entity_serializer = EntityAnnotationSerializer(data=serialize_entity_list,many=True)
        if entity_serializer.is_valid():
            entity_annotation_list = entity_serializer.save()
        else:
            return False     
    elif annotation_type == 'RE':
        entity_list = answer['entity']
        serialize_entity_list = serialize_answer_entity_list(entity_list,project,epoch,doc)
        entity_serializer = EntityAnnotationSerializer(data=serialize_entity_list,many=True)
        if entity_serializer.is_valid():
            entity_annotation_list = entity_serializer.save()

            relation_list = answer['relation']
            #如果实体保存成功，接下来保存关系
            serialize_relation_list = serialize_answer_relation_list(relation_list,project,epoch,doc,entity_annotation_list)
            relation_serializer = RelationAnnotationSerializer(data=serialize_relation_list,many=True)
            if relation_serializer.is_valid():
                relation_serializer.save()
            else:
                print(serialize_entity_list,serialize_relation_list)
                return False
        else:
            print(serialize_entity_list)
            return False     
    elif annotation_type == 'EVENT':
        event_group_list = answer['event_group']
        for event_group in event_group_list:
            #首先标注事件组
            event_group_template_name = event_group['event_group_template']
            event_group_dic = serialize_answer_event_group(event_group_template_name, epoch, doc)
            event_group_serializer = EventAnnotationSerializer(data=event_group_dic)
            print('werwerwe',event_group_dic)
            if event_group_serializer.is_valid():
                event_group_annotation = event_group_serializer.save()
            else:
                print('event group data is invalid')
                return False
            #接下来标记该事件下的所有实体
            entity_list = event_group['entity']
            print('werwerwaaaaaaa',entity_list)
            serialize_entity_list = serialize_answer_entity_list(entity_list,project,epoch,doc,event_group_annotation=event_group_annotation)
            entity_serializer = EntityAnnotationSerializer(data=serialize_entity_list,many=True)
            print(serialize_entity_list)
            if entity_serializer.is_valid():
                entity_annotation_list = entity_serializer.save()
            else:
                print('entity data is invalid')
                return False

        pass
    else:
        class_name = answer['class']
        if class_name != '':
            classification_template = dao.get_classification_template_by_name(class_name, epoch)
            classification_data = serialize_answer_classification(classification_template, epoch, doc)
            
            classification_serializer = ClassificationAnnotationSerializer(data=classification_data)
            if classification_serializer.is_valid():
                classification_serializer.save()
            else:
                print('classification answer is not valid', classification_data)
                return False
    return True

'''
@description: 序列化答案的实体列表
@param {type} 
@return: 
'''
def serialize_answer_entity_list(entity_list,project,epoch,doc,event_group_annotation=None):
    serialize_entity_list = []
    role = Role.objects.get(name='annotator')
    for entity in entity_list:
        entity_dic = {}
        entity_dic['start_offset'] = entity['start_offset']
        entity_dic['end_offset'] = entity['end_offset']
        entity_dic['entity_template'] = dao.get_entity_template_id_by_entity_template_name(project,entity['entity_template'])
        entity_dic['doc'] = doc.id
        entity_dic['user'] = epoch.annotator.id
        entity_dic['role'] = role.id
        entity_dic['content'] = entity['content']
        #如果是事件标注，添加事件
        if event_group_annotation is not None:
            entity_dic['event_group_annotation'] = event_group_annotation.id

        #如果有standard,应上传standard
        if 'standard' in entity_dic.keys():
            entity_dic['standard'] = entity['standard']
        serialize_entity_list.append(entity_dic)
    return serialize_entity_list

'''
@description: 序列化答案的关系
@param {type} 
@return: 
'''
def serialize_answer_relation_list(relation_list,project,epoch,doc,entity_annotation_list):
    serialize_answer_relation_list = []
    role = Role.objects.get(name='annotator')
    for relation in relation_list:
        relation_dic = {}
        relation_dic['user'] = epoch.annotator.id
        start_entity = entity_annotation_list[relation['start_entity_id']]
        end_entity = entity_annotation_list[relation['end_entity_id']]
        relation_dic['start_entity'] = start_entity.id
        relation_dic['end_entity'] = end_entity.id
        relation_dic['relation_entity_template'] = dao.get_relation_template_id_by_relation_name_and_entity(project,relation['relation_template'], start_entity, end_entity)
        
        relation_dic['role'] = role.id
        relation_dic['doc'] = doc.id
        serialize_answer_relation_list.append(relation_dic)
    return serialize_answer_relation_list

'''
@description: 解析标准文件
@param {type} 
@return: 
'''
def resolve_standard_file(files):
    for f in files.getlist('file'):
        #迭代文件中的每一行
        data = f.read()
        if chardet.detect(data)['encoding'] not in ['utf-8','ascii']:
            print('error encoding format')
        else:
            a = json.loads(data.decode())
            return a
            

'''
@description: 下载标注结果,得到实体标注的结果
@param {type} 
@return: 
'''
def get_entity_annotation_list(epoch_doc, user, role):
    doc_entity_annotation = dao.get_entity_annotation_by_doc(epoch_doc,user,role)
    entity_list = []
    for index in range(len(doc_entity_annotation)):
        entity_id = doc_entity_annotation[index].id
        entity_template_id = doc_entity_annotation[index].entity_template_id
        the_entity_template = Entity_template.objects.filter(id=entity_template_id)
        entity_dict = {'id':entity_id,'start_offset':doc_entity_annotation[index].start_offset,'end_offset':doc_entity_annotation[index].end_offset,'content':doc_entity_annotation[index].content,'entity_template':the_entity_template[0].name}

        #查看是否存在standard
        standard = doc_entity_annotation[index].standard
        if standard is not None:
            entity_dict['standard'] = standard.standard_name

        #查看是否存在事件组
        event_group_annotation = doc_entity_annotation[index].event_group_annotation
        if event_group_annotation is not None:
            entity_dict['event_group'] = event_group_annotation.id

        entity_list.append(entity_dict)
    return entity_list

'''
@description: 下载标注结果，得到关系的标注结果
@param {type} 
@return: 
'''
def get_relation_annotation_list(epoch_doc, user, role):
    doc_relation_annotation = dao.get_relation_annotation_by_doc(epoch_doc,user,role)
    relation_list = []
    for index in range(len(doc_relation_annotation)):
        start_id = doc_relation_annotation[index].start_entity_id
        end_id = doc_relation_annotation[index].end_entity_id
        relation_id = doc_relation_annotation[index].relation_entity_template_id
        relation_entity_template = Relation_entity_template.objects.get(id=relation_id)
        relation = relation_entity_template.relation
        
        relation_dict = {'start_entity_id':start_id,'end_entity_id':end_id,'relation_template':relation.name}
        relation_list.append(relation_dict)
    return relation_list
'''
@description: 下载标注结果，得到事件的标注结果
@param {type} 
@return: 
'''
def get_event_group_annotation_list(epoch_doc, user, role):
    doc_event_group_annotation = dao.get_event_annotation_by_doc(epoch_doc, user, role)
    event_group_list = []
    for event_group_annotation in doc_event_group_annotation:
        dic = {}
        dic['event_group_annotation_id'] = event_group_annotation.id
        dic['event_group_template_name'] = event_group_annotation.event_group_template.name
        event_group_list.append(dic)
    return event_group_list
    
'''
@description: 下载标注结果，得到分类的标注结果
@param {type} 
@return: 
'''
def get_classification_annotation_list(epoch_doc, user, role):
    doc_classification_annotation = dao.get_classification_by_doc(epoch_doc, user, role)
    name = ''
    for doc_classification in doc_classification_annotation:
        name = doc_classification.classification_template.name 
    return name

'''
@description: 序列化事件组的答案数据
@param {type} 
@return: 
'''
def serialize_answer_event_group(event_group_template_name, epoch, doc):
    print(event_group_template_name, epoch, doc)
    event_group_dic = {}
    event_group_template = dao.get_event_group_template_by_name(event_group_template_name, epoch)
    role = Role.objects.get(name='annotator')
    event_group_dic['doc'] = doc.id
    event_group_dic['user'] = epoch.annotator.id
    event_group_dic['role'] = role.id
    event_group_dic['event_group_template'] = event_group_template.id
    return event_group_dic

'''
@description: 序列化分类的答案数据
@param {type} 
@return: 
'''
def serialize_answer_classification(classification_template, epoch, doc):
    classification_dic = {}
    role = Role.objects.get(name='annotator')
    classification_dic['doc'] = doc.id
    classification_dic['user'] = epoch.annotator.id
    classification_dic['role'] = role.id
    classification_dic['classification_template'] = classification_template.id
    return classification_dic

'''
@description: 输入实体模板,查询实体模板下是否存在standard_name的标准
@param {type} 
@return: 
'''
def has_standard_template_by_standard_name(entity_template, standard_name):
    standard = entity_template.standard.filter(standard_name=standard_name)
    return standard

'''
@description: 字典匹配,返回结果
@param {type} 
@return: 
'''
def dic_match(doc, dic_queryset, entity_template):
    content = doc.content
    entity_template_id = entity_template.id

    dic_dict = {}
    #把dic_queryset变成字典形式,key是字典名称,value也是dic
    for dic_item in dic_queryset:
        dic_content = dic_item.content
        standard = dic_item.standard
        dic_dict[dic_content] = standard

    dic_list = list(dic_dict.keys())

    #dic按照长度排序
    i,j = 0,0
    for i in range(len(dic_list)):
        temp_dic = dic_list[i]
        for j in range(i, -1, -1):
            if len(dic_list[j - 1]) < len(temp_dic):
                dic_list[j] = dic_list[j - 1]
            else:
                break
        dic_list[j] = temp_dic   

    match_list = []
    for dic in dic_list:
        #可能dic里面存在 正则符号,先转义再用finditer
        transfered_dic = transfer_dic(dic)
        re_result_list = re.finditer(transfered_dic, content)
        for re_result in re_result_list:
            start_offset, end_offset = re_result.span()

            #判断这个匹配结果和之前匹配结果是否存在重叠
            flag = True
            for match in match_list:
                ms = match['start_offset']
                me = match['end_offset']
                if start_offset >= me or end_offset < ms:
                    pass
                else:
                    flag = False
                    break
            #如果没有重叠则添加
            if flag:
                match_data = {'doc':doc.id, 'content':dic, "start_offset":start_offset, 'end_offset':end_offset, 'entity_template':entity_template_id, 'project':doc.project.id}
                if dic_dict[dic] is None:
                    match_data['standard'] = ''
                else:
                    match_data['standard'] = dic_dict[dic].id
                match_list.append(match_data)
    return match_list
                
'''
@description: 发现dic中的正则字符并转义
@param {type} 
@return: 
'''
def transfer_dic(dic):
    re_s = '* . ? + $ ^ [ ] ( ) { } | \ /'
    re_list = re_s.split()
    transferd_dic = ''
    for d in dic:
        if d in re_list:
            transferd_dic += '\\' + d
        else:
            transferd_dic += d
    return transferd_dic

'''
@description: 处理上传的正则文件,转化成serialized_data
@param {type} 
@return: 
'''
def validate_re(file_list, project):
    re_list = []
    #得到project下所有的queryset
    entity_template_query_set = dao.get_entity_template_by_project(project)

    #如果为空直接返回494
    if len(entity_template_query_set) == 0:
        return return_Response('error','the template of this project does not have any entity template',status.HTTP_404_NOT_FOUND)
        
    for f in file_list.getlist('file'):
        df = pd.read_excel(f)
        for index, row in df.iterrows():
            content = row['content']
            entity_name_list = row['entity_name'].split(',')
            #正确情况是 括号组数量=实体类型数量或者括号数量为0,实体类型数量为1, 其他都是错误情况
            bracket_number = validate_bracket_number(content)
            if not((bracket_number == len(entity_name_list)) or (bracket_number == 0 and len(entity_name_list) == 1)):
                return return_Response('error','the number of bracket is not equal to the number of entity_template',status.HTTP_404_NOT_FOUND)

            re_dict = validate_re_data(content, entity_name_list, project)
            re_list.append(re_dict)
    return re_list


'''
@description: 验证re的数据格式
@param {type} 
@return: 
'''
def validate_re_data(content, entity_name_list, project):
    re_dict = {}
    re_dict['project'] = project.id
    re_dict['content'] = content

    #得到project下所有的queryset
    entity_template_query_set = dao.get_entity_template_by_project(project)

    entity_template_list = []
    for entity_name in entity_name_list:
        entity_template = has_entity_template_by_entity_name(entity_template_query_set,entity_name)
        entity_template_list.append(entity_template)
    #如果没找到就读下一行, 如果有查看标准是否存在
    if entity_template is None:
        return return_Response('error', 'no entity_template called ' + entity_name, status.HTTP_400_BAD_REQUEST)
    
    re_dict['entity_template_list'] = [x.id for x in entity_template_list]
    return re_dict


'''
@description: re匹配doc并返回正确答案
@param {type} 
@return: 
'''
def re_match(doc, project, re_, entity_template_list):
    #最终返回的结果
    match_list = []

    doc_content = doc.content
    pattern = re_.content
    
    #finditer匹配
    result = re.finditer(pattern, doc_content)

    for item in result:
        #先得到匹配上的全文
        match_content =item.group()
        match_start, match_end = item.span()
        #有可能它正则里面没有括号,match_content就是匹配上的文字
        if len(item.groups()) == 0:
            #groups为零却匹配上说明整个正则属于没括号的，且只有一个entity_template
            entity_template = entity_template_list[0]
            match_data = {}
            match_data['project'] = project.id
            match_data['doc'] = doc.id
            match_data['content'] = match_content
            match_data['start_offset'] = match_start
            match_data['end_offset'] = match_end
            match_data['entity_template'] = entity_template['entity_template']
            match_list.append(match_data)
        else:
            #如果有多组匹配上，看是否和entity_template_list的长度相等
            if len(item.groups()) != len(entity_template_list):
                continue
            for group,entity_template in zip(item.groups(), entity_template_list):
                #对于多个括号，如果某个括号对应位置为空，匹配结果为None应跳过
                if group is not None:
                    match_data ={}
                    #找到group再当前match_content的index，进而得到再全文中的span
                    group_index = match_content.index(group)
                    group_start = match_start + group_index
                    group_end = group_start + len(group)
                    match_data['doc'] = doc.id
                    match_data['project'] = project.id
                    match_data['content'] = group
                    match_data['start_offset'] = group_start
                    match_data['end_offset'] = group_end
                    match_data['entity_template'] = entity_template['entity_template']
                    match_list.append(match_data)
    return match_list

'''
@description: 判断正则内容中括号的个数
@param {type} 
@return: 
'''
def validate_bracket_number(pattern):
    brakect_pattern = '\(.*?\)'
    brakect_result = re.findall(brakect_pattern, pattern)
    return len(brakect_result)
    
'''
@description: 存正则以及和entity_template的数据,因为是manytomany,需要分开存储
@param {type} 
@return: 
'''
def save_re_and_entity_template(serialize_re_data):
    save_data_list = []
    #保存成功存储的data_list,并返回给前台
    for re_data in serialize_re_data:
        entity_template_list = re_data.pop('entity_template_list')
        serializer = ReSerializer(data=re_data)
        if serializer.is_valid():
            # try:
            #加一个事务
            with transaction.atomic():
                #加一个存储的事务锁
                re_ = serializer.save()
                #添加该re和entity_template的关系
                re_data['entity_template_list'] = []
                save_data = update_re_entity_template(re_, entity_template_list, re_data)
                if isinstance(save_data, bool):
                    return return_Response('error','invalid data!',status.HTTP_400_BAD_REQUEST)
                else:
                    save_data_list.append(save_data)
            # except Exception as e:
            #     return Response(str(e),status=status.HTTP_400_BAD_REQUEST)
        else:
            print(re_data)
            return return_Response('error','invalid re data!',status.HTTP_400_BAD_REQUEST)
    
    return save_data_list

'''
@description: 给正则表达式添加entity_tempalte
@param {type} 
@return: 
'''
def update_re_entity_template(re_, entity_template_list, save_data):
    print(re_)
    for index,entity_template_id in enumerate(entity_template_list):
        entity_template = Entity_template.objects.get(pk=entity_template_id)
        re_entity_tempalte_serialize_data = {}
        re_entity_tempalte_serialize_data['re'] = re_.id
        re_entity_tempalte_serialize_data['entity_template'] = entity_template.id
        re_entity_tempalte_serialize_data['order'] = index + 1

        re_entity_template_serializer = ReEntityTemplateSerializer(data=re_entity_tempalte_serialize_data)

        if re_entity_template_serializer.is_valid():
            print('re_entity_template data is valid')
            re_entity_template_serializer.save()
        else:
            print('invalid' + str(re_entity_tempalte_serialize_data))
            print(re_entity_template_serializer.errors)
            return False


        #每成功一个添加entity_template的信息
        save_data['entity_template_list'].append({'entity_template_id':entity_template.id, 'entity_template_name':entity_template.name, 'order':index+1})
    return save_data