from django.contrib.auth import get_user_model, password_validation
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.db.models import Q
from django.utils import timezone
from django.http import Http404
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.compat import coreapi, coreschema
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema
from rest_framework.schemas import coreapi as coreapi_schema


from allauth.socialaccount.providers.facebook.views import (
    FacebookOAuth2Adapter,
)
from rest_auth.registration.views import SocialLoginView

from dry_rest_permissions.generics import (
    DRYPermissions, DRYPermissionFiltersBase
)

from .models import APIToken
from .serializers import SingleAPITokenSerializer, MultipleAPITokenSerializer
from api_volontaria import permissions
# from .models import APIToken
from . import serializers

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given user.

    list:
    Return a list of all existing users.

    create:
    Create a new user instance.

    update:
    Update fields of a user instance.

    delete:
    Sets the user inactive.
    """
    queryset = User.objects.all()
    filter_fields = '__all__'

    def get_serializer_class(self):
        if (self.action == 'update') | (self.action == 'partial_update'):
            return serializers.UserUpdateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        if self.kwargs.get("pk", "") == "me":
            self.kwargs['pk'] = user.id
        return queryset

    def get_permissions(self):
        """
        Returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = []
        elif self.action == 'list':
            permission_classes = [IsAdminUser, ]
        else:
            permission_classes = [
                IsAuthenticated,
                permissions.IsOwner
            ]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super().retrieve(request, *args, **kwargs)
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            raise PermissionDenied

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.is_active = False
            instance.save()
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

# class APITokenBackend(DRYPermissionFiltersBase):
#     ''' Class used to limit the API tokens 
#     a simple user can retrieve in a list request
#     to its own API tokens
#     '''
#     def filter_list_queryset(self, request, queryset, view):
#         """
#         Limits all list requests to only be seen by the staff or owner.
#         """
#         if request.user.is_staff:
#             return queryset
#         else:
#             return queryset.filter(user=request.user)


class SingleAPITokenViewSet(viewsets.GenericViewSet,
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin):

    ''' This class is strongly inspired from ObtainAuthToken in Django Rest Framework
    Some differences are in the post function:
    - the post function has been modified to allow:
        - creating multiple tokens by a single user
        - specifying to which purpose the token relates
    TODO: - a get function has been added to allow user to retrieve:
        - a list of their tokens
        - the token related to a given purpose  
    '''
    serializer_class = SingleAPITokenSerializer
    permission_classes = (DRYPermissions,)
    
    queryset = APIToken.objects.all()
    filter_fields = ['purpose', 'user', 'created']
    
    # filter_backends = (APITokenBackend,)

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         permission_classes = []
    #     else:
    #         permission_classes = [IsAdminUser]

    #     return [permission() for permission in permission_classes]

    # def get_queryset(self):
    #     if self.request.user.is_staff:
    #         return APIToken.objects.all()
    #     else:
    #         return APIToken.objects.filter(user=self.request.user)

    if coreapi_schema.is_enabled():
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="email",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Email",
                        description="Valid email associated with an active user",
                    ),
                ),
                coreapi.Field(
                    name="purpose",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Purpose",
                        description="Service to be associated with the API Token",
                    ),
                ),
            ],
            encoding="application/json",
        )

    # def get_serializer_context(self):
    #     return {
    #         'request': self.request,
    #         'format': self.format_kwarg,
    #         'view': self
    #     }

    # def get_serializer(self, *args, **kwargs):
    #     kwargs['context'] = self.get_serializer_context()
    #     return self.serializer_class(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purpose = serializer.validated_data['purpose']
        user_email = serializer.validated_data['user_email']
        user = User.objects.get(email=user_email)
        api_token = APIToken.objects.create(user=user, purpose=purpose)
        return Response(
            {'api_token': api_token.key,
            'purpose': api_token.purpose,
            'email': api_token.user.email},
            status=status.HTTP_201_CREATED
            )

    @action(detail=False) 
    def selected_user_tokens(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if (serializer.validated_data['purpose']
        and serializer.validated_data['user_email']):
            selected_purpose = serializer.validated_data['purpose']
            selected_email = serializer.validated_data['user_email']
            selected_user = User.objects.get(email=selected_email)
            
            selected_tokens = APIToken.objects.get_queryset(
                purpose=selected_purpose, user=selected_user
            )
            # should we loop through results before calling Response?
            # and format?
            return Response(selected_tokens)

        elif serializer.validated_data['purpose']:
            selected_purpose = serializer.validated_data['purpose']
            selected_tokens = APIToken.objects.get_queryset(
                purpose=selected_purpose
            )
            # should we loop through results before calling Response?
            # and format?
            return Response(selected_tokens)

        elif serializer.validated_data['user_email']:
            selected_email = serializer.validated_data['user_email']
            selected_user = User.objects.get(email=selected_email)
            selected_tokens = APIToken.objects.get_queryset(
                user=selected_user
            )
            # should we loop through results before calling Response?
            # and format?
            return Response(selected_tokens)

        else:
            # can we return a list here and delete the MultipleAPITokenViewSet?
            # or else just raise an error here
            # return self.list(request, *args, **kwargs)
            raise(Error)

        #     purpose = serializer.validated_data['purpose']
        
        # user_email = serializer.validated_data['user_email']
        # user_email = serializer.validated_data['user_email']
        # user = User.objects.get(email=user_email)
        # selected_user_tokens = APIToken.objects.get_queryset(
        #     user=user
        # ) 
        


class MultipleAPITokenViewSet(mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    queryset = APIToken.objects.all()
    # filter_fields = ['purpose', 'user', 'created']
    serializer_class = MultipleAPITokenSerializer

    permission_classes = (DRYPermissions,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

# How to include OK_Created response in the Response plus an adhoc message?



#############################################
# class APITokenView(APIView):
#     serializer_class = APITokenSerializer
#     filter_fields = '__all__'
#     permission_classes = (DRYPermissions,)

#     def get_serializer_context(self):
#         return {
#             'request': self.request,
#             'format': self.format_kwarg,
#             'view': self
#         }

#     def get_serializer(self, *args, **kwargs):
#         kwargs['context'] = self.get_serializer_context()
#         return self.serializer_class(*args, **kwargs)

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         purpose = serializer.validated_data['purpose']
#         api_token = APIToken.objects.create(user=user, purpose=purpose)
#         return Response({
#             'api_token': api_token.key,
#             'purpose': api_token.purpose,
#             'email': api_token.user.email,
#             })


# obtain_api_token = APITokenView.as_view()

# class APITokenViewSet(viewsets.ModelViewSet):
#     ''' This class is strongly inspired from ObtainToken in Django Rest Framework
#     Some differences are in the post function:
#     - the post function has been modified to allow:
#         - creating multiple tokens by a single user
#         - specifying to which purpose the token relates
#     TODO: - a get function has been added to allow user to retrieve:
#         - a list of their tokens
#         - the token related to a given purpose  
#     '''
#     serializer_class = APITokenSerializer
#     filter_fields = '__all__'
#     permission_classes = (DRYPermissions,)
#     # filter_backends = (APITokenBackend,)

#     # def get_permissions(self):
#     #     if self.action in ['list', 'retrieve']:
#     #         permission_classes = []
#     #     else:
#     #         permission_classes = [IsAdminUser]

#     #     return [permission() for permission in permission_classes]

#     # def get_queryset(self):
#     #     if self.request.user.is_staff:
#     #         return APIToken.objects.all()
#     #     else:
#     #         return APIToken.objects.filter(user=self.request.user)

#     if coreapi_schema.is_enabled():
#         schema = ManualSchema(
#             fields=[
#                 coreapi.Field(
#                     name="email",
#                     required=True,
#                     location='form',
#                     schema=coreschema.String(
#                         title="Email",
#                         description="Valid email associated with an active user",
#                     ),
#                 ),
#                 coreapi.Field(
#                     name="purpose",
#                     required=True,
#                     location='form',
#                     schema=coreschema.String(
#                         title="Purpose",
#                         description="Service to be associated with the API Token",
#                     ),
#                 ),
#             ],
#             encoding="application/json",
#         )

#     def get_serializer_context(self):
#         return {
#             'request': self.request,
#             'format': self.format_kwarg,
#             'view': self
#         }

#     def get_serializer(self, *args, **kwargs):
#         kwargs['context'] = self.get_serializer_context()
#         return self.serializer_class(*args, **kwargs)

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         purpose = serializer.validated_data['purpose']
#         api_token = APIToken.objects.create(user=user, purpose=purpose)
#         return Response({
#             'api_token': api_token.key,
#             'purpose': api_token.purpose,
#             'email': api_token.user.email,
#             })


# class APITokenReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     A simple ViewSet for viewing api tokens.
#     Note: a read-only viewset is needed to match
#     the read-only serializer which is itself needed
#     to allow getting the token user's email from database
#     instead of having to provide it
#     when creating a token
#     """
#     serializer_class = serializers.APITokenReadOnlySerializer
#     # filter_fields = '__all__'
#     filter_fields = [
#         'email',
#         'purpose',
#     ]
#     permission_classes = (DRYPermissions,)
#     filter_backends = (APITokenBackend,)
    