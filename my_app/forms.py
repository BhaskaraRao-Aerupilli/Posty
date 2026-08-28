from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Comment, Profile
from django import forms
from django.forms import ModelForm


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'subtitle', 'category', 'image', 'image_url', 'content', 'is_draft']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['image_url'].required = False
        self.fields['is_draft'].required = False



class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Share your thoughts, questions, or insights on this article...',
                'style': 'min-height: 80px; margin-bottom: 10px;'
            })
        }


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'avatar_url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell the Posty community about yourself...'}),
            'avatar_url': forms.URLInput(attrs={'placeholder': 'Or paste image URL (e.g. from GitHub, Gravatar, Unsplash)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].required = False
        self.fields['avatar_url'].required = False

