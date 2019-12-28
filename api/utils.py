'''
@Author: liangming
@Date: 2019-12-26 08:28:23
@LastEditTime : 2019-12-28 08:37:20
@LastEditors  : Please set LastEditors
@Description: 各种工具方法
@FilePath: /ecust_annotation/api/utils.py
'''
import chardet
from rest_framework.response import Response
from rest_framework import status
from api.models import *
from api import dao
from django.shortcuts import get_object_or_404
import math
import random

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
    for epoch_num in range(total_epoches):
        for annotator in annotators:
            data = {}
            data['num'] = epoch_num + 1
            data['re_annotate_num'] = 0
            data['project'] = project.id
            data['reviewer'] = reviewers[epoch_num%len(reviewers)].id
            data['annotator'] = annotator.id
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

