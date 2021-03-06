import requests

from django.conf import settings
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from allthatbank.utils.auth import Authentication
from common.response import response_data
from user.models import User
from user.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserList(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(response_data(True, serializer.data))
        else:
            try:
                User.objects.get(username=request.data['username'])
                return Response(response_data(False, serializer.errors), status=status.HTTP_409_CONFLICT)
            except User.DoesNotExist:
                return Response(response_data(False, serializer.errors))

    def get(self, request):
        qs = User.objects.all()
        serializer = UserSerializer(qs, many=True)
        return Response(response_data(True, serializer.data))


class UserDetail(APIView):
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(response_data(True, serializer.data))

    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(response_data(True, serializer.data))
        else:
            return Response(response_data(False, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DebugLocalToken(APIView):
    def post(self, request):
        token = request.data['x-access-token']
        secret = settings.SECRET_KEY
        data = Authentication().validate_token(token, secret)
        if type(data) is not dict:
            data = {'error': data}
        return Response(response_data(True, data))


class DebugFbToken(APIView):
    def post(self, request):
        user_token = request.data['token']
        res = self.debug_token(user_token)
        sns_id = res['data']['user_id']
        try:
            user = User.objects.get(sns_type='facebook', sns_id=sns_id)
            # token 갱신
            data = {'sns_access_token': user_token}
            serializer = UserSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(response_data(True, serializer.data))
            else:
                return Response(response_data(False, 'FB 토큰 갱신 에러'))
        except User.DoesNotExist:
            return Response(response_data(True, None))

    def debug_token(self, user_token):
        url = 'https://graph.facebook.com/debug_token'
        app_token = '|'.join([settings.FB_APP_ID, settings.FB_APP_SECRET])
        params = {'input_token': user_token, 'access_token': app_token}

        res = requests.get(url, params).json()
        return res


class SignIn(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        token = User.authentication(username, password)
        if token is None:
            return Response(response_data(False, '로그인 실패'), status=status.HTTP_401_UNAUTHORIZED)
        else:
            data = {'x_access_token': token}
        return Response(response_data(True, data))
