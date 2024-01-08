"""Test utils and common stuff."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from unittest.mock import patch

from pypaperless import Paperless
from pypaperless.util import (
    create_url_from_input,
    dataclass_from_dict,
    dataclass_to_dict,
    update_dataclass,
)


async def test_dataclass_conversion():
    """Test dataclass utils."""

    class _Status(Enum):
        """Test enum."""

        ACTIVE = 1
        INACTIVE = 2
        UNKNOWN = -1

        @classmethod
        def _missing_(cls: type, value: object):  # noqa ARG003
            """Set default."""
            return cls.UNKNOWN

    @dataclass
    class _AnotherPerson:
        """Test class."""

        name: str
        age: int

    @dataclass
    class _Person:
        """Test class."""

        name: str
        age: int
        height: float
        birth: date
        last_login: datetime
        friends: list[_AnotherPerson] | None
        deleted: datetime | None
        is_deleted: bool
        status: _Status
        file: bytes

    raw_data = {
        "name": "Lee Tobi, Sajangnim",
        "age": 38,
        "height": 1.76,
        "birth": "1986-05-23",
        "last_login": "2023-08-08T06:06:35.495972Z",
        "is_deleted": False,
        "friends": [
            {
                "name": "Erika",
                "age": "50",  # this should be int, check "back conversion" at bottom
            },
            {
                "name": "Reinhard",
                "age": 40,
            },
        ],
        "status": 1,
        "file": b"5-23-42-666-0815-1337",
    }

    res = dataclass_from_dict(_Person, raw_data)

    assert isinstance(res.name, str)
    assert isinstance(res.age, int)
    assert isinstance(res.height, float)
    assert isinstance(res.birth, date)
    assert isinstance(res.last_login, datetime)
    assert isinstance(res.friends, list)
    assert isinstance(res.friends[0], _AnotherPerson)
    assert isinstance(res.friends[0].age, int)
    assert isinstance(res.friends[1].age, int)
    assert res.deleted is None
    assert res.is_deleted is False
    assert isinstance(res.status, _Status)
    assert isinstance(res.file, bytes)

    update_dataclass(
        res,
        {
            "deleted": datetime.now(),
            "is_deleted": True,
        },
    )

    assert isinstance(res.deleted, datetime)
    assert res.is_deleted

    assert res.status == _Status.ACTIVE
    update_dataclass(res, {"status": 100})
    assert isinstance(res.status, _Status)
    assert res.status == _Status.UNKNOWN

    # back conversion
    back = dataclass_to_dict(res)

    assert isinstance(back["friends"][0]["age"], int)  # was str in the source dict


async def test_paperless(paperless: Paperless, data):
    """Test Paperless object."""
    assert paperless.url.host == "local.test"
    assert paperless.url.port == 1337
    assert paperless.is_initialized

    # okay, lets make a real request
    async with paperless.generate_request("get", "https://www.google.com", ssl=True) as req:
        assert req.status == 200

    # fetch an example json
    json = await paperless.request_json("get", "https://cat-fact.herokuapp.com/facts/", ssl=False)
    assert len(json) > 0

    # fetch an example content
    content = await paperless.request_file("get", "https://www.google.com", ssl=True)
    assert len(content) > 0

    # test another paperless in context and with request opts
    paperless2 = Paperless("local.test:1337", "another-secret-key", request_opts={"ssl": False})

    with patch.object(paperless2, "request_json", return_value=data["endpoints"]):
        async with paperless2:
            assert paperless2.is_initialized


async def test_url_creation():
    """Test url creation."""
    # test default ssl
    url = create_url_from_input("hostname")
    assert url.host == "hostname"
    assert url.port == 443

    # test if api-path is added
    assert url.name == "api"

    # test full url string
    assert f"{url}" == "https://hostname/api"

    # test enforce http
    url = create_url_from_input("http://hostname")
    assert url.port == 80

    # should be https even on just setting a port number
    url = create_url_from_input("hostname:80")
    assert url.scheme == "https"

    # test api/api url
    url = create_url_from_input("hostname/api/api/")
    assert f"{url}" == "https://hostname/api/api"

    # test with path and check if "api" is added
    url = create_url_from_input("hostname/path/to/paperless")
    assert f"{url}" == "https://hostname/path/to/paperless/api"
