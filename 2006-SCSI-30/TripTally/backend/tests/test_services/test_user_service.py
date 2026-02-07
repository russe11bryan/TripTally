import pytest
from app.models.account import User
from app.schemas.user import UserCreate
from app.services import user_service


class FakeUserRepo:
    """In-memory fake implementing the UserRepository protocol for unit tests."""
    def __init__(self):
        self._users = {}
        self._next = 1

    def add(self, user: User) -> User:
        user.id = self._next
        self._next += 1
        # store a shallow copy
        self._users[user.id] = User(**user.__dict__)
        return self._users[user.id]

    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        for u in self._users.values():
            if u.email == email:
                return u
        return None

    def list(self) -> list[User]:
        return list(self._users.values())

    def update(self, user: User) -> User:
        if user.id in self._users:
            self._users[user.id] = User(**user.__dict__)
        return self._users.get(user.id)

    def delete(self, user_id: int) -> bool:
        return self._users.pop(user_id, None) is not None

    def add_saved_location(self, user_id: int, location_id: int) -> bool:
        u = self._users.get(user_id)
        if not u:
            return False
        if location_id in u.saved_locations:
            return False
        u.saved_locations.append(location_id)
        return True

    def remove_saved_location(self, user_id: int, location_id: int) -> bool:
        u = self._users.get(user_id)
        if not u:
            return False
        if location_id not in u.saved_locations:
            return False
        u.saved_locations.remove(location_id)
        return True

    def get_saved_locations(self, user_id: int) -> list[int]:
        u = self._users.get(user_id)
        if not u:
            return []
        return list(u.saved_locations)


def make_user_create(email="a@example.com", password="pw", display_name="User"):
    return UserCreate(email=email, password=password, display_name=display_name)


def test_create_user_success():
    repo = FakeUserRepo()
    payload = make_user_create()

    created = user_service.create_user(repo, payload)

    assert created.id > 0
    assert created.email == payload.email
    # password should not equal raw password (hashed)
    assert created.password != payload.password


def test_create_user_duplicate_email_raises():
    repo = FakeUserRepo()
    # pre-populate user
    existing = User(id=0, email="dup@example.com", password="x", display_name="X")
    repo.add(existing)

    payload = make_user_create(email="dup@example.com")

    with pytest.raises(ValueError):
        user_service.create_user(repo, payload)


def test_update_user_profile_email_conflict():
    repo = FakeUserRepo()
    u1 = repo.add(User(id=0, email="one@example.com", password="p", display_name="One"))
    u2 = repo.add(User(id=0, email="two@example.com", password="p", display_name="Two"))

    # attempt to update u2's email to u1's email should raise
    with pytest.raises(ValueError):
        user_service.update_user_profile(repo, u2.id, email="one@example.com")


def test_add_and_remove_saved_location_flow():
    repo = FakeUserRepo()
    u = repo.add(User(id=0, email="loc@example.com", password="p", display_name="L", saved_locations=[]))

    # add location
    ok = user_service.add_saved_location(repo, u.id, 42)
    assert ok is True
    assert 42 in repo.get_by_id(u.id).saved_locations

    # adding duplicate via service should raise
    with pytest.raises(ValueError):
        user_service.add_saved_location(repo, u.id, 42)

    # remove location
    ok = user_service.remove_saved_location(repo, u.id, 42)
    assert ok is True
    assert 42 not in repo.get_by_id(u.id).saved_locations

    # removing non-existent should raise
    with pytest.raises(ValueError):
        user_service.remove_saved_location(repo, u.id, 999)


def test_deactivate_and_delete_user():
    repo = FakeUserRepo()
    u = repo.add(User(id=0, email="del@example.com", password="p", display_name="Del"))

    # deactivate
    ok = user_service.deactivate_user_account(repo, u.id)
    assert ok is True
    assert repo.get_by_id(u.id).status == "deactivated"

    # delete permanently
    res = user_service.delete_user_permanently(repo, u.id)
    assert res is True
    assert repo.get_by_id(u.id) is None
