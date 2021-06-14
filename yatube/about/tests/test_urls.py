from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_and_tech_urls_exists_at_desired_location(self):
        """URL-адрес использует соответствующий шаблон."""

        urls = ("/about/author/", "/about/tech/")

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
