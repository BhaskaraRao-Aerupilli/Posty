from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Post
from . import ai_service
import json


class AIFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.post = Post.objects.create(
            title='Future of Artificial Intelligence',
            subtitle='How generative models are transforming daily developer workflows',
            content='Artificial intelligence is evolving at a breakneck pace. Modern tools allow developers to write, test, and ship code faster than ever before.',
            author=self.user
        )

    def test_ai_service_generate_post(self):
        result = ai_service.generate_post("Quantum Computing")
        self.assertIn("title", result)
        self.assertIn("subtitle", result)
        self.assertIn("content", result)
        self.assertTrue(len(result["title"]) > 0)

    def test_ai_service_enhance_content(self):
        result = ai_service.enhance_content("here is some draft text", action="polish")
        self.assertIn("enhanced_content", result)
        self.assertTrue(len(result["enhanced_content"]) > 0)

    def test_ai_service_summarize_post(self):
        result = ai_service.summarize_post(self.post.title, self.post.content)
        self.assertIn("summary", result)
        self.assertIn("key_takeaways", result)
        self.assertTrue(len(result["key_takeaways"]) > 0)

    def test_ai_service_ask_question(self):
        result = ai_service.ask_post_question(self.post.title, self.post.content, "What is this post about?")
        self.assertIn("answer", result)
        self.assertTrue(len(result["answer"]) > 0)

    def test_api_generate_post_endpoint(self):
        response = self.client.post(
            '/api/ai/generate/',
            data=json.dumps({'topic': 'Django and Python', 'tone': 'Technical'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('title', data['data'])

    def test_api_enhance_endpoint(self):
        response = self.client.post(
            '/api/ai/enhance/',
            data=json.dumps({'content': 'My blog post content.', 'action': 'expand'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('enhanced_content', data['data'])

    def test_api_summarize_endpoint(self):
        response = self.client.get(f'/api/ai/summarize/{self.post.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('summary', data['data'])

    def test_api_chat_endpoint(self):
        response = self.client.post(
            f'/api/ai/chat/{self.post.id}/',
            data=json.dumps({'question': 'What are the main points?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('answer', data['data'])

    def test_api_image_search_endpoint(self):
        response = self.client.get('/api/images/search/?q=Pyramids')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('images', data)
        self.assertTrue(isinstance(data['images'], list))

    def test_like_toggle(self):
        self.client.login(username='testuser', password='password123')
        # Like
        response = self.client.post(f'/post/{self.post.id}/like/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_liked'])
        self.assertEqual(data['total_likes'], 1)
        # Unlike
        response = self.client.post(f'/post/{self.post.id}/like/')
        data = response.json()
        self.assertFalse(data['is_liked'])
        self.assertEqual(data['total_likes'], 0)

    def test_bookmark_toggle(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(f'/post/{self.post.id}/bookmark/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_bookmarked'])

    def test_add_comment(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(
            f'/post/{self.post.id}/comment/',
            data={'content': 'Incredible insights! Thanks for writing.'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.post.comments.count(), 1)

    def test_ai_comment_reply(self):
        response = self.client.post(
            '/api/ai/comment-reply/',
            data=json.dumps({'post_title': self.post.title, 'comment_text': 'Great article!'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('reply', data['data'])

    def test_author_profile_view(self):
        response = self.client.get(f'/profile/{self.user.username}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_saved_posts_view(self):
        self.client.login(username='testuser', password='password123')
        self.post.bookmarks.add(self.user)
        response = self.client.get('/saved/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)

    def test_feed_search_and_category(self):
        response = self.client.get('/display-post/?q=Artificial&category=General')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)

    def test_rss_feed_endpoint(self):
        response = self.client.get('/feed/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('xml', response['Content-Type'])

    def test_ai_translate_post_endpoint(self):
        response = self.client.get(f'/api/ai/translate/{self.post.id}/?lang=Spanish')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('title', data['data'])
        self.assertIn('content', data['data'])

    def test_ai_generate_image_endpoint(self):
        response = self.client.post(
            '/api/ai/generate-image/',
            data=json.dumps({'topic': 'Pyramids of Giza at Sunset'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('url', data['data'])

    def test_author_analytics_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Creator Analytics')

    def test_my_drafts_view(self):
        self.client.login(username='testuser', password='password123')
        draft = Post.objects.create(
            title='Secret Draft Article',
            subtitle='Not yet published',
            content='Draft content here',
            author=self.user,
            is_draft=True
        )
        response = self.client.get('/drafts/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, draft.title)

    def test_export_markdown(self):
        response = self.client.get(f'/post/{self.post.id}/export-md/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        self.assertContains(response, self.post.title)

    def test_edit_profile_view(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/edit-profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Your Profile')

        post_data = {
            'bio': 'Updated author bio for testing',
            'avatar_url': 'https://example.com/avatar.jpg'
        }
        res_post = self.client.post('/edit-profile/', post_data, follow=True)
        self.assertEqual(res_post.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated author bio for testing')
        self.assertEqual(self.user.profile.avatar_url, 'https://example.com/avatar.jpg')




