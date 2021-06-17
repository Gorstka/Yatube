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
        expected_object_name = self.post.text[:15]
        self.assertEqual(expected_object_name, str(self.post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Ж" * 100,
            description="Тестовый текст",
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            "title": "Заголовок",
            "description": "Описание",
            "slug": "Адрес страницы",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_text_convert_to_slug(self):
        """Содержимое поля title преобразуется в slug."""
        slug = self.group.slug
        self.assertEqual(slug, "ж" * 100)

    def test_text_slug_max_length_not_exceed(self):
        """
        Длинный slug обрезается и не превышает max_length поля slug в модели.
        """
        max_length_slug = self.group._meta.get_field("slug").max_length
        length_slug = len(self.group.slug)
        self.assertEqual(max_length_slug, length_slug)

    def test_object_name_is_title_field(self):
        """__str__  group - это строчка с содержимым group.title."""
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(self.group))
