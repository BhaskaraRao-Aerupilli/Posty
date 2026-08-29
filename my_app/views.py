from django.shortcuts import redirect, render, get_object_or_404
from .forms import Post, PostForm, UserRegistrationForm, CommentForm, ProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Post, Comment, Profile, CATEGORY_CHOICES
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json
from . import ai_service
from . import image_search


def home(request):
    all_published = Post.objects.filter(is_draft=False)
    featured_post = all_published.order_by('-views_count', '-created_at').first()
    recent_posts = all_published.exclude(id=featured_post.id if featured_post else None).order_by('-created_at')[:6]
    categories = [cat[0] for cat in CATEGORY_CHOICES]
    total_articles = all_published.count()
    total_authors = User.objects.count()

    context = {
        'featured_post': featured_post,
        'posts': recent_posts,
        'categories': categories,
        'total_articles': total_articles,
        'total_authors': total_authors,
    }
    return render(request, 'home.html', context)




def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = 'Invalid username or password'
            return render(request, 'login.html', {'error': error})


def user_logout(request):
    logout(request)
    return redirect('home')


def display_post(request):
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    
    posts = Post.objects.filter(is_draft=False).order_by('-created_at')

    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(subtitle__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )
        
    if selected_category and selected_category != 'All':
        posts = posts.filter(category=selected_category)
        
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ['All'] + [cat[0] for cat in CATEGORY_CHOICES]
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj.object_list,
        'query': query,
        'selected_category': selected_category or 'All',
        'categories': categories,
        'total_count': posts.count()
    }
    return render(request, 'display-post.html', context)


def read_post(request, id):
    post = get_object_or_404(Post, pk=id)
    
    # Increment view count
    post.views_count += 1
    post.save(update_fields=['views_count'])
    
    comments = post.comments.all()
    comment_form = CommentForm()
    
    is_liked = False
    is_bookmarked = False
    if request.user.is_authenticated:
        is_liked = post.likes.filter(id=request.user.id).exists()
        is_bookmarked = post.bookmarks.filter(id=request.user.id).exists()
        
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked,
    }
    return render(request, 'read-post.html', context)


@login_required(login_url='login')
def add_post(request): 
    form = PostForm()
    if request.method == 'GET':
        return render(request, 'add-post.html', {'form': form})
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if request.FILES.get('image'):
                post.image_url = ''
            post.save()
            return redirect('display-post')
        else:
            return render(request, 'add-post.html', {'form': form})
        

@login_required(login_url='login')       
def update_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if request.user != post.author:
        return HttpResponse('Unauthorized', status=401)
    form = PostForm(instance=post)
    if request.method == 'GET':
        return render(request, 'update-post.html', {'form': form, 'post': post})
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.updated_at = timezone.now()
            if request.FILES.get('image'):
                post.image_url = ''
            post.save()
            return redirect('display-post')
        else:
            return render(request, 'update-post.html', {'form': form, 'post': post})

        

def delete_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if request.user != post.author:
        return redirect('display-post')
    post.delete()
    return redirect('display-post')



# ==========================================
# AI Assistant & Image Search API Endpoints
# ==========================================

@csrf_exempt
def ai_generate_post_view(request):
    """Generate title, subtitle, content, and live web images from a topic."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        topic = data.get('topic', '')
        tone = data.get('tone', 'Engaging')
        
        if not topic:
            return JsonResponse({'error': 'Topic is required'}, status=400)
            
        result = ai_service.generate_post(topic=topic, tone=tone)
        
        # Also fetch matching live web images for the topic
        images = image_search.search_web_images(topic, limit=6)
        result['images'] = images
        result['suggested_image'] = images[0]['url'] if images else ''
        
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def api_search_images_view(request):
    """Search live web pages, Google / Bing, and Wikimedia for images."""
    query = request.GET.get('q', '').strip()
    if not query and request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            query = body.get('q', '').strip()
        except Exception:
            pass

    if not query:
        return JsonResponse({'error': 'Search query is required'}, status=400)

    try:
        images = image_search.search_web_images(query, limit=12)
        return JsonResponse({'success': True, 'images': images, 'query': query})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def ai_enhance_text_view(request):
    """Polish, expand, summarize, or fix grammar for text."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        content = data.get('content', '')
        action = data.get('action', 'polish')
        
        if not content:
            return JsonResponse({'error': 'Content is required'}, status=400)
            
        result = ai_service.enhance_content(content=content, action=action)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ai_summarize_post_view(request, id):
    """Generate key takeaways and summary for a given post."""
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
        
    try:
        result = ai_service.summarize_post(title=post.title, content=post.content)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ai_chat_post_view(request, id):
    """Interactive Q&A chat grounded in the post's content."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
        
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
        
    try:
        data = json.loads(request.body.decode('utf-8'))
        question = data.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Question cannot be empty'}, status=400)
            
        result = ai_service.ask_post_question(title=post.title, content=post.content, question=question)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ai_comment_reply_view(request):
    """AI Assistant to help authors draft smart replies to comments."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    try:
        data = json.loads(request.body.decode('utf-8'))
        post_title = data.get('post_title', '')
        comment_text = data.get('comment_text', '')
        if not comment_text:
            return JsonResponse({'error': 'Comment text is required'}, status=400)
            
        result = ai_service.generate_comment_reply(post_title=post_title, comment_text=comment_text)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==========================================
# Community, Likes, Bookmarks & Profile Views
# ==========================================

@login_required(login_url='login')
@csrf_exempt
def toggle_like_view(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        is_liked = False
    else:
        post.likes.add(request.user)
        is_liked = True
    return JsonResponse({'success': True, 'is_liked': is_liked, 'total_likes': post.total_likes})


@login_required(login_url='login')
@csrf_exempt
def toggle_bookmark_view(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user)
        is_bookmarked = False
    else:
        post.bookmarks.add(request.user)
        is_bookmarked = True
    return JsonResponse({'success': True, 'is_bookmarked': is_bookmarked})


@login_required(login_url='login')
def add_comment_view(request, id):
    post = get_object_or_404(Post, pk=id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(post=post, author=request.user, content=content)
    return redirect('read-post', id=post.id)


@login_required(login_url='login')
def bookmarked_posts_view(request):
    posts = request.user.bookmarked_posts.all().order_by('-created_at')
    return render(request, 'bookmarks.html', {'posts': posts})


def author_profile_view(request, username):
    author_user = get_object_or_404(User, username=username)
    posts = author_user.posts.all().order_by('-created_at')
    total_views = sum(p.views_count for p in posts)
    total_likes = sum(p.total_likes for p in posts)
    
    context = {
        'author_user': author_user,
        'profile': getattr(author_user, 'profile', None),
        'posts': posts,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_posts': posts.count()
    }
    return render(request, 'profile.html', context)


@login_required(login_url='login')
def edit_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            p = form.save(commit=False)
            # If user uploaded a new local file, clear avatar_url
            if request.FILES.get('avatar'):
                p.avatar_url = ''
            elif p.avatar_url:
                # User set/generated a new avatar_url
                p.avatar = None
            p.save()
            return redirect('author-profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit-profile.html', {'form': form, 'profile': profile})




# ==========================================
# Posty v3.0: Analytics, Translation, Drafts & Export
# ==========================================

@login_required(login_url='login')
def author_analytics_view(request):
    """Visual Analytics Dashboard for authors."""
    user_posts = request.user.posts.all()
    published_posts = user_posts.filter(is_draft=False)
    draft_posts = user_posts.filter(is_draft=True)
    
    total_views = sum(p.views_count for p in published_posts)
    total_likes = sum(p.total_likes for p in published_posts)
    total_comments = sum(p.total_comments for p in published_posts)
    total_bookmarks = sum(p.bookmarks.count() for p in published_posts)
    
    # Calculate Engagement Rate per view
    engagement_rate = 0.0
    if total_views > 0:
        engagement_rate = round(((total_likes + total_comments + total_bookmarks) / total_views) * 100, 1)
        
    top_posts = published_posts.order_by('-views_count')[:5]
    
    # Category Distribution
    category_counts = {}
    for p in published_posts:
        category_counts[p.category] = category_counts.get(p.category, 0) + 1
        
    context = {
        'total_published': published_posts.count(),
        'total_drafts': draft_posts.count(),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_bookmarks': total_bookmarks,
        'engagement_rate': engagement_rate,
        'top_posts': top_posts,
        'category_counts': category_counts,
    }
    return render(request, 'analytics.html', context)


@login_required(login_url='login')
def my_drafts_view(request):
    """Private workspace for drafts."""
    drafts = request.user.posts.filter(is_draft=True).order_by('-created_at')
    return render(request, 'drafts.html', {'drafts': drafts})


@csrf_exempt
def ai_translate_post_view(request, id):
    """Real-Time AI Multi-Language Translation."""
    post = get_object_or_404(Post, pk=id)
    target_language = request.GET.get('lang', 'Spanish')
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            target_language = body.get('lang', target_language)
        except Exception:
            pass
            
    try:
        translated = ai_service.translate_post(
            title=post.title,
            subtitle=post.subtitle,
            content=post.content,
            target_language=target_language
        )
        return JsonResponse({'success': True, 'data': translated})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def ai_generate_image_view(request):
    """Generate high quality AI artwork from a prompt."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    try:
        body = json.loads(request.body.decode('utf-8'))
        topic = body.get('topic', '').strip()
        custom_prompt = body.get('prompt', '').strip()
        
        if not topic and not custom_prompt:
            return JsonResponse({'error': 'Topic or prompt is required'}, status=400)
            
        final_prompt = custom_prompt if custom_prompt else ai_service.generate_ai_image_prompt(topic)
        result = image_search.generate_ai_artwork(final_prompt)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def export_markdown_view(request, id):
    """Export article formatted as a Markdown (.md) document."""
    post = get_object_or_404(Post, pk=id)
    
    md_content = f"""---
title: "{post.title}"
subtitle: "{post.subtitle}"
category: "{post.category}"
author: "{post.author.username}"
date: "{post.created_at.strftime('%Y-%m-%d')}"
views: {post.views_count}
likes: {post.total_likes}
---

# {post.title}

> *{post.subtitle}*

**Category:** {post.category}  
**Author:** {post.author.username}  
**Published:** {post.created_at.strftime('%B %d, %Y')}

---

{post.content}
"""
    response = HttpResponse(md_content, content_type='text/markdown; charset=utf-8')
    safe_title = "".join(c for c in post.title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    response['Content-Disposition'] = f'attachment; filename="{safe_title or "article"}.md"'
    return response

