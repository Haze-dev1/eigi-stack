"""Create LRN accounts in a throwaway local database and print bearer tokens for them.

Run from a directory with no ``.env`` so nothing from ``backend/.env`` is loaded::

    cd "$(mktemp -d)" && \\
    MONGODB_URI="mongodb://localhost:27027/?directConnection=true" \\
    MONGODB_DATABASE=lrn_test_<stamp> JWT_SECRET=<same made-up secret as the API> \\
    PYTHONPATH=<repo>/backend <repo>/backend/.venv/bin/python \\
        <repo>/.claude/skills/lrn-test/scripts/seed_users.py [role:email ...]

Defaults to two students and one superadmin. Institution admins come from the real
onboarding → superadmin approval flow, which is itself a journey worth testing. Prints JSON
``[{role, email, user_id, token}]``; set ``localStorage.lrn_access_token`` to a token on the
frontend origin to sign in as that account. Refuses any non-local MongoDB.
"""

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from commons.auth import sign_token
from core.config.settings import get_settings
from core.cruds.user_crud import CRUDUser
from core.database.database import close_database, connect_database, get_database_engine
from core.models.user_model import User, UserRole, normalize_email

DEFAULT_USERS = [
    "student:student-a@lrn-qa.edu",
    "student:student-b@lrn-qa.edu",
    "superadmin:superadmin@lrn-qa.edu",
]
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


async def seed(specs: list[str]) -> list[dict[str, str]]:
    """Create each requested account unless it exists, then sign a one-day token for it.
    Existing accounts keep their data; only a missing role upgrade is applied.

    Args:
        specs: ``role:email`` pairs.

    Raises:
        SystemExit: If MongoDB is not local or a spec is malformed.
        RuntimeError: If the database or JWT secret is not configured.

    Returns:
        One record per account with its signed token.
    """
    settings = get_settings()
    host = urlsplit((settings.mongodb_uri or "").replace("mongodb://", "http://", 1)).hostname
    if host not in LOCAL_HOSTS:
        raise SystemExit(f"Refusing to seed non-local MongoDB host {host!r}")
    await connect_database()
    try:
        crud = CRUDUser()
        records = []
        for spec in specs:
            role_name, _, email = spec.partition(":")
            if not email or role_name not in {r.value for r in UserRole}:
                raise SystemExit(f"Expected role:email, got {spec!r}")
            role = UserRole(role_name)
            user = await crud.read_by_email(email=normalize_email(email))
            if user is None:
                now = datetime.now(UTC)
                user = User(email=email, role=role, created_at=now, updated_at=now)
                user = await get_database_engine().save(user)
            elif user.role != role:
                user = await crud.update_role(user_id=user.id, role=role) or user
            token = sign_token(
                {"sub": str(user.id), "session_version": user.session_version, "role": role.value},
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
            records.append(
                {"role": role.value, "email": user.email, "user_id": str(user.id), "token": token}
            )
        return records
    finally:
        await close_database()


def main() -> None:
    """Seed the accounts named on the command line, or the defaults, and print them as JSON.
    Exit non-zero on any refusal or database error.
    """
    print(json.dumps(asyncio.run(seed(sys.argv[1:] or DEFAULT_USERS)), indent=2))


if __name__ == "__main__":
    main()
