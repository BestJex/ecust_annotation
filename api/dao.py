'''
@Author: liangming
@Date: 2019-12-27 00:27:40
<<<<<<< HEAD
@LastEditTime: 2020-03-03 21:35:50
@LastEditors: Please set LastEditors
=======
@LastEditTime : 2020-01-03 06:46:42
@LastEditors  : Please set LastEditors
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
@Description: 复杂查询接口
@FilePath: /ecust_annotation/api/dao.py
'''
from api.models import *
from django.db.models.query import QuerySet

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
     doc.epoch.add(epoch)

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

'''
@description: 查询这个epoch下的ann_allocation对象
@param {type} 
@return: 
'''
def get_ann_allocation_by_epoch(epoch):
    epoch_docs = epoch.doc.all()
    return Annotate_allocation.objects.filter(annotator=epoch.annotator).filter(doc__in=epoch_docs)

'''
<<<<<<< HEAD
@description: 查询这个epoch对应的epoch_num下的的revew_allocation对象
=======
@description: 查询这个epoch下的revew_allocation对象
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
@param {type} 
@return: 
'''
def get_review_allocation_by_epoch(epoch):
<<<<<<< HEAD
    epoch_num = epoch.num
    project = epoch.project
    epoch_list = Epoch.objects.filter(project=project).filter(num=epoch_num)
    print(epoch_list)
    epoch_docs = get_doc_by_epoch(epoch_list)
=======
    epoch_docs = epoch.doc.all()
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
    return Review_allocation.objects.filter(reviewer=epoch.reviewer).filter(doc__in=epoch_docs)

'''
@description: 查询project的所有epoch
@param {type} 
@return: 
'''
def get_epoch_by_project(project):
    return project.epoch

'''
@description: 查询annotator的所有epoch,排除undo状态的
@param {type} 
@return: 
'''
def get_epoch_by_annotator(annotator):
    return Epoch.objects.filter(annotator=annotator).exclude(state='UNDO')

'''
@description: 查询reviewer处于reviewing和finish的epoch
@param {type} 
@return: 
'''
def get_epoch_by_reviewer(reviewer):
    return Epoch.objects.filter(reviewer=reviewer).filter(state__in=['REVIEWING','FINISH'])

'''
@description: 根据doc返回annotation的type
@param {type} 
@return: 
'''
def get_annotation_type_by_doc(doc):
    return doc.project.template.template_type

'''
@description: 根据doc和user返回entity_annotation结果
@param {type} 
@return: 
'''
def get_entity_annotation_by_doc(doc,user,role):
    return Entity_annotation.objects.filter(doc=doc).filter(user=user).filter(role=role)

'''
@description: 根据doc user和role返回relation_entity_annotation的结果
@param {type} 
@return: 
'''
def get_relation_annotation_by_doc(doc,user,role):
    return Relation_annotation.objects.filter(doc=doc).filter(user=user).filter(role=role)

'''
@description: 根据doc user role返回classification的结果
@param {type} 
@return: 
'''
def get_classification_by_doc(doc,user,role):
    return Classification_annotation.objects.filter(doc=doc).filter(user=user).filter(role=role)

'''
@description: 根据doc user role返回event结果
@param {type} 
@return: 
'''
def get_event_annotation_by_doc(doc,user,role):
    return Event_group_annotation.objects.filter(doc=doc).filter(user=user).filter(role=role)

'''
@description: 更新annotation_allocation的状态
@param {type} 
@return: 
'''
def update_annotation_allocation_state(annotate_allocation,state):
    if isinstance(annotate_allocation,QuerySet):
        for item in annotate_allocation:
            item.state = state
            item.save()
    else:
        annotate_allocation.state = state
        annotate_allocation.save()

'''
@description: 获取该user在该doc下的annotation_allocation
@param {type} 
@return: 
'''
def get_annotation_allocation_by_doc_user(doc,user):
    ann_allocation = Annotate_allocation.objects.filter(doc=doc).filter(annotator=user)
    return ann_allocation


'''
@description: 查询该doc、该user该role下的epoch
@param {type} 
@return: 
'''
def get_epoch_of_annotator_by_doc(doc,user,role):
    #首先找到该doc和user对应的epoch
    if role.name == 'annotator':
        epoch = doc.epoch.all().filter(annotator=user)[0]
    else:
        epoch = doc.epoch.all().filter(reviewer=user)
    return epoch

'''
@description: 更新epoch的状态，可能是一组epoch
@param {type} 
@return: 
'''
def update_epoch_state(epoch,state):
    if not isinstance(epoch,QuerySet):
        epoch.state = state
        epoch.save()
    else:
        for item in epoch:
            item.state = state
            item.save()        

'''
@description: 查询该doc所在epoch_num的epoch
@param {type} 
@return: 
'''
def get_epoch_by_doc(doc):
    doc_epoch = doc.epoch.all()[0]
    project = doc_epoch.project
    epoch_num = doc_epoch.num
    return Epoch.objects.filter(project=project).filter(num=epoch_num)

'''
@description: 得到该doc对应Epoch中处于waiting状态的epoch
@param {type} 
@return: 
'''
def get_waiting_epoch(doc):
<<<<<<< HEAD
    return get_epoch_by_doc(doc).filter(state='WAITING')
=======
    return doc.epoch.all().filter(state='WAITING')
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664

'''
@description: 查询doc的project
@param {type} 
@return: 
'''
def get_project_by_doc(doc):
    return doc.project

'''
@description: 判断该doc所属的epoch是否为该project的最后一个epoch
@param {type} 
@return: 
'''
def is_last_epoch(project,doc):
    epoch_num = doc.epoch.all()[0].num
    total_epoch_num = get_total_epoch_num_by_project(project)
    return True if epoch_num == total_epoch_num else False

'''
@description: 查询project的总epoch数
@param {type} 
@return: 
'''
def get_total_epoch_num_by_project(project):
    return Epoch.objects.filter(project=project).order_by('-num')[0].num

'''
@description: 输入project的epoch_num下的所有epoch，返回该epoch_num下所有分配的doc
@param {type} 
@return: 
'''
def get_doc_by_epoch(epoches):
    if isinstance(epoches,QuerySet):
        return Doc.objects.filter(epoch__in=epoches).distinct()
    else:
        return Doc.objects.filter(epoch=epoches)

'''
<<<<<<< HEAD
@description: 输入doc查询两个标注者对其的标注结果，要根据annotation_type查询不同的东西
@param {type} 
@return: 
'''
def get_annotation_of_doc(doc,annotation_type):
=======
@description: 输入doc查询两个标注者对其的标注结果
@param {type} 
@return: 
'''
def get_annotation_of_doc(doc):
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
    #查询该doc对应的两个epoch，对应两个annotator
    doc_epoch = doc.epoch.all()
    annotator_one = doc_epoch[0].annotator
    annotator_two = doc_epoch[1].annotator

<<<<<<< HEAD
    annotation_one,annotation_two = {},{}
    if annotation_type == 'NER':
        #查询annotator_one的标注结果
        annotation_one['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_two)
    elif annotation_type == 'RE':
        #查询annotator_one的标注结果
        annotation_one['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_two)
        annotation_one['relation'] = Relation_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['relation'] = Relation_annotation.objects.filter(doc=doc).filter(user=annotator_two)
    elif annotation_type == 'CLASSIFICATION':
        annotation_one['classification'] = Classification_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['classification'] = Classification_annotation.objects.filter(doc=doc).filter(user=annotator_two)
    else:
        annotation_one['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['entity'] = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_two)
        annotation_one['event'] = Event_group_annotation.objects.filter(doc=doc).filter(user=annotator_one)
        annotation_two['event'] = Event_group_annotation.objects.filter(doc=doc).filter(user=annotator_two)

=======
    #查询annotator_one的标注结果
    annotation_one = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_one)
    annotation_two = Entity_annotation.objects.filter(doc=doc).filter(user=annotator_two)
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
    return annotation_one,annotation_two

'''
@description: 查询该doc所对应的epoch
@param {type} 
@return: 
'''
def get_doc_epoch(doc):
    return doc.epoch.all()


'''
@description: 更新epoch的re_annotate_num
@param {type} 
@return: 
'''
def update_epoch_re_annotate_num(epoch,re_annotate_num):
<<<<<<< HEAD
    epoch.re_annotate_num = re_annotate_num
'''
@description: 
@param {type} 查询reviewer在epoch_num下的所有doc
@return: 
'''
def get_reviewer_epoch_doc(epoch):
    epoch_num = epoch.num
    project = epoch.project
    epoch_list = Epoch.objects.filter(num=epoch_num).filter(project=project)
    return get_doc_by_epoch(epoch_list)

'''
@description: 根据doc查询project的类型
@param {type} 
@return: 
'''
def get_project_type_by_doc(doc):
    return doc.project.template.template_type
=======
    epoch.re_annotate_num = re_annotate_num
>>>>>>> 4db9a43a35352092df80178a27ac7553373b9664
