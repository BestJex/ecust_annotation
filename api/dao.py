'''
@Author: liangming
@Date: 2019-12-27 00:27:40
@LastEditTime : 2019-12-28 08:38:33
@LastEditors  : Please set LastEditors
@Description: 复杂查询接口
@FilePath: /ecust_annotation/api/dao.py
'''
from api.models import *

'''
@description: 根据project得到对应template的entity_template
@param {type} 
@return: 
'''
def get_entity_template_by_project(project):
    entity_template_query_set = project.template.entity_group_template.all()
    entity_template = None

    for entity_group in entity_template_query_set:
        entity_template = entity_group.entity_template.all() if entity_template is None else entity_template.union(entity_group.entity_template.all(),all=True)
        
    return entity_template


'''
@description: 查询一个project的总的文本数量
@param {type} 
@return: 
'''
def get_doc_num_by_project(project):
    return len(project.doc.all())    


'''
@description: 根据epoch_num和project找到对应的epoch
@param {type} 
@return: 
'''
def get_epoch_by_num_and_project(epoch_num,project):
    return Epoch.objects.filter(project=project.id).filter(num=epoch_num)

'''
@description: 根据project返回没有分配的docs
@param {type} 
@return: 
'''
def get_unallocated_docs_by_project(project):
    return Doc.objects.filter(project=project).filter(epoch=None)

'''
@description: 更新doc的epoch
@param {type} 
@return: 
'''
def update_doc_epoch(doc,epoch):
     doc.epoch = epoch
     doc.save()

'''
@description:  分配annotation的allocation
@param {type} 
@return: 
'''
def create_annotation_allocation(doc,epoch):
    ann_allocation = Annotate_allocation(doc=doc,annotator=epoch.annotator)
    ann_allocation.save()


'''
@description: 新建review——allcation
@param {type} 
@return: 
'''
def create_review_allocation(doc,epoch):
    review_allocation = Review_allocation(doc=doc,reviewer=epoch.reviewer)
    review_allocation.save()