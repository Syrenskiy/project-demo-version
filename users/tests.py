from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

# Test case classes for user registration and login functionality.


class RegisterUserTestCase(TestCase):
    """Test cases for user registration functionality."""

    def setUp(self):
        """Set up initial data for registration tests."""
        self.data = {
            'username': 'testuser',
            'email': 'testemail@gmail.com',
            'password1': 'testpassword',
            'password2': 'testpassword'
        }

        self.user_model = get_user_model()

    def test_registration_get(self):
        """Verify registration page can be accessed."""
        path = reverse('users:register')
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, template_name='users/register.html')

    def test_registration_success(self):
        """Test successful registration redirects to confirmation and creates user."""
        path = reverse('users:register')
        response = self.client.post(path, self.data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('users:register_done'))
        self.assertTrue(self.user_model.objects.filter(username=self.data['username']).exists())

    def test_registration_sends_email(self):
        """Ensure a welcome email is sent upon successful registration."""
        path = reverse('users:register')
        response = self.client.post(path, self.data)

        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)

        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Princess Castle')  # Check subject
        self.assertIn(self.data['email'], sent_email.to)
        self.assertIn('Registro exitoso.\n\nBienvenido(a) a la familia Princess Castle!', sent_email.body)  # Check the content of the email

    def test_registration_missing_fields(self):
        """Check registration fails if required fields are missing."""
        path = reverse('users:register')
        required_message = 'Este campo es requerido.'

        # Check each required field
        for field in self.data.keys():
            # Copy data so as not to change the original dictionary
            data_copy = self.data.copy()
            data_copy[field] = ''  # Skip the current field

            response = self.client.post(path, data_copy)

            self.assertEqual(response.status_code, HTTPStatus.OK)

            self.assertContains(response, required_message)

    def test_registration_password_mismatch(self):
        """Ensure registration fails if passwords do not match."""
        self.data['password2'] = 'wrongpassword'

        path = reverse('users:register')
        response = self.client.post(path, self.data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Los dos campos de contraseña no coinciden.')

    def test_registration_existing_user(self):
        """Check registration fails if the username already exists."""
        self.user_model.objects.create_user(username=self.data['username'])
        path = reverse('users:register')
        response = self.client.post(path, self.data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Ya existe un usuario con este nombre.')

    def test_registration_existing_email(self):
        """Ensure registration fails if email is already used."""
        self.user_model.objects.create_user(username='testuser2', email=self.data['email'])
        path = reverse('users:register')
        response = self.client.post(path, self.data)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Este correo electrónico ya existe')


class LoginUserTestCase(TestCase):
    """Test cases for user login functionality."""
    def setUp(self):
        """Set up initial data for login tests."""
        self.data = {
            'username': 'testuser',
            'email': 'testemail@gmail.com',
            'password': 'testpassword',
        }

        self.user_model = get_user_model()
        self.user_model.objects.create_user(username=self.data['username'],
                                            email=self.data['email'],
                                            password=self.data['password'])

    def test_login_get(self):
        """Verify login page can be accessed."""
        path = reverse('users:login')
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, template_name='users/login.html')

    def test_login_with_username_success(self):
        """Ensure login is successful with correct username and password."""
        path = reverse('users:login')
        response = self.client.post(path, {'username': self.data['username'],
                                           'password': self.data['password']})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_email_success(self):
        """Ensure login is successful with correct email and password."""
        path = reverse('users:login')
        response = self.client.post(path, {'username': self.data['email'],
                                           'password': self.data['password']})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('home'))

    def test_login_with_invalid_username(self):
        """Check login fails if username is invalid."""
        path = reverse('users:login')
        response = self.client.post(path, {'username': 'wrongusername',
                                           'password': self.data['password']})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response,'Por favor, introduzca un nombre de usuario y clave correctos.')

    def test_login_with_invalid_password(self):
        """Check login fails if password is incorrect."""
        path = reverse('users:login')
        response = self.client.post(path, {'username': self.data['username'],
                                           'password': 'wrongpassword'})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response,'Por favor, introduzca un nombre de usuario y clave correctos.')

    def test_logout_success(self):
        """Ensure logout is successful and redirects to home page."""
        # Log in via POST
        login_path = reverse('users:login')
        self.client.post(login_path, {'username': self.data['username'], 'password': self.data['password']})

        # Log out via POST
        logout_path = reverse('users:logout')
        response = self.client.post(logout_path)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('home'))

        # Verify user is logged out
        response = self.client.get(reverse('home'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
