from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@require_GET
@cache_page(20, key_prefix="index_page")
def index(request):
    posts = Post.objects.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "index.html",
        {"page": page},
    )


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:12]

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(
        request,
        "posts/group.html",
        {
            "group": group,
            "posts": posts,
            "page": page,
        },
    )


@require_GET
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_all = Post.objects.filter(author_id=author.id)

    paginator = Paginator(posts_all, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()

    return render(
        request,
        "posts/profile.html",
        {
            "posts_all": posts_all,
            "author": author,
            "page": page,
            "following": following,
        },
    )


@require_GET
def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    posts_count = Post.objects.filter(author_id=author.id)

    comments = post.comments.all()
    form = CommentForm()

    return render(
        request,
        "posts/post.html",
        {
            "author": author,
            "posts_count": posts_count,
            "post": post,
            "comments": comments,
            "form": form,
        },
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if not form.is_valid():
        return render(
            request, "posts/new_post.html", {"form": form, "edit": False}
        )

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("index")


@login_required
def post_edit(request, username, post_id):
    post_edit = get_object_or_404(Post, id=post_id, author__username=username)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post_edit
    )

    if request.user != post_edit.author:
        return redirect("post", username, post_id)

    if form.is_valid():
        form.save()
        return redirect("post", username, post_id)

    return render(
        request,
        "posts/new_post.html",
        {"form": form, "post_edit": post_edit, "edit": True},
    )


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("post", username=author.username, post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "posts/follow.html", {"page": page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not follow:
        Follow.objects.create(user=request.user, author=author)
    return redirect("profile", username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username
    ).delete()
    return redirect("profile", username)
