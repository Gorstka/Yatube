import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="slug",
            description="Тестовый текст",
        )
        cls.user = User.objects.create(username="Pasha", id="1")

        cls.post = Post.objects.create(
            text="Тестовый заголовок", author=cls.user, id=69
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
            "image": uploaded,
        }

        self.authorized_client.post(
            reverse("new_post"), data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                group=self.group.id,
                image="posts/small.gif",
            ).exists()
        )

    def test_post_edit_form(self):
        """Редактирование поста через форму
        изменяет соответствующую запись в БД"""

        posts_count = Post.objects.count()

        form_data = {
            "text": "Тестовый текст1",
            "group": self.group.id,
        }

        self.authorized_client.post(
            reverse("post_edit", kwargs={"username": "Pasha", "post_id": 69}),
            data=form_data,
        )

        self.post.refresh_from_db()

        self.assertEqual(self.post.text, "Тестовый текст1")

        self.assertEqual(self.post.group, self.group)

        self.assertEqual(Post.objects.count(), posts_count)


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username="Pasha", id="1")

        cls.post = Post.objects.create(
            text="Тестовый заголовок", author=cls.user, id=69
        )

        cls.comment = Comment.objects.create(
            text="Текст", author=cls.user, id=35
        )

        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_comment(self):
        """Проверка возможности комментирования
        авторизованным пользователем постов."""
        comment_count = Comment.objects.count()

        form_data = {
            "text": "Текст",
            "post": self.post.id,
        }

        self.authorized_client.post(
            reverse(
                "add_comment", kwargs={"username": "Pasha", "post_id": 69}
            ),
            data=form_data,
            follow=True,
        )

        self.post.refresh_from_db()

        self.assertEqual(Comment.objects.count(), comment_count + 1)

        self.assertTrue(
            Comment.objects.filter(
                text="Текст",
                post=self.post.id,
            ).exists()
        )
