from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(title="Заголовок", slug="slug")
        user = User.objects.create(username="Pasha", id="1")
        Post.objects.create(text="Тестовый заголовок", author=user, id=69)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="Pasha", id="1")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_user = User.objects.create_user(username="Sergo", id="2")
        self.authorized_another_user = Client()
        self.authorized_another_user.force_login(self.another_user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """URL-адрес использует соответствующий шаблон."""

        urls = (
            "/",
            "/new/",
            "/group/slug/",
            "/Pasha/",
            "/Pasha/69/",
            "/Pasha/69/edit/",
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_on_auth_login(self):
        """URL-адрес использует соответствующий шаблон."""

        redirect_urls = {
            "/new/": "/auth/login/?next=/new/",
            "/Pasha/69/edit/": "/auth/login/?next=/Pasha/69/edit/",
        }
        for url, re_urls in redirect_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, re_urls)

    def test_post_edit_redirect_authorized_client_on_post(self):
        """Страница по адресу /username/post_id/edit/ перенаправит авторизированного
        пользователя не автора на страницу поста.
        """
        url = "/Pasha/69/edit/"
        response = self.authorized_another_user.get(url)
        self.assertRedirects(response, "/Pasha/69/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_url_names = {
            "/": "index.html",
            "/new/": "posts/new_post.html",
            "/group/slug/": "posts/group.html",
            "/Pasha/": "posts/profile.html",
            "/Pasha/69/": "posts/post.html",
            "/Pasha/69/edit/": "posts/new_post.html",
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
