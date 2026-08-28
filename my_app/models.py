from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


CATEGORY_CHOICES = (
    ('Technology', 'Technology'),
    ('AI & Future', 'AI & Future'),
    ('Design & Art', 'Design & Art'),
    ('History & Culture', 'History & Culture'),
    ('Business & Startups', 'Business & Startups'),
    ('General', 'General'),
)


class Post(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='General')
    content = models.TextField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='posts')
    views_count = models.PositiveIntegerField(default=0)
    is_draft = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    bookmarks = models.ManyToManyField(User, related_name='bookmarked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def get_image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_url:
            return self.image_url
        return ''


    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def total_comments(self):
        return self.comments.count()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, default="Passionate writer and reader on Posty.")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, default='')

    @property
    def get_avatar(self):
        if self.avatar:
            try:
                return self.avatar.url
            except Exception:
                pass
        if self.avatar_url:
            return self.avatar_url
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=d4af37&color=000000&bold=true"

    def __str__(self):
        return f"{self.user.username}'s Profile"



@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)

    