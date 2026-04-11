import json

from allauth.account import app_settings as allauth_account_settings
from allauth.account.forms import (
    AddEmailForm,
    ChangePasswordForm,
    LoginForm,
    ReauthenticateForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    SetPasswordForm,
    UserTokenForm,
)
from allauth.account.internal.flows import email_verification, manage_email, password_change, password_reset, reauthentication
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from allauth.account.utils import complete_signup
from allauth.socialaccount.forms import DisconnectForm
from allauth.socialaccount.internal.flows import connect as social_connect
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.forms import EnduroSignupForm

from accounts.models import CoachAthlete, Role


def _full_name(user) -> str:
    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    return user.username or user.email or ""


def _initials(full_name: str, email: str) -> str:
    name_parts = [part for part in full_name.split() if part]
    if len(name_parts) >= 2:
        return f"{name_parts[0][0]}{name_parts[1][0]}".upper()
    if len(name_parts) == 1:
        return name_parts[0][:2].upper()
    return (email[:2] or "EB").upper()


def _json_body(request) -> dict:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _form_errors(form) -> dict[str, list[str]]:
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


def _default_route_for_user(user) -> str:
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", Role.ATHLETE)
    has_incomplete_google_profile = bool(
        profile
        and SocialAccount.objects.filter(user=user, provider="google").exists()
        and not (
            getattr(profile, "google_profile_completed", False)
            and getattr(profile, "google_role_confirmed", False)
        )
    )
    if has_incomplete_google_profile:
        return "/app/profile/complete"
    return "/coach/plans" if role == Role.COACH else "/app/dashboard"


def _get_email_confirmation_or_none(key: str):
    confirmation = EmailConfirmationHMAC.from_key(key)
    if confirmation:
        return confirmation
    from allauth.account.models import EmailConfirmation

    return EmailConfirmation.from_key(key)


def _serialize_email_addresses(user) -> list[dict]:
    return [
        {
            "email": address.email,
            "verified": bool(address.verified),
            "primary": bool(address.primary),
            "can_delete": bool(manage_email.can_delete_email(address)),
            "can_mark_primary": bool(manage_email.can_mark_as_primary(address)),
        }
        for address in EmailAddress.objects.filter(user=user).order_by("email")
    ]


def _safe_redirect_target(request, fallback: str) -> str:
    candidate = ""
    if request.method == "GET":
        candidate = str(request.GET.get("next") or "").strip()
    else:
        candidate = str(_json_body(request).get("next") or "").strip()

    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


def _serialize_social_accounts(user) -> list[dict]:
    accounts = SocialAccount.objects.filter(user=user).select_related("user")
    serialized = []
    for account in accounts:
        provider_account = account.get_provider_account()
        brand = provider_account.get_brand()
        serialized.append(
            {
                "id": account.pk,
                "provider": account.provider,
                "provider_name": provider_account.get_provider().name,
                "brand_name": brand.name,
                "label": str(provider_account),
                "uid": account.uid,
            }
        )
    return serialized


@login_required
def auth_me(request):
    user = request.user
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", Role.ATHLETE)
    full_name = _full_name(user)
    default_app_route = "/coach/plans" if role == Role.COACH else "/app/dashboard"
    coached_athlete_count = 0
    garmin_connection = None
    try:
        garmin_connection = user.garmin_connection
    except ObjectDoesNotExist:
        garmin_connection = None
    if role == Role.COACH:
        coached_athlete_count = CoachAthlete.objects.filter(
            coach=user,
            hidden_from_plans=False,
        ).count()

    payload = {
        "id": user.id,
        "full_name": full_name,
        "email": user.email,
        "role": role,
        "initials": _initials(full_name, user.email or ""),
        "capabilities": {
            "can_view_coach": role == Role.COACH,
            "can_view_athlete": True,
            "can_complete_profile": bool(profile and not profile.google_profile_completed),
            "has_garmin_connection": bool(garmin_connection and garmin_connection.is_active),
            "garmin_connect_enabled": bool(getattr(settings, "GARMIN_CONNECT_ENABLED", False)),
            "garmin_sync_enabled": bool(getattr(settings, "GARMIN_SYNC_ENABLED", False)),
            "coached_athlete_count": coached_athlete_count,
        },
        "default_app_route": default_app_route,
    }
    return JsonResponse(payload)


@require_http_methods(["POST"])
def auth_login(request):
    payload = _json_body(request)
    form = LoginForm(
        data={
            "login": payload.get("email", ""),
            "password": payload.get("password", ""),
            "remember": bool(payload.get("remember")),
        },
        request=request,
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Prihlaseni se nepodarilo. Zkontroluj e-mail a heslo.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.login(request)
    user = form.user
    return JsonResponse(
        {
            "ok": True,
            "message": "Prihlaseni probehlo uspesne.",
            "redirect_to": _default_route_for_user(user),
            "user": {
                "email": user.email,
                "full_name": _full_name(user),
            },
        }
    )


@require_http_methods(["POST"])
def auth_signup(request):
    payload = _json_body(request)
    form = EnduroSignupForm(
        data={
            "first_name": payload.get("first_name", ""),
            "last_name": payload.get("last_name", ""),
            "role": payload.get("role", Role.ATHLETE),
            "email": payload.get("email", ""),
            "password1": payload.get("password", ""),
            "password2": payload.get("password_confirmation", ""),
        }
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Registraci se nepodarilo dokoncit. Oprav prosim oznacena pole.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    user, _ = form.try_save(request)
    if user is not None:
        complete_signup(
            request,
            user,
            allauth_account_settings.EMAIL_VERIFICATION,
            "/accounts/confirm-email/",
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "Registrace probehla. Zkontroluj e-mail a potvrz adresu.",
            "redirect_to": "/accounts/confirm-email/",
        }
    )


@require_http_methods(["POST"])
def auth_password_reset(request):
    form = ResetPasswordForm(data={"email": _json_body(request).get("email", "")})
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Obnovu hesla se nepodarilo zahajit. Zkontroluj e-mail.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.save(request)
    return JsonResponse(
        {
            "ok": True,
            "message": "Pokud ucet existuje, poslali jsme odkaz pro obnovu hesla.",
            "redirect_to": "/accounts/password/reset/done/",
        }
    )


@require_http_methods(["POST"])
def auth_logout_view(request):
    auth_logout(request)
    return JsonResponse(
        {
            "ok": True,
            "message": "Odhlaseni probehlo uspesne.",
            "redirect_to": "/accounts/login/",
        }
    )


@require_http_methods(["GET", "POST"])
def auth_email_confirm(request, key: str):
    confirmation = _get_email_confirmation_or_none(key)
    if request.method == "GET":
        if not confirmation:
            return JsonResponse(
                {
                    "ok": False,
                    "can_confirm": False,
                    "message": "Tento potvrzovaci odkaz vyprsel nebo je neplatny.",
                },
                status=404,
            )

        email_address = confirmation.email_address
        return JsonResponse(
            {
                "ok": True,
                "can_confirm": bool(email_address.can_set_verified()),
                "email": email_address.email,
                "user": {
                    "display": _full_name(email_address.user),
                },
            }
        )

    if not confirmation:
        return JsonResponse(
            {
                "ok": False,
                "message": "Tento potvrzovaci odkaz vyprsel nebo je neplatny.",
            },
            status=404,
        )

    email_address, response = email_verification.verify_email_and_resume(request, confirmation)
    if response:
        return JsonResponse(
            {
                "ok": True,
                "message": "E-mail byl potvrzen.",
                "redirect_to": response.url if hasattr(response, "url") else _default_route_for_user(request.user),
            }
        )
    if not email_address:
        return JsonResponse(
            {
                "ok": False,
                "message": "E-mail se nepodarilo potvrdit.",
            },
            status=400,
        )

    return JsonResponse(
        {
            "ok": True,
            "message": "E-mail byl potvrzen.",
            "redirect_to": _default_route_for_user(email_address.user),
        }
    )


@require_http_methods(["GET", "POST"])
def auth_password_reset_from_key(request, uidb36: str, key: str):
    actual_key = key
    if key == "set-password":
        actual_key = request.session.get("_password_reset_key", "")

    token_form = UserTokenForm(data={"uidb36": uidb36, "key": actual_key})
    token_is_valid = bool(actual_key) and token_form.is_valid()

    if request.method == "GET":
        if key != "set-password" and token_is_valid:
            request.session["_password_reset_key"] = actual_key
            return JsonResponse(
                {
                    "ok": True,
                    "token_valid": True,
                    "redirect_to": f"/accounts/password/reset/key/{uidb36}-set-password/",
                }
            )

        if not token_is_valid:
            return JsonResponse(
                {
                    "ok": False,
                    "token_valid": False,
                    "message": "Tento odkaz pro obnovu hesla uz neni platny.",
                },
                status=400,
            )

        return JsonResponse(
            {
                "ok": True,
                "token_valid": True,
                "message": "Muzes nastavit nove heslo.",
            }
        )

    if not token_is_valid:
        return JsonResponse(
            {
                "ok": False,
                "message": "Tento odkaz pro obnovu hesla uz neni platny.",
            },
            status=400,
        )

    payload = _json_body(request)
    form = ResetPasswordKeyForm(
        data={
            "password1": payload.get("password", ""),
            "password2": payload.get("password_confirmation", ""),
        },
        user=token_form.reset_user,
        temp_key=actual_key,
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Oprav prosim oznacena pole.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.save()
    password_reset.finalize_password_reset(request, token_form.reset_user)
    return JsonResponse(
        {
            "ok": True,
            "message": "Heslo bylo zmeneno.",
            "redirect_to": "/accounts/password/reset/key/done/",
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def auth_email_addresses(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "emails": _serialize_email_addresses(request.user),
                "can_add_email": EmailAddress.objects.can_add_email(request.user),
                "current_email": request.user.email,
            }
        )

    payload = _json_body(request)
    action = str(payload.get("action") or "").strip()
    selected_email = str(payload.get("email") or "").strip().lower()

    if action == "add":
        form = AddEmailForm(data={"email": payload.get("new_email", "")}, user=request.user)
        if not form.is_valid():
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Novy e-mail se nepodarilo pridat.",
                    "errors": _form_errors(form),
                },
                status=400,
            )
        manage_email.add_email(request, form)
        return JsonResponse(
            {
                "ok": True,
                "message": "E-mail byl pridan.",
                "emails": _serialize_email_addresses(request.user),
                "redirect_to": "/accounts/email/",
            }
        )

    try:
        email_address = EmailAddress.objects.get_for_user(request.user, selected_email)
    except EmailAddress.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "message": "Vybrany e-mail se nepodarilo najit.",
            },
            status=404,
        )

    if action == "primary":
        success = manage_email.mark_as_primary(request, email_address)
        if not success:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Tento e-mail nelze nastavit jako primarni.",
                },
                status=400,
            )
        return JsonResponse(
            {
                "ok": True,
                "message": "Primarni e-mail byl zmenen.",
                "emails": _serialize_email_addresses(request.user),
                "redirect_to": "/accounts/email/",
            }
        )

    if action == "send":
        did_send = email_verification.send_verification_email_to_address(request, email_address)
        return JsonResponse(
            {
                "ok": True,
                "message": "Ověřovací e-mail byl odeslán." if did_send else "Ověřovací e-mail se nepodařilo odeslat.",
                "emails": _serialize_email_addresses(request.user),
                "redirect_to": "/accounts/confirm-email/" if did_send else "/accounts/email/",
            }
        )

    if action == "remove":
        success = manage_email.delete_email(request, email_address)
        if not success:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Tento e-mail nelze odebrat.",
                },
                status=400,
            )
        return JsonResponse(
            {
                "ok": True,
                "message": "E-mail byl odebran.",
                "emails": _serialize_email_addresses(request.user),
                "redirect_to": "/accounts/email/",
            }
        )

    return JsonResponse(
        {
            "ok": False,
            "message": "Neznama akce.",
        },
        status=400,
    )


@login_required
@require_http_methods(["POST"])
def auth_password_change(request):
    payload = _json_body(request)
    form = ChangePasswordForm(
        data={
            "oldpassword": payload.get("current_password", ""),
            "password1": payload.get("password", ""),
            "password2": payload.get("password_confirmation", ""),
        },
        user=request.user,
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Zmenu hesla se nepodarilo ulozit.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.save()
    password_change.finalize_password_change(request, request.user)
    return JsonResponse(
        {
            "ok": True,
            "message": "Heslo bylo zmeneno.",
            "redirect_to": _default_route_for_user(request.user),
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def auth_password_set(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "has_usable_password": bool(request.user.has_usable_password()),
                "redirect_to": "/accounts/password/change/" if request.user.has_usable_password() else "",
            }
        )

    payload = _json_body(request)
    form = SetPasswordForm(
        data={
            "password1": payload.get("password", ""),
            "password2": payload.get("password_confirmation", ""),
        },
        user=request.user,
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Nastaveni hesla se nepodarilo ulozit.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.save()
    password_change.finalize_password_set(request, request.user)
    return JsonResponse(
        {
            "ok": True,
            "message": "Heslo bylo nastaveno.",
            "redirect_to": _default_route_for_user(request.user),
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def auth_social_connections(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "accounts": _serialize_social_accounts(request.user),
                "connect_google_url": "/accounts/google/login/?process=connect",
            }
        )

    payload = _json_body(request)
    account_id = payload.get("account_id")
    try:
        account = SocialAccount.objects.get(pk=account_id, user=request.user)
    except SocialAccount.DoesNotExist:
        return JsonResponse(
            {
                "ok": False,
                "message": "Vybrany externi ucet se nepodarilo najit.",
            },
            status=404,
        )

    form = DisconnectForm(data={"account": account.pk}, request=request)
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Tento externi ucet nelze odpojit.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    form.save()
    return JsonResponse(
        {
            "ok": True,
            "message": "Externi ucet byl odpojen.",
            "accounts": _serialize_social_accounts(request.user),
            "redirect_to": "/accounts/social/connections/",
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def auth_reauthenticate(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "ok": True,
                "next": _safe_redirect_target(request, _default_route_for_user(request.user)),
                "has_usable_password": bool(request.user.has_usable_password()),
            }
        )

    payload = _json_body(request)
    form = ReauthenticateForm(data={"password": payload.get("password", "")}, user=request.user)
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Potvrzeni pristupu se nepodarilo.",
                "errors": _form_errors(form),
            },
            status=400,
        )

    reauthentication.reauthenticate_by_password(request)
    return JsonResponse(
        {
            "ok": True,
            "message": "Pristup byl potvrzen.",
            "redirect_to": _safe_redirect_target(request, _default_route_for_user(request.user)),
        }
    )
