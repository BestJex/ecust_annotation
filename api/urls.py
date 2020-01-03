'''
@Author: your name
@Date: 2019-12-22 04:13:58
@LastEditTime : 2020-01-03 04:06:45
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/urls.py
'''
from django.contrib import admin
from django.urls import path
from api.authentication import CustomAuthToken
from api.views import *

app_name="api"

urlpatterns = [
    path('auth_token/',CustomAuthToken.as_view()),
    path('roles/',RoleList().as_view()),
    path('templates/',TemplateList.as_view(),name='templates'),
    path('templates/<int:pk>/',TemplateDetail.as_view(),name='template-detail'),
    path('templates/<int:pk>/<str:templateclass>/',TemplateClassList.as_view(),name='template-class'),
    path('templates/relations/<int:relationid>/entitys/',RelationEntityList.as_view(),name='relation-entitys'),
    path('templates/<str:templateclass>/<int:templateclassid>/entitys/',EntityTemplateList.as_view(),name='template-class-entitys'),
    path('projects/',ProjectList.as_view(),name='projects'),
    path('projects/<int:projectid>/',ProjectDetail.as_view(),name='project-detail'),  
    path('projects/<int:projectid>/docs/',ProjectDoc.as_view(),name='project-doc'),
    path('projects/<int:projectid>/dics/',ProjectDic.as_view(),name='project-dic'),
    path('projects/<int:projectid>/epoches/',ProjectEpoch.as_view(),name='project-epoch'),
    path('annotators/<int:annotatorid>/epoches/',AnnotatorEpoch.as_view(),name='annotator-epoch'),
    path('reviewers/<int:reviewerid>/epoches/',ReviewerEpoch.as_view(),name='reviewer-epoch'),
    path('projects/epoches/<int:epochid>/docs/',EpochDoc.as_view(),name='epoch-doc'),
    path('projects/docs/<int:docid>/<str:role>/<int:userid>/annotations/',AnnotationList.as_view(),name='annotation'),
    path('projects/docs/<int:docid>/annotations/entities/',AnnotationEntity.as_view(),name='annotation-entity'),
    path('projects/docs/<int:docid>/annotations/relations/',AnnotationRelation.as_view(),name='annotation-reltaion'),
    path('projects/docs/<int:docid>/annotations/events/',AnnotationEvent.as_view(),name='annotation-event'),
    path('projects/docs/<int:docid>/annotations/classifications/',AnotationClassification.as_view(),name='annotation-classification'),
    path('projects/docs/<int:docid>/annotations/confirmations/',AnnotationConfirmation.as_view(),name='annotation-confitmation')            
]