'''
@Author: your name
@Date: 2019-12-22 04:13:58
@LastEditTime : 2019-12-27 05:59:02
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
]