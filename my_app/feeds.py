from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Post


class LatestPostsFeed(Feed):
    title = "Posty - Latest Articles & Insights"
    link = "/display-post/"
    description = "Updates on technology, AI, design, and culture from the Posty community."

    def items(self):
        return Post.objects.all().order_by('-created_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return f"{item.subtitle}\n\n{item.content[:300]}..."

    def item_link(self, item):
        return reverse('read-post', args=[item.pk])
