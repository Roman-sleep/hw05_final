import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        picture_jpg_in_byte = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.picture = SimpleUploadedFile(
            name='picture.jpg',
            content=picture_jpg_in_byte,
            content_type='image/jpg'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_created_successfully(self):
        """Fорма редактирует существующий пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста из формы',
            'author': self.user,
            'image': self.picture,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_eddited_successfully(self):
        """Fорма редактирует существующий пост."""
        form_data = {
            'text': 'Текст поста из формы',
            'author': self.user
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        form_data = {
            'text': 'Новый текст поста из формы',
            'author': self.authorized_client
        }
        last_post = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': last_post}),
            is_edit=True,
            data=form_data,
        )
        last_post_text_eddited = Post.objects.get(id=last_post).text
        self.assertEqual(last_post_text_eddited, 'Новый текст поста из формы')

    def test_post_edit_not_create_guest_client(self):
        """ Fорма не изменит запись в Post если неавторизован."""
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
        )
        self.assertRedirects(
            response,
            f"/auth/login/?next=/posts/{self.post.id}/edit/"
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text="Изменяем текст").exists())


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.comment_count = Comment.objects.count()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает новый комментарий."""
        form_data = {
            'post': self.post,
            'text': 'Другой тестовый комментарий',
            'author': self.comment.author,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), self.comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            post=self.post,
            text=form_data['text'],
            author=self.comment.author
        ).exists(), ('Пост не был создан'))

    def test_ignore_comment(self):
        """Форма не создает комментарий неавторизованного пользователя."""
        form_data = {
            'text': 'Третий тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertNotIn(form_data['text'], response.content.decode())
        self.assertEqual(Comment.objects.count(), self.comment_count)
