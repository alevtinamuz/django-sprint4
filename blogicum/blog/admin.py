from django.contrib import admin

from .models import Post, Category, Location, Comment


@admin.register(Post)
class PostAdminModel(admin.ModelAdmin):
    list_display = ['title', 'pub_date', 'category', 'is_published', 'author']
    search_fields = ['title']
    list_filter = ['is_published', 'category']


@admin.register(Category)
class CategoryAdminModel(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published']
    search_fields = ['title']
    list_filter = ['is_published']


@admin.register(Location)
class LocationAdminModel(admin.ModelAdmin):
    list_display = ['name', 'is_published']
    search_fields = ['name']
    list_filter = ['is_published']


@admin.register(Comment)
class CommentAdminModel(admin.ModelAdmin):
    list_display = ['post', 'author', 'text']
