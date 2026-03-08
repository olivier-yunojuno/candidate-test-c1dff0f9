import datetime
import uuid
from contextlib import nullcontext
from unittest import mock

import pytest
from django.utils.timezone import now as tz_now

from visitors.models import InvalidVisitorPass, Visitor, VisitorLog

TEST_UUID: str = "68201321-9dd2-4fb3-92b1-24367f38a7d6"

TODAY: datetime.datetime = tz_now()
ONE_DAY: datetime.timedelta = datetime.timedelta(days=1)
TOMORROW: datetime.datetime = TODAY + ONE_DAY
YESTERDAY: datetime.datetime = TODAY - ONE_DAY


@pytest.mark.parametrize(
    "url_in,url_out",
    (
        ("google.com", f"google.com?vuid={TEST_UUID}"),
        ("google.com?vuid=123", f"google.com?vuid={TEST_UUID}"),
    ),
)
def test_visitor_tokenise(url_in, url_out):
    visitor = Visitor(uuid=uuid.UUID(TEST_UUID))
    assert visitor.tokenise(url_in) == url_out


@pytest.mark.django_db
def test_deactivate():
    visitor = Visitor.objects.create(email="foo@bar.com")
    assert visitor.is_active
    visitor.deactivate()
    assert not visitor.is_active
    visitor.refresh_from_db()
    assert not visitor.is_active


@pytest.mark.django_db
def test_reactivate():
    visitor = Visitor.objects.create(
        email="foo@bar.com", is_active=False, expires_at=YESTERDAY
    )
    assert not visitor.is_active
    assert visitor.has_expired
    assert not visitor.is_valid
    visitor.reactivate()
    assert visitor.is_active
    assert not visitor.has_expired
    assert visitor.is_valid
    visitor.refresh_from_db()
    assert visitor.is_active
    assert not visitor.has_expired
    assert visitor.is_valid


@pytest.mark.parametrize(
    "is_active,expires_at,can_still_be_used,is_valid",
    (
        (True, TOMORROW, True, True),
        (False, TOMORROW, True, False),
        (False, YESTERDAY, True, False),
        (True, YESTERDAY, True, False),
        (True, TOMORROW, False, False),
    ),
)
def test_validate(
    is_active: bool,
    expires_at: datetime.datetime,
    can_still_be_used: bool,
    is_valid: bool,
):
    visitor = Visitor(is_active=is_active, expires_at=expires_at)
    assert visitor.is_active == is_active
    assert visitor.has_expired == bool(expires_at < TODAY)
    validation_context = (
        nullcontext()
        if can_still_be_used
        else mock.patch("visitors.models.Visitor.can_still_be_used", return_value=False)
    )
    with validation_context:
        if is_valid:
            visitor.validate()
            return
        with pytest.raises(InvalidVisitorPass):
            visitor.validate()


@pytest.mark.parametrize(
    "is_active,expires_at,can_still_be_used,is_valid",
    (
        (True, TOMORROW, True, True),
        (False, TOMORROW, True, False),
        (False, YESTERDAY, True, False),
        (True, YESTERDAY, True, False),
        (True, None, True, True),
        (False, None, True, False),
        (True, TOMORROW, False, False),
    ),
)
def test_is_valid(
    is_active: bool,
    expires_at: datetime.datetime,
    can_still_be_used: bool,
    is_valid: bool,
):
    visitor = Visitor(is_active=is_active, expires_at=expires_at)
    validation_context = (
        nullcontext()
        if can_still_be_used
        else mock.patch("visitors.models.Visitor.can_still_be_used", return_value=False)
    )
    with validation_context:
        assert visitor.is_valid == is_valid


def test_defaults():
    visitor = Visitor()
    assert visitor.created_at
    assert visitor.expires_at == visitor.created_at + Visitor.DEFAULT_TOKEN_EXPIRY


@pytest.mark.parametrize(
    "expires_at,has_expired",
    (
        (TOMORROW, False),
        (YESTERDAY, True),
        (None, False),
    ),
)
def test_has_expired(expires_at, has_expired):
    visitor = Visitor()
    visitor.expires_at = expires_at
    assert visitor.has_expired == has_expired


@pytest.mark.django_db
@pytest.mark.parametrize(
    "visitor_logs_count,uses_count",
    (
        # We'll just test a couple of counts, to make sure they're correlated to
        # the number of VisitorLogs:
        (0, 0),
        (1, 1),
        (10, 10),
    ),
)
def test_uses_count(visitor_logs_count: int, uses_count: int):
    visitor = Visitor.objects.create()
    VisitorLog.objects.bulk_create(
        [VisitorLog(visitor=visitor) for _ in range(visitor_logs_count)],
    )
    assert visitor.uses_count() == uses_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    "maximum_uses,visitor_logs_count,can_still_be_used",
    (
        # unlimited uses first:
        (0, 0, True),
        (0, 10, True),
        # limited number of uses:
        (1, 0, True),
        (1, 1, False),  # the single use that was allowed was... used
        (2, 0, True),
        (2, 1, True),
        (2, 2, False),
    ),
)
def test_can_still_be_used(
    maximum_uses: int, visitor_logs_count: int, can_still_be_used: bool
):
    visitor = Visitor.objects.create(maximum_uses=maximum_uses)
    VisitorLog.objects.bulk_create(
        [VisitorLog(visitor=visitor) for _ in range(visitor_logs_count)],
    )
    assert visitor.can_still_be_used() == can_still_be_used
