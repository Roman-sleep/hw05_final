from posts.models import User
from django.contrib.auth.forms import UserCreationForm


class CreationForm(UserCreationForm):
    """Форма создания пользователя."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
