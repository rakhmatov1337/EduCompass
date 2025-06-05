from rest_framework import generics, permissions
from .serializers import MyCourseSerializer
from main.models import Enrollment
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from django.db.models import Count, Prefetch
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model


from .serializers import EduCenterCreateSerializer, BranchCreateSerializer
from .permissions import IsEduCenter, IsSuperUser
from main.models import EducationCenter, Branch, Like, View, Course
from api.serializers import LikeSerializer, ViewSerializer, EducationCenterSerializer
from api.paginations import DefaultPagination

User = get_user_model()


class EduCenterViewSet(ReadOnlyModelViewSet):
    serializer_class = EducationCenterSerializer
    pagination_class = DefaultPagination

    queryset = (
        EducationCenter.objects
        .filter(active=True)
        .annotate(
            likes_count=Count('likes', distinct=True),
            views_count=Count('views', distinct=True)
        )
        .prefetch_related(
            'edu_type',
            Prefetch('branches', queryset=Branch.objects.prefetch_related(
                Prefetch(
                    'courses', queryset=Course.objects.select_related('category'))
            ))
        )
    )


class EduCenterCreateView(CreateAPIView):
    serializer_class = EduCenterCreateSerializer
    permission_classes = [IsSuperUser]


class LikeViewSet(ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Like.objects.none()

        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(EducationCenter),
            object_id=self.kwargs['edu_center_pk']
        )

    def create(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):
            return Response({"detail": "Fake view for schema generation."})

        edu_center = get_object_or_404(
            EducationCenter, pk=self.kwargs['edu_center_pk'])
        content_type = ContentType.objects.get_for_model(EducationCenter)

        existing_like = Like.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=edu_center.id
        ).first()

        if existing_like:
            existing_like.delete()
            return Response({"liked": False, "message": "Like removed."})

        like = Like.objects.create(
            user=request.user,
            content_object=edu_center
        )
        serializer = self.get_serializer(like)
        return Response({"liked": True, "data": serializer.data})


class ViewViewSet(ModelViewSet):
    serializer_class = ViewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return View.objects.none()

        return View.objects.filter(
            content_type=ContentType.objects.get_for_model(EducationCenter),
            object_id=self.kwargs['edu_center_pk']
        )

    def perform_create(self, serializer):
        if getattr(self, 'swagger_fake_view', False):
            return

        edu_center = get_object_or_404(
            EducationCenter, pk=self.kwargs['edu_center_pk'])
        serializer.save(user=self.request.user, content_object=edu_center)


class BranchViewSet(ModelViewSet):
    serializer_class = BranchCreateSerializer
    permission_classes = [IsEduCenter]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'EDU_CENTER':
            edu_center = EducationCenter.objects.filter(user=user).first()
            if edu_center:
                return Branch.objects.filter(edu_center=edu_center)
        return Branch.objects.none()

    def perform_create(self, serializer):
        edu_center = EducationCenter.objects.filter(
            user=self.request.user).first()
        if not edu_center:
            raise PermissionDenied(
                "Sizga biriktirilgan Education Center mavjud emas.")
        serializer.save(edu_center=edu_center)


class MyCoursesView(generics.ListAPIView):
    serializer_class = MyCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related('course__level').prefetch_related('course__days')


