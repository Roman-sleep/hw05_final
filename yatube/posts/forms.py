from django.forms import ModelForm
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        exclude = ('author',)
        help_texts = {
            'text': ('Текст'),
            'group': ('Группа'),
            'author': ('Автор'),
            'image': ('Картинка'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_text = {
            'text': 'Здесь можно написать комментарий',
        }
