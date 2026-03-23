from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from urllib.parse import urlencode

from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.account.models import EmailAddress
from allauth.core import context
from allauth.socialaccount.internal.flows.login import complete_login
from allauth.socialaccount.models import SocialAccount, SocialLogin

from accounts.models import Role


class GoogleProfileCompletionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.factory = RequestFactory()

    def test_google_user_without_names_is_redirected_to_completion(self):
        user = self.User.objects.create_user(
            username="google-athlete",
            email="google@example.com",
            password="unused-pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-athlete")

        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('account_complete_profile')}?{urlencode({'next': reverse('dashboard_home')})}",
        )

    def test_regular_user_without_names_is_not_redirected(self):
        user = self.User.objects.create_user(
            username="email-athlete",
            email="email@example.com",
            password="test-pass-123",
        )

        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 200)

    def test_google_user_with_complete_name_but_unconfirmed_is_still_redirected(self):
        user = self.User.objects.create_user(
            username="google-complete",
            email="google-complete@example.com",
            password="unused-pass",
            first_name="Jan",
            last_name="Novak",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-complete")

        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('account_complete_profile')}?{urlencode({'next': reverse('dashboard_home')})}",
        )

    def test_completion_form_saves_names_and_redirects_back(self):
        user = self.User.objects.create_user(
            username="google-finish",
            email="google-finish@example.com",
            password="unused-pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-finish")

        self.client.force_login(user)
        response = self.client.post(
            reverse("account_complete_profile"),
            data={
                "first_name": "Petr",
                "last_name": "Svoboda",
                "role": Role.COACH,
                "next": reverse("dashboard_home"),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_home"))
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Petr")
        self.assertEqual(user.last_name, "Svoboda")
        self.assertEqual(user.profile.role, Role.COACH)
        self.assertTrue(user.profile.google_profile_completed)
        self.assertTrue(user.profile.google_role_confirmed)
        self.assertTrue(user.profile.coach_join_code)

    def test_completion_page_is_accessible_for_redirected_google_user(self):
        user = self.User.objects.create_user(
            username="google-onboarding",
            email="google-onboarding@example.com",
            password="unused-pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-onboarding")

        self.client.force_login(user)

        response = self.client.get(reverse("account_complete_profile"))

        self.assertEqual(response.status_code, 200)

    def test_google_user_with_confirmed_profile_is_not_redirected(self):
        user = self.User.objects.create_user(
            username="google-confirmed",
            email="google-confirmed@example.com",
            password="unused-pass",
            first_name="Jan",
            last_name="Novak",
        )
        user.profile.google_profile_completed = True
        user.profile.google_role_confirmed = True
        user.profile.save(update_fields=["google_profile_completed", "google_role_confirmed"])
        SocialAccount.objects.create(user=user, provider="google", uid="google-confirmed")

        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 200)

    def test_allauth_complete_login_creates_user_and_followup_request_requires_completion(self):
        sociallogin = self._build_sociallogin(
            uid="google-first-login",
            email="google-first-login@example.com",
            first_name="Google",
            last_name="Runner",
        )
        request = self._build_request(path="/accounts/google/login/callback/")

        with context.request_context(request):
            response = complete_login(request, sociallogin)

        self.assertEqual(response.status_code, 302)
        created_user = self.User.objects.get(email="google-first-login@example.com")
        self.assertTrue(
            SocialAccount.objects.filter(
                user=created_user,
                provider="google",
                uid="google-first-login",
            ).exists()
        )
        self.assertFalse(created_user.profile.google_profile_completed)
        self.assertFalse(created_user.profile.google_role_confirmed)

        self.client.force_login(created_user)
        dashboard_response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertEqual(
            dashboard_response.url,
            f"{reverse('account_complete_profile')}?{urlencode({'next': reverse('dashboard_home')})}",
        )

    def test_authenticated_unconfirmed_google_user_can_logout(self):
        user = self.User.objects.create_user(
            username="google-logout",
            email="google-logout@example.com",
            password="unused-pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-logout")

        self.client.force_login(user)

        response = self.client.post(reverse("account_logout"))

        self.assertEqual(response.status_code, 302)
        followup = self.client.get(reverse("dashboard_home"))
        self.assertEqual(followup.status_code, 302)
        self.assertIn(reverse("account_login"), followup.url)

    def test_authenticated_unconfirmed_google_user_visiting_login_is_redirected_to_completion(self):
        user = self.User.objects.create_user(
            username="google-login-page",
            email="google-login-page@example.com",
            password="unused-pass",
        )
        SocialAccount.objects.create(user=user, provider="google", uid="google-login-page")

        self.client.force_login(user)

        response = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('account_complete_profile')}?{urlencode({'next': reverse('account_login')})}",
        )

    def test_anonymous_user_can_open_login_page(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)

    def test_google_user_with_old_completion_but_unconfirmed_role_is_redirected(self):
        user = self.User.objects.create_user(
            username="google-old-completion",
            email="google-old-completion@example.com",
            password="unused-pass",
            first_name="Old",
            last_name="User",
        )
        user.profile.google_profile_completed = True
        user.profile.google_role_confirmed = False
        user.profile.save(update_fields=["google_profile_completed", "google_role_confirmed"])
        SocialAccount.objects.create(user=user, provider="google", uid="google-old-completion")

        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{reverse('account_complete_profile')}?{urlencode({'next': reverse('dashboard_home')})}",
        )

    def test_email_signup_persists_selected_role(self):
        response = self.client.post(
            reverse("account_signup"),
            data={
                "first_name": "Coach",
                "last_name": "User",
                "role": Role.COACH,
                "email": "coach-signup@example.com",
                "password1": "strong-pass-12345",
                "password2": "strong-pass-12345",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = self.User.objects.get(email="coach-signup@example.com")
        self.assertEqual(user.profile.role, Role.COACH)
        self.assertTrue(user.profile.coach_join_code)

    def _build_request(self, *, path: str):
        request = self.factory.get(path, HTTP_HOST="localhost")
        request.user = AnonymousUser()
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def _build_sociallogin(self, *, uid: str, email: str, first_name: str, last_name: str) -> SocialLogin:
        user = self.User(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        account = SocialAccount(
            provider="google",
            uid=uid,
            extra_data={
                "email": email,
                "given_name": first_name,
                "family_name": last_name,
            },
        )
        account.user = user
        email_address = EmailAddress(email=email, verified=True, primary=True)
        sociallogin = SocialLogin(
            user=user,
            account=account,
            email_addresses=[email_address],
        )
        provider = get_social_adapter().get_provider(self._build_request(path="/accounts/google/login/callback/"), "google")
        sociallogin.provider = provider
        sociallogin.account._provider = provider
        sociallogin.state = {"process": "login", "next": reverse("dashboard_home")}
        return sociallogin
