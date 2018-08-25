from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from board.models import Post
from board.serializers import PostSerializer
from common.paging import paging_data
from common.response import response_data
from user.models import User


class PostListAPIView(APIView):
    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(response_data(True, serializer.data))
        else:
            return Response(response_data(False, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        limit = request.query_params.get('limit', 10)
        page = request.query_params.get('page', 1)

        qs = paging_data(Post.objects.all(), limit, page)
        serializer = PostSerializer(qs, many=True)
        return Response(response_data(True, serializer.data))


class PostDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        free = self.get_object(pk)
        serializer = PostSerializer(free)
        return Response(response_data(True, serializer.data))

    def put(self, request, pk):
        free = self.get_object(pk)
        serializer = PostSerializer(free, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(response_data(True, serializer.data))
        else:
            return Response(response_data(False, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        free = self.get_object(pk)
        free.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
