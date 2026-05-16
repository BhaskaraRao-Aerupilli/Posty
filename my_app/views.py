from django.shortcuts import redirect, render
from .forms import Post, PostForm, UserRegistrationForm
from django.contrib.auth import authenticate,login,logout
from .models import Post
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse



def home(request):
    posts = Post.objects.all().order_by('-created_at')[:3]
    context = {
        'posts': posts
    }
    return render(request, 'home.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method=='GET':
        return render(request, 'login.html')
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            error='invalid username or password'
            return render(request,'login.html',{'error':error})
        
def user_logout(request):
    logout(request)
    return redirect('home')

def display_post(request):
    posts= Post.objects.all().order_by('-created_at')
    return render(request,'display-post.html', {'posts': posts})

def read_post(request, id):
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return redirect('display-post')
    return render(request, 'read-post.html', {'post': post})

@login_required(login_url='login')
def add_post(request): 
    form= PostForm()
    if request.method == 'GET':
        return render(request, 'add-post.html', {'form': form})
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post=form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('display-post')
        else:
            return render(request, 'add-post.html', {'form': form})
        
@login_required(login_url='login')       
def update_post(request, id):
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return HttpResponse('Post not found', status=404)
    if request.user != post.author:
        return HttpResponse('Unauthorized', status=401)
    form = PostForm(instance=post)
    if request.method == 'GET':
        return render(request, 'update-post.html', {'form': form})
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save(commit=False)
            post.updated_at = timezone.now()
            post.save()
            return redirect('display-post')
        else:
            return render(request, 'update-post.html', {'form': form})
        
def delete_post(request, id):
    try:
        post = Post.objects.get(pk=id)
    except Post.DoesNotExist:
        return redirect('display-post')
    if request.user != post.author:
        return redirect('display-post')
    post.delete()
    return redirect('display-post')