'''
@Author: your name
@Date: 2019-12-23 01:12:33
@LastEditTime : 2019-12-23 01:24:42
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /ecust_annotation/api/tests.py
'''
from django.test import TestCase
# Create your tests here.
data = '''{
    "name": "ner_template",
    "template_type": "NER",
    "entity_group_template": [
        {
            "name": "suspect",
            "entity_template": [
                {
                    "name": "suspect_name",
                    "color": "#ffffff"
                },
                {
                    "name": "suspect_sex",
                    "color": "#fffddf"
                }
            ]
        }
    ]
}'''

data ="""{'name': 'ner_template', 'template_type': 'NER', 'entity_group_template': [OrderedDict([('name', 'suspect'), ('entity_template', [OrderedDict([('name', 'suspect_name'), ('color', '#ffffff')]), OrderedDict([('name', 'suspect_sex'), ('color', '#fffddf')])])])]}"""