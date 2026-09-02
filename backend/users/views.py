from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .models import Follow
from .serializers import UserSerializer, SubscriptionSerializer, AvatarSerializer

User = get_user_model()


class SubscriptionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = SubscriptionSerializer

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Follow.objects.filter(user=user, following=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Follow.objects.create(user=user, following=author)
            serializer = SubscriptionSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            follow = Follow.objects.filter(user=user, following=author)
            if follow.exists():
                follow.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": "Вы не подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def subscriptions(self, request):
        queryset = User.objects.filter(followers__user=request.user).order_by("-id")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar(self, request):

        if request.method == "PUT":
            serializer = AvatarSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            avatar_data = serializer.validated_data.get("avatar")

            if request.user.avatar:
                request.user.avatar.delete(save=False)

            request.user.avatar = avatar_data
            request.user.save(update_fields=["avatar"])

            avatar_url = request.build_absolute_uri(request.user.avatar.url)

            return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            user = request.user

            if not user.avatar:
                return Response(
                    {"detail": "У пользователя нет аватара для удаления"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=["avatar"])

            return Response(status=status.HTTP_204_NO_CONTENT)
