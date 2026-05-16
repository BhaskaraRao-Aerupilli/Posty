from django.contrib import admin

# Register your models here.
from .models import Post
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at','updated_at')
    list_filter = ('created_at', 'author','updated_at')


admin.site.register(Post, PostAdmin)    