"""The /v1/me lifecycle, ported from modules/users (users.service.ts)."""

from django.db import transaction
from django.utils import timezone

from api.common.errors import ConflictError
from api.common.guards import email_verified, is_admin

from .models import UsernameRedirect
from .usernames import is_reserved_username, is_username_taken, username_cooldown_end


def me_fields(user) -> dict:
    """The public shape of a user row, shared by /me and the data export.

    Keys are the camelCase wire names, so both the export (raw JSON) and
    MeOut (validated, alias-serialized) emit the same contract.
    """
    return {
        "id": user.pk,
        "name": user.name,
        "email": user.email,
        "emailVerified": email_verified(user),
        "image": user_image(user),
        "username": user.username,
        "plan": user.plan,
        "isAnonymous": user.is_guest,
        "createdAt": user.date_joined,
    }


def with_admin(user) -> dict:
    """Only /me responses carry isAdmin; the export reports the plain shape."""
    fields = me_fields(user)
    fields["isAdmin"] = is_admin(user)
    return fields


def user_image(user) -> str | None:
    """The avatar carries over from the Google account if there is one; guests
    and password accounts have none."""
    accounts = user.socialaccount_set.filter(provider="google")
    account = accounts.first()
    if account:
        return (account.extra_data or {}).get("picture")
    return None


@transaction.atomic
def update_me(user, *, name: str | None = None, username: str | None = None) -> dict:
    """Name is a display field; a username change has a cooldown, keeps old names
    reserved for the owner, and takes back the user's own old names."""
    changes: dict = {}

    if name:
        changes["name"] = name

    if username and username != user.username:
        cooldown = username_cooldown_end(user.username_changed_at)
        if cooldown:
            formatted = cooldown.strftime("%d %B %Y")
            raise ConflictError(f"You can change your username again after {formatted}.")
        if is_reserved_username(username):
            raise ConflictError("This username is reserved")

        own = UsernameRedirect.objects.filter(old_username=username, user=user).first()
        if own:
            own.delete()
        elif is_username_taken(username):
            raise ConflictError("This username is taken")

        UsernameRedirect.objects.create(old_username=user.username, user=user)
        changes["username"] = username
        changes["username_changed_at"] = timezone.now()

    if not changes:
        return me_fields(user)

    for key, value in changes.items():
        setattr(user, key, value)
    user.save(update_fields=list(changes.keys()))
    return me_fields(user)


def delete_me(user) -> None:
    user.delete()


def export_my_data(user) -> dict:
    from resumes.models import Profile

    profile = Profile.objects.filter(user=user).first()
    return {
        "exportedAt": timezone.now(),
        "account": me_fields(user),
        "profile": profile.data if profile else None,
    }
