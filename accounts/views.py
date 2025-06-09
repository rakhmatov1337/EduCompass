from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import UserCreateSerializer
from rest_framework import generics, status
from rest_framework import generics, permissions
from .serializers import MyCourseSerializer
from main.models import Enrollment
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from django.db.models import Count, Prefetch
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model


from .serializers import EduCenterCreateSerializer, BranchCreateSerializer, UserSerializer
from .permissions import IsEduCenterOrReadOnly, IsSuperUser
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
    """
    GET (list/retrieve):   hammaga (shu jumladan student/anonim) ochiq.
    POST/PUT/PATCH/DELETE:  faqat EDU_CENTER.
    """
    queryset = Branch.objects.all()
    serializer_class = BranchCreateSerializer
    permission_classes = [IsEduCenterOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Edu center admini o‘z markazi filiallarini boshqaradi:
        if user.is_authenticated and user.role == 'EDU_CENTER':
            return qs.filter(edu_center__user=user)
        # STUDENT/BRANCH/anonim: barcha filiallarni list qiladi
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        ec = EducationCenter.objects.filter(user=user).first()
        if not ec:
            raise PermissionDenied(
                "Sizga biriktirilgan Education Center mavjud emas.")
        serializer.save(edu_center=ec)


class MyCoursesView(generics.ListAPIView):
    serializer_class = MyCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related('course__level').prefetch_related('course__days')


class RegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user_data = response.data
        user = User.objects.get(pk=user_data['id'])
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "user":    user_data,
                "access":  access_token,
                "refresh": refresh_token
            },
            status=status.HTTP_201_CREATED
        )


class CurrentUserRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
