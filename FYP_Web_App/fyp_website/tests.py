from django.urls import reverse, resolve
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from . import views, models

#fyp_website app tests

class HomeTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        self.client.login(username='john', password='johnpassword')
    
    def test_home_view_status_code(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_saved_results_view_status_code(self):
        url = reverse('saved_results')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_help_page_view_status_code(self):
        url = reverse('help_page')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_dataset_cntr_view_status_code(self):
        url = reverse('dataset_cntr')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_sna_viz_view_status_code(self):
        url = reverse('sna_viz')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_login_view_status_code(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_signup_view_status_code(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_home_view_func(self):
        view = resolve('/')
        self.assertEquals(view.func, views.home)
        
    def test_saved_results_view_func(self):
        view = resolve('/saved_results/')
        self.assertEquals(view.func, views.saved_results)
        
    def test_sna_viz_view_func(self):
        view = resolve('/sna_viz/')
        self.assertEquals(view.func, views.sna_viz)
        
    def test_dataset_cntr_view_func(self):
        view = resolve('/dataset_cntr/')
        self.assertEquals(view.func, views.dataset_constructor)
        
    def test_help_view_func(self):
        view = resolve('/help/')
        self.assertEquals(view.func, views.help_page)
        
    def test_home_contains(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        self.assertContains(response, "If results don't automatically populate in the table below please ref")
        self.assertContains(response, 'Num Results: 0')
        
    def test_sna_viz_contains(self):
        url = reverse('sna_viz')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_data_cntr_contains(self):
        url = reverse('dataset_cntr')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_saved_results_contains(self):
        url = reverse('saved_results')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_help_contains(self):
        url = reverse('help_page')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
    
        
class LoginRequiredTests(TestCase):
    def setUp(self):
        self.url = reverse('help_page')
        self.response = self.client.get(self.url)

    def test_redirection(self):
        login_url = reverse('login')
        self.assertRedirects(self.response, '{login_url}?next={url}'.format(login_url=login_url, url=self.url))