'''
@Author: meloming
@Date: 2019-12-22 04:04:59
@LastEditTime : 2020-01-03 03:04:22
@LastEditors  : Please set LastEditors
@Description: used for authentication
@FilePath: /ecust_annotation/api/authentication.py
'''
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from api.serializer import RoleSerializer
from api import utils

'''
@description: to return custom token when the request has been authorized
@param {type} 
@return: {
    "user_id": 1,
    "token": "e41b8abd408e5266f4e240de8949b21988277e9c",
    "user_role": [
        {
            "name": "admin"
        },
        {
            "name": "annotator"
        },
        {
            "name": "reviewer"
        }
    ]
}
'''
class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token,_ = Token.objects.get_or_create(user=user)

        #serialize role list of a user
        role_serializer = RoleSerializer(user.role,many=True)
        role_list = utils.serialize_user_role(role_serializer.data)
        
        return Response({
            'user_id': user.pk,
            'token': token.key,
            'roles': role_list
        })