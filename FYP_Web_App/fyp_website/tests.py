from django.urls import reverse, resolve
from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from . import views, models

#fyp_website app tests

class FYPWebsiteTests(TestCase):
    """
        Tests for most of the website.
    """
    def setUp(self):
        """
            Sets up the environment for the test cases. Creates a user account and logs in with it.
        """
        self.client = Client()
        self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
        self.client.login(username='john', password='johnpassword')
    
    def test_home_view_status_code(self):
        """
            Tests the status code that is returned when the home page is requested.
        """
        url = reverse('home')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_saved_results_view_status_code(self):
        """
            Tests the status code that is returned when the saved results page is requested.
        """
        url = reverse('saved_results')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_help_page_view_status_code(self):
        """
            Tests the status code that is returned when the help page is requested.
        """
        url = reverse('help_page')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_dataset_cntr_view_status_code(self):
        """
            Tests the status code that is returned when the dataset constructor page is requested.
        """
        url = reverse('dataset_cntr')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_sna_viz_view_status_code(self):
        """
            Tests the status code that is returned when the SNA and Visualizations page is requested.
        """
        url = reverse('sna_viz')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_login_view_status_code(self):
        """
            Tests the status code that is returned when the login page is requested.
        """
        url = reverse('login')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_signup_view_status_code(self):
        """
            Tests the status code that is returned when the signup page is requested.
        """
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_account_info_view_status_code(self):
        """
            Tests the status code that is returned when the account info page is requested.
        """
        url = reverse('account_info')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_password_change_view_status_code(self):
        """
            Tests the status code that is returned when the password change page is requested.
        """
        url = reverse('password_change')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        
    def test_home_view_func(self):
        """
            Tests that the function resolved when the home page is requested is the correct one.
        """
        view = resolve('/')
        self.assertEquals(view.func, views.home)
        
    def test_saved_results_view_func(self):
        """
            Tests that the function resolved when the saved results page is requested is the correct one.
        """
        view = resolve('/saved_results/')
        self.assertEquals(view.func, views.saved_results)
        
    def test_sna_viz_view_func(self):
        """
            Tests that the function resolved when the SNA and Visualization page is requested is the correct one.
        """
        view = resolve('/sna_viz/')
        self.assertEquals(view.func, views.sna_viz)
        
    def test_dataset_cntr_view_func(self):
        """
            Tests that the function resolved when the dataset constructor page is requested is the correct one.
        """
        view = resolve('/dataset_cntr/')
        self.assertEquals(view.func, views.dataset_constructor)
        
    def test_help_view_func(self):
        """
            Tests that the function resolved when the help page is requested is the correct one.
        """
        view = resolve('/help/')
        self.assertEquals(view.func, views.help_page)
        
    def test_home_contains(self):
        """
            Tests that the home page constains the expected information.
        """
        url = reverse('home')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        self.assertContains(response, "If results don't automatically populate in the table below please ref")
        self.assertContains(response, 'Num Results: 0')
        
    def test_sna_viz_contains(self):
        """
            Tests that the SNA and Visualization page constains the expected information.
        """
        url = reverse('sna_viz')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_data_cntr_contains(self):
        """
            Tests that the dataset constructor page constains the expected information.
        """
        url = reverse('dataset_cntr')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_saved_results_contains(self):
        """
            Tests that the saved results page constains the expected information.
        """
        url = reverse('saved_results')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_help_contains(self):
        """
            Tests that the help page constains the expected information.
        """
        url = reverse('help_page')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_account_info_contains(self):
        """
            Tests that the account info page constains the expected information.
        """
        url = reverse('account_info')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_pass_change_contains(self):
        """
            Tests that the password change page constains the expected information.
        """
        url = reverse('password_change')
        response = self.client.get(url)
        self.assertContains(response, 'href="/saved_results/"')
        self.assertContains(response, 'href="/help/"')
        self.assertContains(response, 'href="/dataset_cntr/"')
        self.assertContains(response, 'href="/sna_viz/"')
        
    def test_get_saved_results(self):
        """
            Tests that a saved result can be extracted.
        """
        url = reverse('get_saved_result')
        a = models.Source(source='test', user=self.user)
        a.save()
        b = models.ExtractedRelation(ckpt='aa', sentence='aa', head='a', tail='a', pred_relation='a', conf=0, sentiment='a', source=a)
        b.save()
        response = self.client.get(url, {'source_id':a.source_id})
        self.assertContains(response, 'data')
        self.assertContains(response, 'aa')
        
class LoginRequiredTests(TestCase):
    """
        Tests for making sure that a user must be logged in.
    """
    def setUp(self):
        """
            Sets up for the test.
        """
        self.url = reverse('help_page')
        self.response = self.client.get(self.url)

    def test_redirection(self):
        """
            Tests that if the user is not logged in, they will be redirected to the login page.
        """
        login_url = reverse('login')
        self.assertRedirects(self.response, '{login_url}?next={url}'.format(login_url=login_url, url=self.url))