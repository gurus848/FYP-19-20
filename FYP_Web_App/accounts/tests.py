# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from django.contrib.auth.forms import UserCreationForm
from django.urls import resolve, reverse
from .views import signup
from django.contrib.auth.models import User

# accounts app tests.

class SignUpTests(TestCase):
    """
        Tests that sign up system.
    """
    def setUp(self):
        """
            Sets up for the test cases.
        """
        url = reverse('signup')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        """
            Tests that the response code when the signup page is requested is correct.
        """
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        """
            Test that the signup view function can be resolved correctly by Django.
        """
        view = resolve('/signup/')
        self.assertEquals(view.func, signup)

    def test_csrf(self):
        """
            Test that the response contains a CSRF token.
        """
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        """
            Tests that the form in the response is of the right type.
        """
        form = self.response.context.get('form')
        self.assertIsInstance(form, UserCreationForm)
        
    def test_form_inputs(self):
        """
            Test that the response webpage contains some important elements.
        """
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, 'type="password"', 2)

class SuccessfulSignUpTests(TestCase):
    """
        Tests the successful signup cases.
    """
    def setUp(self):
        """
            Sets up for the successful signup tests.
        """
        url = reverse('signup')
        data = {
            'username': 'john',
            'password1': 'abcdef123456',
            'password2': 'abcdef123456'
        }
        self.response = self.client.post(url, data)
        self.home_url = reverse('home')

    def test_redirection(self):
        """
            Tests that the user is redirected to the home page.
        """
        self.assertRedirects(self.response, self.home_url)

    def test_user_creation(self):
        """
            Tests that a user object has been created.
        """
        self.assertTrue(User.objects.exists())

    def test_user_authentication(self):
        """
            Tests that the system has detected that a user has been authenticated.
        """
        response = self.client.get(self.home_url)
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)
        
class InvalidSignUpTests(TestCase):
    """
        Tests the invalid signup cases.
    """
    def setUp(self):
        """
            Sets up for the test cases. Submits an invalid signup case.
        """
        url = reverse('signup')
        self.response = self.client.post(url, {})  # submit an empty dictionary

    def test_signup_status_code(self):
        """
            Tests the status code of the response.
        """
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        """
            Tests that the form submission indicated that it was invalid.
        """
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_dont_create_user(self):
        """
            Tests that a user has not been created.
        """
        self.assertFalse(User.objects.exists())