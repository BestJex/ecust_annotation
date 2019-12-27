'''
@Author: liangming
@Date: 2019-12-27 00:27:40
@LastEditTime : 2019-12-27 00:37:51
@LastEditors  : Please set LastEditors
@Description: 复杂查询接口
@FilePath: /ecust_annotation/api/dao.py
'''
from api.models import *

def get_entity_template_by_project(project):
    entity_template_query_set = project.template.entity_group_template.all()
    entity_template = None

    for entity_group in entity_template_query_set:
        entity_template = entity_group.entity_template.all() if entity_template is None else entity_template.union(entity_group.entity_template.all(),all=True)
        
    return entity_template