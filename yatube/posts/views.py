from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Group, User, Follow, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from yatube.settings import POSTS_PER_PAGE


def paginator(page_number, posts):
    """Вспомогательная функция для паджинатора."""
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    """Главная страница."""
    template = 'posts/index.html'
    posts = Post.objects.all()
    context = {
        'page_obj': paginator(request.GET.get('page'), posts),
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница постов группы."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': paginator(request.GET.get('page'), posts),
    }
    return render(request, template, context)


def profile(request, username):
    """Страница пользователя."""
    author = get_object_or_404(
        User.objects.select_related('profile'), username=username)
    posts = author.posts.all()
    template = 'posts/profile.html'
    context = {
        'author': author,
        'posts': posts,
        'page_obj': paginator(request.GET.get('page'), posts),
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Информация о посте."""
    form = CommentForm(request.POST or None)
    page_obj = get_object_or_404(Post, id=post_id)
    comments = page_obj.comments.all()
    template = 'posts/post_detail.html'
    context = {
        'page_obj': page_obj,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Создание поста."""
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'is_edit': True,
        'form': form,
        'post': post
    }
    return render(request, template, context)


@login_required
def post_del(request, post_id):
    """Удаление поста."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user.pk != post.author.pk:
        return redirect('posts:index')
    post.delete()
    return redirect('posts:index')


@login_required
def add_comment(request, post_id):
    """Создание комментария к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def edit_comment(request, comment_id):
    """Редактирование коммента."""
    template = 'posts/edit_comment.html'
    comment = get_object_or_404(
        Comment.objects.select_related('author'), pk=comment_id
    )
    if request.user.pk != comment.author.pk:
        return redirect('posts:post_detail', comment.post.pk)
    form = CommentForm(
        instance=comment,
        data=request.POST or None,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', comment.post.pk)
    context = {
        'form': form,
        'title': 'Редактировать коммент'
    }
    return render(request, template, context)


@login_required
def del_comment(request, comment_id):
    """Удаление коммента."""
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user.pk != comment.author.pk:
        return redirect('posts:post_detail', comment.post.pk)
    comment.delete()
    return redirect('posts:post_detail', comment.post.pk)


@login_required
def follow_index(request):
    """Подписки пользователя."""
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginator(request.GET.get('page'), posts),
        'title': 'Подписки'
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    is_follower.delete()
    return redirect('posts:profile', username=author)
