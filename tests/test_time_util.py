from datetime import datetime, timezone
from unittest.mock import patch
from shared.time_util import get_now


class TestGetNow:
    def test_returns_integer(self):
        result = get_now()
        assert isinstance(result, int)

    def test_returns_utc_timestamp(self):
        fixed_dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        expected = int(fixed_dt.timestamp())

        with patch("shared.time_util.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = get_now()

        assert result == expected

    def test_returns_recent_timestamp(self):
        before = int(datetime.now(timezone.utc).timestamp())
        result = get_now()
        after = int(datetime.now(timezone.utc).timestamp())
        assert before <= result <= after
