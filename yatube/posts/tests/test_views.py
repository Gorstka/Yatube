from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title="Заголовок", slug="slug")
        cls.another_group = Group.objects.create(
            title="Заголовок2", slug="slug2", id="3"
        )
        cls.user = User.objects.create(username="Pasha", id="1")
        cls.post = Post.objects.create(
            text="Тестовый заголовок",
            author=cls.user,
            id=69,
            group=cls.group,
            image="media/posts/square.jpg",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            "index.html": reverse("index"),
            "posts/group.html": reverse(
                "group_posts", kwargs={"slug": "slug"}
            ),
            "posts/new_post.html": reverse("new_post"),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        url_reverse = reverse("index")
        response = self.authorized_client.get(url_reverse)
        form_field = response.context["page"].object_list[0]
        self.assertEqual(form_field, self.post)
        self.assertEqual(form_field.image, self.post.image)

    def test_group_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        url_reverse = reverse("group_posts", kwargs={"slug": "slug"})
        response = self.authorized_client.get(url_reverse)
        form_field_group = response.context["group"]
        form_field_post = response.context["post"]
        self.assertEqual(form_field_group.title, self.group.title)
        self.assertEqual(form_field_group.slug, self.group.slug)
        self.assertEqual(form_field_post.image, self.post.image)

    def test_new_post_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        url_reverse = reverse("new_post")
        response = self.authorized_client.get(url_reverse)
        form_fields = {"text": forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        url_reverse = reverse(
            "post_edit", kwargs={"username": "Pasha", "post_id": 69}
        )
        response = self.authorized_client.get(url_reverse)
        form_fields = {"text": forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url_reverse = reverse("profile", kwargs={"username": "Pasha"})
        response = self.authorized_client.get(url_reverse)
        form_field = response.context["page"].object_list[0]
        self.assertEqual(form_field, self.post)
        self.assertEqual(form_field.image, self.post.image)

    def test_post_view_page_shows_correct_context(self):
        """Шаблон post_view сформирован с правильным контекстом."""
        url_reverse = reverse(
            "post", kwargs={"username": "Pasha", "post_id": 69}
        )
        response = self.authorized_client.get(url_reverse)
        form_field = response.context["post"]
        self.assertEqual(form_field, self.post)
        self.assertEqual(form_field.image, self.post.image)

    def test_index_and_group_posts_pages_shows_correct_post(self):
        """Если при создании поста указать группу,
        он попадает на страницы: главную страницу сайта и выбранной группы"""
        url_reverse = (
            reverse("index"),
            reverse("group_posts", kwargs={"slug": "slug"}),
        )

        for url in url_reverse:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                form_field = response.context["page"].object_list[0]
                self.assertEqual(form_field, self.post)

    def test_group_posts_page_shows_correct_posts(self):
        """Если при создании поста указать группу,
        он не попадает в группу, для которой не был предназначен"""
        url_reverse = reverse("group_posts", kwargs={"slug": "slug2"})
        response = self.authorized_client.get(url_reverse)
        form_field = len(response.context["page"].object_list)
        self.assertEqual(form_field, 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username="Pasha", id="1")

        cls.group = Group.objects.create(title="Заголовок", slug="slug")

        cls.posts = [
            Post(
                text=f"Тестовый заголовок{i}",
                author=cls.user,
                group=cls.group,
            )
            for i in range(1, 13)
        ]

        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        pages = {
            reverse("index"): "index",
            reverse("group_posts", kwargs={"slug": "slug"}): "group",
            reverse("profile", kwargs={"username": "Pasha"}): "profile",
        }
        for records in pages.keys():
            response = self.client.get(records)
            self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_second_page_contains_two_records(self):
        pages = {
            (reverse("index") + "?page=2"): "index",
            (
                reverse("group_posts", kwargs={"slug": "slug"}) + "?page=2"
            ): "group_posts",
            (
                reverse("profile", kwargs={"username": "Pasha"}) + "?page=2"
            ): "profile",
        }
        for records in pages.keys():
            response = self.client.get(records)
            self.assertEqual(len(response.context.get("page").object_list), 2)
