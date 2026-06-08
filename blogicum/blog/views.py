from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .constants import ITEMS_PER_PAGE
from .forms import CommentForm, PostForm
from .models import Post, Category, Comment

User = get_user_model()


def get_published_posts(queryset=None):
    if queryset is None:
        queryset = Post.objects
    return queryset.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).select_related('category', 'location', 'author')


def annotate_posts(queryset):
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


class BaseUserMixin:
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'


class BasePostMixin:
    model = Post


class BaseCommentMixin:
    model = Comment
    template_name = 'blog/comment.html'


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        obj = self.get_object()
        post_pk = obj.post.pk if hasattr(obj, 'post') else obj.pk
        return redirect('blog:post_detail', pk=post_pk)


class SuccessUrlToPostMixin:
    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
        )


class IndexListView(ListView, BasePostMixin):
    template_name = 'blog/index.html'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        return annotate_posts(get_published_posts())


class PostDetailView(DetailView, BasePostMixin):
    template_name = 'blog/detail.html'

    def get_queryset(self):
        posts = Post.objects.select_related('category', 'location', 'author')
        if self.request.user.is_authenticated:
            return posts.filter(
                (
                    Q(pub_date__lte=timezone.now())
                    & Q(is_published=True)
                    & Q(category__is_published=True)
                )
                | Q(author=self.request.user)
            )
        return posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = (
            self.object.comments.select_related('author').all()
        )
        context['form'] = CommentForm()
        return context


class CategoryPostsListView(ListView, BasePostMixin):
    template_name = 'blog/category.html'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return annotate_posts(
            get_published_posts(self.category.posts.all())
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileDetailView(DetailView, BaseUserMixin):
    template_name = 'blog/profile.html'
    paginate_by = ITEMS_PER_PAGE

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        if self.request.user == self.object:
            posts = self.object.posts.all()
        else:
            posts = get_published_posts(
                self.object.posts.all()
            )
        posts = annotate_posts(posts)
        paginator = Paginator(posts, self.paginate_by)
        context['page_obj'] = paginator.get_page(self.request.GET.get('page'))
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView, BaseUserMixin):
    template_name = 'blog/user.html'
    fields = ('first_name', 'last_name', 'email', 'username',)

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.object.username}
        )


class PostCreateView(LoginRequiredMixin, CreateView, BasePostMixin):
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(
    LoginRequiredMixin,
    OnlyAuthorMixin,
    SuccessUrlToPostMixin,
    UpdateView,
    BasePostMixin
):
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'


class PostDeleteView(
    LoginRequiredMixin, OnlyAuthorMixin, DeleteView, BasePostMixin
):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')


class CommentCreateView(
    LoginRequiredMixin,
    SuccessUrlToPostMixin,
    CreateView,
    BaseCommentMixin
):
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentUpdateView(
    LoginRequiredMixin,
    OnlyAuthorMixin,
    SuccessUrlToPostMixin,
    UpdateView,
    BaseCommentMixin
):
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'



class CommentDeleteView(
    LoginRequiredMixin,
    OnlyAuthorMixin,
    SuccessUrlToPostMixin,
    DeleteView,
    BaseCommentMixin
):
    pk_url_kwarg = 'comment_id'

