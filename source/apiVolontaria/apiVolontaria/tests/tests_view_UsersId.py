import json

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.urls import reverse

from location.models import Country, StateProvince, Address
from volunteer.models import Cell
from apiVolontaria import models
from apiVolontaria.factories import UserFactory, AdminFactory

from apiVolontaria.testing_tools import CustomAPITestCase


class UsersIdTests(CustomAPITestCase):

    ATTRIBUTES = [
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'phone',
        'mobile',
        'is_superuser',
        'managed_cell',
    ]

    def setUp(self):
        self.client = APIClient()

        self.user = UserFactory()
        self.user.set_password('Test123!')
        self.user.save()

        self.admin = AdminFactory()
        self.admin.set_password('Test123!')
        self.admin.save()

    def test_retrieve_user_id_not_exist(self):
        """
        Ensure we can't retrieve a user that doesn't exist.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse(
                'users_id',
                kwargs={'pk': 999},
            )
        )

        content = {"detail": "Not found."}
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_user_id_not_exist_without_permission(self):
        """
        Ensure we can't know a user doesn't exist without permission
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                'users_id',
                kwargs={'pk': 999},
            )
        )

        content = {"detail": "You are not authorized "
                             "to get detail of a given user."}
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user(self):
        """
        Ensure we can retrieve a user.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse(
                'users_id',
                kwargs={'pk': self.user.id},
            )
        )

        content = json.loads(response.content)

        # Check id of the user
        self.assertEqual(content['id'], self.user.id)

        # Check the system doesn't return attributes not expected
        attributes = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'phone',
            'mobile',
            'is_superuser',
            'managed_cell',
        ]
        for key in content.keys():
            self.assertTrue(
                key in attributes,
                'Attribute "{0}" is not expected but is '
                'returned by the system.'.format(key)
            )
            attributes.remove(key)

        # Ensure the system returns all expected attributes
        self.assertTrue(
            len(attributes) == 0,
            'The system failed to return some '
            'attributes : {0}'.format(attributes)
        )

        # Check the status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_profile(self):
        """
        Ensure we can retrieve our profile without id.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                'profile',
            )
        )

        content = json.loads(response.content)

        # Check id of the user
        self.assertEqual(content['id'], self.user.id)

        # Check the system doesn't return attributes not expected
        attributes = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'phone',
            'mobile',
            'is_superuser',
            'managed_cell',
        ]
        for key in content.keys():
            self.assertTrue(
                key in attributes,
                'Attribute "{0}" is not expected but is '
                'returned by the system.'.format(key)
            )
            attributes.remove(key)

        # Ensure the system returns all expected attributes
        self.assertTrue(
            len(attributes) == 0,
            'The system failed to return some '
            'attributes : {0}'.format(attributes)
        )

        # Check the status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_with_permission(self):
        """
        Ensure we can update a specific user if caller has permission.
        """

        data_post = {
            "phone": "1234567890",
        }

        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            reverse(
                'users_id',
                kwargs={'pk': self.user.id},
            ),
            data_post,
            format='json',
        )

        content = json.loads(response.content)

        # Check if update was successful
        self.assertEqual(content['phone'], data_post['phone'])

        # Check id of the user
        self.assertEqual(content['id'], self.user.id)

        # Check the system doesn't return attributes not expected
        attributes = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'phone',
            'mobile',
            'is_superuser',
            'managed_cell',
        ]
        for key in content.keys():
            self.assertTrue(
                key in attributes,
                'Attribute "{0}" is not expected but is '
                'returned by the system.'.format(key)
            )
            attributes.remove(key)

        # Ensure the system returns all expected attributes
        self.assertTrue(
            len(attributes) == 0,
            'The system failed to return some '
            'attributes : {0}'.format(attributes)
        )

        # Check the status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_without_permission(self):
        """
        Ensure we can update a specific user if caller has permission.
        """

        data_post = {
            "phone": "1234567890",
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                'users_id',
                kwargs={'pk': self.user.id},
            ),
            data_post,
            format='json',
        )

        content = {"detail": "You are not authorized "
                             "to update a given user."}
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_profile(self):
        """
        Ensure we can update our own profile.
        """

        data_post = {
            "phone": "1234567890",
            "password": "Test123!",
            "new_password": "new_pass1234",
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                'profile',
            ),
            data_post,
            format='json',
        )

        content = json.loads(response.content)

        # Check if update was successful
        self.assertEqual(content['phone'], data_post['phone'])
        self.assertTrue(
            models.User.objects.get(id=self.user.id)
            .check_password("new_pass1234")
        )

        # Check id of the user
        self.assertEqual(content['id'], self.user.id)

        # Check the system doesn't return attributes not expected
        attributes = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'phone',
            'mobile',
            'is_superuser',
            'managed_cell',
        ]
        for key in content.keys():
            self.assertTrue(
                key in attributes,
                'Attribute "{0}" is not expected but is '
                'returned by the system.'.format(key)
            )
            attributes.remove(key)

        # Ensure the system returns all expected attributes
        self.assertTrue(
            len(attributes) == 0,
            'The system failed to return some '
            'attributes : {0}'.format(attributes)
        )

        # Check the status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile_bad_password(self):
        """
        Ensure we can't update our password if it is wrong.
        """

        data_post = {
            "phone": "1234567890",
            "password": "wrong",
            "new_password": "new_pass1234",
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                'profile',
            ),
            data_post,
            format='json',
        )

        content = ["Bad password"]
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_weak_new_password(self):
        """
        Ensure we can't update our password if it is wrong.
        """

        data_post = {
            "phone": "1234567890",
            "password": "Test123!",
            "new_password": "1234567890",
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                'profile',
            ),
            data_post,
            format='json',
        )

        content = {
            'password': [
                'This password is too common.',
                'This password is entirely numeric.'
            ]
        }
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_missing_password(self):
        """
        Ensure we can't update our password old one is not provided.
        """

        data_post = {
            "phone": "1234567890",
            "new_password": "new_pass1234",
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                'profile',
            ),
            data_post,
            format='json',
        )

        content = ['Missing "password" field. Cannot update password.']
        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_with_empty_managed_cell(self):
        """
        Ensure we can retrieve a user with an empty managed_cell list.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse(
                'users_id',
                kwargs={'pk': self.user.id},
            )
        )

        content = json.loads(response.content)

        self.assertEqual(content['managed_cell'], list())

    def test_retrieve_user_with_managed_cell(self):
        """
        Ensure we can retrieve a user with an manager in it managed_cell list.
        """
        self.client.force_authenticate(user=self.admin)

        random_country = Country.objects.create(
            name="random country",
            iso_code="RC",
        )
        random_state_province = StateProvince.objects.create(
            name="random state",
            iso_code="RS",
            country=random_country,
        )
        address = Address.objects.create(
            address_line1='random address 1',
            postal_code='RAN DOM',
            city='random city',
            state_province=random_state_province,
            country=random_country,
        )

        cell = Cell.objects.create(
            name='my cell',
            address=address,
        )

        cell.managers.set([self.user])
        cell.save()

        response = self.client.get(
            reverse(
                'users_id',
                kwargs={'pk': self.user.id},
            )
        )

        content = json.loads(response.content)

        self.check_attributes(content)

        cell_attributes = [
            'id',
            'name',
            'address',
            'managers',
        ]
        self.check_attributes(content['managed_cell'][0], cell_attributes)
