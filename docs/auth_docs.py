from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@swagger_auto_schema(
    method='post',
    operation_summary="Log in to the system",
    operation_description="Use username and password to receive access and refresh tokens. These tokens are required to access protected endpoints.",
    tags=["Authentication"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Your username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Your password'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login successful. Returns access and refresh tokens.",
            examples={
                "application/json": {
                    "access": "<JWT_ACCESS_TOKEN>",
                    "refresh": "<JWT_REFRESH_TOKEN>"
                }
            }
        ),
        401: "Unauthorized – invalid credentials"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_doc_view(request):
    return Response({'detail': 'This is just for documentation purposes.'})
