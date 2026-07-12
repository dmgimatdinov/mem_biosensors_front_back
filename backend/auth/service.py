import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


_AUTH_CONNECTION: Optional[sqlite3.Connection] = None

from fastapi import HTTPException

import settings
from auth.rbac import (
    ROLE_KB_ADMIN,
    ROLE_SYSTEM,
    ROLE_VALIDATION_SPECIALIST,
    ROLE_DESIGNER,
)
from auth.rate_limit import RedisRateLimiter
from auth.security import (
    TokenPair,
    create_token_payload,
    decode_jwt,
    encode_jwt,
    generate_api_key,
    hash_api_key,
    hash_password,
    hash_token,
    verify_password,
)
import db.manager


def _auth_db_path() -> str:
    override = os.getenv("AUTH_DB_PATH", "").strip()
    if override:
        return override
    if os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("PYTEST_XDIST_WORKER") is not None or "pytest" in sys.modules or os.getenv("TESTING", "0") == "1":
        return ":memory:"
    return os.getenv("AUTH_DB_PATH", "auth_service.db")


def get_connection():
    global _AUTH_CONNECTION
    db_path = _auth_db_path()
    if db_path == ":memory:":
        if _AUTH_CONNECTION is None:
            _AUTH_CONNECTION = sqlite3.connect(db_path, check_same_thread=False)
            _AUTH_CONNECTION.execute("PRAGMA foreign_keys = ON")
        return _AUTH_CONNECTION
    try:
        return db.manager.get_connection()
    except Exception:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


@dataclass
class Principal:
    username: str
    role: str
    auth_type: str


class AuthService:
    def __init__(self):
        self.auth_mode = settings.AUTH_MODE
        self.jwt_secret = settings.JWT_SECRET
        self.access_ttl = settings.JWT_ACCESS_TTL_SECONDS
        self.refresh_ttl = settings.JWT_REFRESH_TTL_SECONDS
        self.user_rate_limit = settings.RATE_LIMIT_USER_PER_MIN
        self.synthesis_rate_limit = settings.RATE_LIMIT_SYNTHESIS_PER_HOUR
        self.rate_limiter = RedisRateLimiter(settings.REDIS_URL)
        self.ensure_auth_tables()
        self.ensure_bootstrap_users()

    def ensure_auth_tables(self) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS AuthUsers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(128) UNIQUE NOT NULL,
                    password_hash VARCHAR(512) NOT NULL,
                    role VARCHAR(64) NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_service_account INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS AuthRefreshTokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash VARCHAR(128) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    revoked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES AuthUsers (id)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS AuthApiKeys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    key_prefix VARCHAR(32) NOT NULL,
                    key_hash VARCHAR(128) UNIQUE NOT NULL,
                    revoked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP DEFAULT NULL,
                    FOREIGN KEY (user_id) REFERENCES AuthUsers (id)
                )
                """
            )
            conn.commit()

    def ensure_bootstrap_users(self) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Default admin/admin for migration compatibility.
            cursor.execute("SELECT id FROM AuthUsers WHERE username = ?", ("admin",))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO AuthUsers (username, password_hash, role, is_active, is_service_account)
                    VALUES (?, ?, ?, 1, 0)
                    """,
                    ("admin", hash_password("admin"), ROLE_KB_ADMIN),
                )

            # Service account for background tasks.
            cursor.execute("SELECT id FROM AuthUsers WHERE username = ?", ("system",))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO AuthUsers (username, password_hash, role, is_active, is_service_account)
                    VALUES (?, ?, ?, 1, 1)
                    """,
                    ("system", hash_password(os.getenv("SYSTEM_PASSWORD", "system")), ROLE_SYSTEM),
                )
            conn.commit()

    def register_user(self, username: str, password: str, role: str) -> Dict[str, Any]:
        if role not in {ROLE_DESIGNER, ROLE_KB_ADMIN, ROLE_VALIDATION_SPECIALIST, ROLE_SYSTEM}:
            raise HTTPException(status_code=400, detail="Invalid role")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM AuthUsers WHERE username = ?", (username,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="User already exists")

            cursor.execute(
                """
                INSERT INTO AuthUsers (username, password_hash, role, is_active, is_service_account)
                VALUES (?, ?, ?, 1, 0)
                """,
                (username, hash_password(password), role),
            )
            conn.commit()

        return {"username": username, "role": role}

    def _get_user_record(self, username: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, role, is_active, is_service_account
                FROM AuthUsers
                WHERE username = ?
                """,
                (username,),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "role": row[3],
            "is_active": bool(row[4]),
            "is_service_account": bool(row[5]),
        }

    def login(self, username: str, password: str) -> TokenPair:
        user = self._get_user_record(username)
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_payload = create_token_payload(user["username"], user["role"], "access", self.access_ttl)
        refresh_payload = create_token_payload(user["username"], user["role"], "refresh", self.refresh_ttl)
        access_token = encode_jwt(access_payload, self.jwt_secret)
        refresh_token = encode_jwt(refresh_payload, self.jwt_secret)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO AuthRefreshTokens (user_id, token_hash, expires_at, revoked)
                VALUES (?, ?, ?, 0)
                """,
                (
                    user["id"],
                    hash_token(refresh_token),
                    datetime.utcfromtimestamp(refresh_payload["exp"]).isoformat(),
                ),
            )
            cursor.execute(
                "UPDATE AuthUsers SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],),
            )
            conn.commit()

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def refresh(self, refresh_token: str) -> TokenPair:
        payload = self.decode_token(refresh_token, expected_type="refresh")
        token_hash = hash_token(refresh_token)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, user_id, revoked FROM AuthRefreshTokens WHERE token_hash = ?",
                (token_hash,),
            )
            row = cursor.fetchone()
            if not row or row[2]:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            cursor.execute(
                "SELECT username, role FROM AuthUsers WHERE id = ? AND is_active = 1",
                (row[1],),
            )
            user_row = cursor.fetchone()
            if not user_row:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            cursor.execute("UPDATE AuthRefreshTokens SET revoked = 1 WHERE id = ?", (row[0],))
            conn.commit()

        return self._mint_for_user(user_row[0], user_row[1])

    def _mint_for_user(self, username: str, role: str) -> TokenPair:
        user = self._get_user_record(username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        access_payload = create_token_payload(username, role, "access", self.access_ttl)
        refresh_payload = create_token_payload(username, role, "refresh", self.refresh_ttl)
        access_token = encode_jwt(access_payload, self.jwt_secret)
        refresh_token = encode_jwt(refresh_payload, self.jwt_secret)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO AuthRefreshTokens (user_id, token_hash, expires_at, revoked)
                VALUES (?, ?, ?, 0)
                """,
                (
                    user["id"],
                    hash_token(refresh_token),
                    datetime.utcfromtimestamp(refresh_payload["exp"]).isoformat(),
                ),
            )
            conn.commit()

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def logout(self, refresh_token: str) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE AuthRefreshTokens SET revoked = 1 WHERE token_hash = ?",
                (hash_token(refresh_token),),
            )
            conn.commit()

    def decode_token(self, token: str, expected_type: str = "access") -> Dict[str, Any]:
        try:
            payload = decode_jwt(token, self.jwt_secret)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload

    def authenticate(self, authorization: Optional[str], api_key: Optional[str]) -> Principal:
        if self.auth_mode == "disabled":
            return Principal(username="anonymous", role=ROLE_SYSTEM, auth_type="disabled")

        if api_key:
            principal = self._authenticate_api_key(api_key)
            if principal:
                return principal

        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Missing authentication token")

        token = authorization.split(" ", 1)[1]
        payload = self.decode_token(token, expected_type="access")
        return Principal(username=payload["sub"], role=payload["role"], auth_type="jwt")

    def _authenticate_api_key(self, api_key: str) -> Optional[Principal]:
        key_hash = hash_api_key(api_key)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.username, u.role, k.id
                FROM AuthApiKeys k
                JOIN AuthUsers u ON u.id = k.user_id
                WHERE k.key_hash = ? AND k.revoked = 0 AND u.is_active = 1
                """,
                (key_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute(
                "UPDATE AuthApiKeys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
                (row[2],),
            )
            conn.commit()
        return Principal(username=row[0], role=row[1], auth_type="api_key")

    def generate_api_key(self, username: str, name: str) -> Dict[str, Any]:
        user = self._get_user_record(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        plain_key = generate_api_key()
        key_hash = hash_api_key(plain_key)
        prefix = plain_key[:12]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO AuthApiKeys (user_id, name, key_prefix, key_hash, revoked)
                VALUES (?, ?, ?, ?, 0)
                """,
                (user["id"], name, prefix, key_hash),
            )
            key_id = cursor.lastrowid
            conn.commit()

        return {
            "id": key_id,
            "name": name,
            "key_prefix": prefix,
            "api_key": plain_key,
            "username": username,
        }

    def list_api_keys(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if username:
                cursor.execute(
                    """
                    SELECT k.id, u.username, k.name, k.key_prefix, k.created_at, k.last_used_at, k.revoked
                    FROM AuthApiKeys k
                    JOIN AuthUsers u ON u.id = k.user_id
                    WHERE u.username = ?
                    ORDER BY k.id DESC
                    """,
                    (username,),
                )
            else:
                cursor.execute(
                    """
                    SELECT k.id, u.username, k.name, k.key_prefix, k.created_at, k.last_used_at, k.revoked
                    FROM AuthApiKeys k
                    JOIN AuthUsers u ON u.id = k.user_id
                    ORDER BY k.id DESC
                    """
                )
            rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "username": row[1],
                "name": row[2],
                "key_prefix": row[3],
                "created_at": row[4],
                "last_used_at": row[5],
                "revoked": bool(row[6]),
            }
            for row in rows
        ]

    def revoke_api_key(self, key_id: int) -> None:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE AuthApiKeys SET revoked = 1 WHERE id = ?", (key_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="API key not found")
            conn.commit()

    def enforce_user_rate_limit(self, principal: Principal) -> None:
        if self.auth_mode == "disabled":
            return
        allowed, retry = self.rate_limiter.check(
            key=f"user:{principal.username}",
            limit=self.user_rate_limit,
            window_seconds=60,
        )
        if not allowed:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry after {retry}s")

    def enforce_synthesis_rate_limit(self, principal: Principal) -> None:
        if self.auth_mode == "disabled":
            return
        allowed, retry = self.rate_limiter.check(
            key=f"synth:{principal.username}",
            limit=self.synthesis_rate_limit,
            window_seconds=3600,
        )
        if not allowed:
            raise HTTPException(status_code=429, detail=f"Synthesis limit exceeded. Retry after {retry}s")
