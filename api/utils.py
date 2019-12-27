'''
@Author: liangming
@Date: 2019-12-26 08:28:23
@LastEditTime : 2019-12-27 01:29:45
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
            if chardet.detect(line)['encoding'] != 'utf-8':
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
        