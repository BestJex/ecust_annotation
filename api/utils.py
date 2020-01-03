'''
@Author: liangming
@Date: 2019-12-26 08:28:23
@LastEditTime : 2020-01-03 06:36:54
@LastEditors  : Please set LastEditors
@Description: 各种工具方法
@FilePath: /ecust_annotation/api/utils.py
'''
import chardet
from rest_framework.response import Response
from rest_framework import status
from api.models import *
from api.serializer import *
from api import dao
from django.shortcuts import get_object_or_404
import math
import random
from api import consistency

'''
@description: 验证上传文件是否符合要求，读取所有的文件，并保存在一个list中返回
@param {file} 
@return: file中每行的list，如果出错，返回报错信息
'''
def validate_files(files,ann_num_per_epoch):
    docs = []
    #迭代每个文件
    for f in files.getlist('file'):
        #迭代文件中的每一行
        for line in f:
            #如果不为utf-8则跳过改行
            if chardet.detect(line)['encoding'] not in ['utf-8','ascii']:
                continue 
            doc_line = line.decode('utf-8').strip().replace('\r','').replace('\n','')
            #如果该行为空
            if doc_line == "":
                continue
            docs.append(doc_line)

    #如果没有上传文件或者文件格式不正确，报错
    if len(docs) == 0:
        return return_Response('error','not valid file format!',status.HTTP_400_BAD_REQUEST)

    #如果传ann_num_per_epoch,报错
    if ann_num_per_epoch == '':
        return return_Response('error','ann_num_per_epoch could not be null',status.HTTP_400_BAD_REQUEST)

    if int(ann_num_per_epoch) > len(docs) or int(ann_num_per_epoch) < 1:
        return return_Response('error','ann_num_per_epoch is bigger than the whole doc',status.HTTP_400_BAD_REQUEST)

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
def validate_dic(file,project_id):
    dic = []
    project = get_object_or_404(Project,pk=project_id)
    #得到project下所有的queryset
    entity_template_query_set = dao.get_entity_template_by_project(project)

    #如果为空直接返回494
    if len(entity_template_query_set) == 0:
        return return_Response('error','the template of this project does not have any entity template',status.HTTP_404_NOT_FOUND)
        
    for line in file:
        #如果不为utf-8则跳过改行
        encoding = chardet.detect(line)['encoding']
        if encoding not in ['utf-8','ascii']:
            continue 
        dic_line = line.decode('utf-8').strip().replace('\r','').replace('\n','')
        #如果该行为空
        if dic_line == "":
            continue
        dic_arr = dic_line.split('\t')
        content,entity_name = dic_arr[0],dic_arr[1]
        #看entity_name是否在entity_list中
        entity_template = has_entity_template_by_entity_name(entity_template_query_set,entity_name)
        #如果没找到就读下一行
        if entity_template is None:
            continue
        dic.append({'project':project_id,'content':content,'entity_template':entity_template.id})

    if len(dic) == 0:
        return return_Response('error','no valid data in uploaded dic file! may be input wrong entity name',status.HTTP_400_BAD_REQUEST)
    
    return dic

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

            #如果是第一个epoch，state改为ANNOTATING
            if epoch_num == 0:
                data['state'] = 'ANNOTATING'
            serialize_data.append(data)
            print(data,'\n')
    return serialize_data,total_epoches

'''
@description: 分配ann_allocation和review_allocation
@param {type} 
@return: 
'''
def get_annotation_review_allocation(project,total_allocate_epoch,annotators,reviewers):
    for epoch_num in range(total_allocate_epoch):
        #获得该epoch_num的所有epoch（每个annotator一个）
        epoches = dao.get_epoch_by_num_and_project(epoch_num+1,project)

        #获取待分配的doc，其中地雷任务会返回全部
        docs = get_random_unallocated_docs_by_project(project)

        #对每一条文本进行分配,每一个doc分配两个annotator一个reviewer
        #即每个doc分配和两个epoch做分配
        for doc_index in range(2*len(docs)):
            doc = docs[doc_index//2]
            epoch = epoches[doc_index%len(epoches)]

            #更新doc的epoch
            dao.update_doc_epoch(doc,epoch)

            #创建annotation_allocation
            dao.create_annotation_allocation(doc,epoch)

            #每一个doc两个annotator一个reviewer
            if doc_index%2 == 0:
                dao.create_review_allocation(doc,epoch)
            


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
            data_item['state'] = epoch_data['state']
            data_item['annotators'] = []
            data_item['reviewers'] = {'reviewer':epoch_data['reviewer'],'progress':epoch_data['review_progress']}
            data.append(data_item)
        data_item['annotators'].append({'annotator':epoch_data['annotator'],'progress':epoch_data['annotate_progress']})
    return data

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
    return serializer.data

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
    epoch = doc.epoch.all().filter(state__in=['WAITING','FINISH'])

    #查询doc对应proejct的epoch的总数
    return True if len(epoch) == len(dao.get_epoch_by_doc(doc)) else False

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
    
    fields = ['start_offset','end_offset','content','entity_template','user']
    for doc in doces:
        annotation_data = {}
        annotation_data['doc_id'] = doc.pk
        annotation_data['content'] = doc.content
        #查询每一条doc对应的标注
        annotation_one,annotation_two = dao.get_annotation_of_doc(doc)
        annotation_data['annotation_one'] = EntityAnnotationSerializer(annotation_one,fields=fields,many=True).data
        annotation_data['annotation_two'] = EntityAnnotationSerializer(annotation_two,fields=fields,many=True).data
        annotation_data_list.append(annotation_data)
    print(annotation_data_list)
    #进行一致性校验,consistency_result应该为一个list，里面记录需要重新标注的doc_id
    c = consistency.Consistency(annotation_data_list)
    consistency_result = c.refusedDocList(accept=0.9)
    
    #真实应该返回consistency_result
    return consistency_result

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