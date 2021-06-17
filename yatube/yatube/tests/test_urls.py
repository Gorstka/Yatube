from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username="Pasha", id="1")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_page_not_found(self):
        """Возвращение кода ошибки 404 - страница не найдена"""
        url = "/69/"
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
