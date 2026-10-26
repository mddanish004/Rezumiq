import pytest
from django.utils import timezone

from accounts.models import User


@pytest.mark.django_db
def test_user_defaults():
    user = User.objects.create_user(username="amy", email="amy@example.com", password="x")
    assert user.plan == User.Plan.FREE
    assert not user.is_guest
    assert not user.is_suspended


@pytest.mark.django_db
def test_suspend_and_unsuspend():
    user = User.objects.create_user(username="raj", email="raj@example.com", password="x")
    user.suspend()
    assert user.is_suspended
    assert user.suspended_at <= timezone.now()

    user.unsuspend()
    assert not user.is_suspended
    assert user.suspended_at is None
