from django.contrib.auth.models import User
from django.test import TestCase

from ..models import Group, Post


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create(id="1")
        cls.post = Post.objects.create(
            text="Тестовый текст, первые пятнадцать символов поста",
            author=user,
        )

    def test_object_name_is_text_field(self):
        """__str__  post - это строчка с содержимым post.text"""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Ж" * 100, description="Тестовый текст"
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        group = self.group
        field_verboses = {
            "title": "Заголовок",
            "description": "Описание",
            "slug": "Адрес странцы",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )

    def test_text_convert_to_slug(self):
        """Содержимое поля title преобразуется в slug."""
        group = self.group
        slug = group.slug
        self.assertEquals(slug, "zh" * 50)

    def test_text_slug_max_length_not_exceed(self):
        """
        Длинный slug обрезается и не превышает max_length поля slug в модели.
        """
        group = self.group
        max_length_slug = group._meta.get_field("slug").max_length
        length_slug = len(group.slug)
        self.assertEqual(max_length_slug, length_slug)

    def test_object_name_is_title_field(self):
        """__str__  group - это строчка с содержимым group.title."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
