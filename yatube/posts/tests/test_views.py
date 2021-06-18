import shutil
import tempfile
from django.conf import settings
from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title="Заголовок", slug="slug")

        cls.another_group = Group.objects.create(
            title="Заголовок2", slug="slug2", id="3"
        )

        cls.user = User.objects.create(
            username="Pasha",
            id="1",
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый заголовок",
            author=cls.user,
            id=69,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
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


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username="Pasha",
            id="1",
        )

        cls.group = Group.objects.create(title="Заголовок", slug="slug")

        cls.post = Post.objects.create(
            text="Тестовый заголовок",
            author=cls.user,
            id=69,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_cache_correct_work(self):
        response = self.guest_client.get(reverse("index"))
        cached_response_content = response.content
        Post.objects.create(text="Тестовый заголовок", author=self.user)
        response = self.guest_client.get(reverse("index"))
        self.assertEqual(cached_response_content, response.content)
        cache.clear()
        response = self.guest_client.get(reverse("index"))
        self.assertNotEqual(cached_response_content, response.content)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(title="Заголовок", slug="slug")

        cls.user = User.objects.create(
            username="Pasha",
            id="1",
        )

        cls.another_user = User.objects.create(
            username="Serega",
            id="2",
        )

        cls.post = Post.objects.create(
            text="Тестовый заголовок",
            author=cls.user,
            id=69,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)
        cache.clear()

    def test_another_user_can_follow_author(self):
        """Авторизованный пользователь может подписываться
        и удалять подписки на других пользователей."""
        follow = Follow.objects.count()
        Follow.objects.create(user=self.another_user, author=self.user)
        self.assertEqual(Follow.objects.count(), follow + 1)
        Follow.objects.filter(
            user=self.another_user, author=self.user
        ).delete()
        self.assertEqual(Follow.objects.count(), follow)

    def test_follows_shows_correct_posts(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        Follow.objects.create(
            user=self.another_user,
            author=self.user,
        )
        url_reverse = reverse("follow_index")
        response = self.another_authorized_client.get(url_reverse)
        form_field = response.context["page"].object_list[0]
        self.assertEqual(form_field, self.post)

    def test_unfollows_shows_correct_posts(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него"""
        Follow.objects.create(
            user=self.another_user,
            author=self.user,
        )
        url_reverse = reverse("follow_index")
        response = self.authorized_client.get(url_reverse)
        form_field = len(response.context["page"].object_list)
        self.assertEqual(form_field, 0)
