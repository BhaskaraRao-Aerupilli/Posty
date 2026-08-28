"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from os import name

from django.contrib import admin
from django.urls import path
from my_app import views
from django.conf import settings
from django.conf.urls.static import static  

from my_app.feeds import LatestPostsFeed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('display-post/', views.display_post, name='display-post'),
    path('read-post/<int:id>/', views.read_post, name='read-post'),
    path('add-post/', views.add_post, name='add-post'),
    path('update-post/<int:id>/', views.update_post, name='update-post'),
    path('delete-post/<int:id>/', views.delete_post, name='delete-post'),
    
    # Social & Community routes
    path('post/<int:id>/like/', views.toggle_like_view, name='toggle-like'),
    path('post/<int:id>/bookmark/', views.toggle_bookmark_view, name='toggle-bookmark'),
    path('post/<int:id>/comment/', views.add_comment_view, name='add-comment'),
    path('api/ai/comment-reply/', views.ai_comment_reply_view, name='ai-comment-reply'),
    path('saved/', views.bookmarked_posts_view, name='saved-posts'),
    path('profile/<str:username>/', views.author_profile_view, name='author-profile'),
    path('profile-edit/', views.edit_profile_view, name='edit-profile'),
    path('edit-profile/', views.edit_profile_view, name='edit-profile-alias'),
    path('analytics/', views.author_analytics_view, name='analytics'),

    path('drafts/', views.my_drafts_view, name='drafts'),
    path('post/<int:id>/export-md/', views.export_markdown_view, name='export-markdown'),
    
    # AI API routes
    path('api/ai/generate/', views.ai_generate_post_view, name='ai-generate-post'),
    path('api/ai/enhance/', views.ai_enhance_text_view, name='ai-enhance-text'),
    path('api/ai/summarize/<int:id>/', views.ai_summarize_post_view, name='ai-summarize-post'),
    path('api/ai/chat/<int:id>/', views.ai_chat_post_view, name='ai-chat-post'),
    path('api/ai/translate/<int:id>/', views.ai_translate_post_view, name='ai-translate-post'),
    path('api/ai/generate-image/', views.ai_generate_image_view, name='ai-generate-image'),
    
    # Live Web & Google Images Search route
    path('api/images/search/', views.api_search_images_view, name='api-search-images'),
    
    # RSS Feed
    path('feed/', LatestPostsFeed(), name='post-feed'),
]

from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

