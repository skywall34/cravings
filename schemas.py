"""Pydantic request + response models — the explicit wire interface.

Request bodies were previously `body: dict` with hand-rolled key checks spread
across routes; these models concentrate that contract in one place. Domain
validation lives in field_validators (raising ValueError → 422, flattened to a
string `detail` by the handler in main.py so shipped clients keep parsing it).

Response models are the single source of each wire shape — `is_registered` is
computed once and FastAPI filters output to the declared fields.
"""

import os
from typing import Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, field_validator

from tagging import safety


def _admin_emails() -> frozenset[str]:
    raw = os.environ.get("CRAVINGS_ADMIN_EMAILS", "")
    return frozenset(e.strip().lower() for e in raw.split(",") if e.strip())


def is_admin_email(email: str | None) -> bool:
    return bool(email and email.lower() in _admin_emails())


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class PatchMeBody(BaseModel):
    # None = field omitted → keep existing; [] = explicitly clear.
    dietary_restrictions: list[str] | None = None
    safety_overrides: list[str] | None = None

    @field_validator("dietary_restrictions")
    @classmethod
    def _check_dietary(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            unknown = set(v) - set(safety.DIETARY_FLAGS)
            if unknown:
                raise ValueError(f"unknown dietary flags: {sorted(unknown)}")
        return v

    @field_validator("safety_overrides")
    @classmethod
    def _check_safety(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            unknown = set(v) - set(safety.SAFETY_FLAGS)
            if unknown:
                raise ValueError(f"unknown safety flags: {sorted(unknown)}")
        return v


class OnboardingBody(BaseModel):
    preferences: dict[str, float]
    reset: bool = False

    @field_validator("preferences")
    @classmethod
    def _non_empty(cls, v: dict[str, float]) -> dict[str, float]:
        if not v:
            raise ValueError("preferences required")
        return v


class SwipeBody(BaseModel):
    food_item_id: int
    direction: Literal["left", "right", "never"]
    session_id: str = ""
    snapshot_token: str = ""
    taste_prefs: dict[str, float] = {}


class SessionResetBody(BaseModel):
    session_id: str = ""


class RegisterBody(BaseModel):
    email: str
    password: str
    name: str

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        try:
            return validate_email(v.strip(), check_deliverability=False).normalized
        except EmailNotValidError as e:
            raise ValueError(f"invalid email: {e}") from e

    @field_validator("password")
    @classmethod
    def _password_len(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("password must be at least 8 characters")
        return v.strip()

    @field_validator("name")
    @classmethod
    def _name_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name required")
        return v.strip()


class LoginBody(BaseModel):
    email: str
    password: str = ""

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        try:
            return validate_email(v.strip(), check_deliverability=False).normalized
        except EmailNotValidError as e:
            raise ValueError(f"invalid email: {e}") from e


class VerifyEmailBody(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        try:
            return validate_email(v.strip(), check_deliverability=False).normalized
        except EmailNotValidError as e:
            raise ValueError(f"invalid email: {e}") from e

    @field_validator("code")
    @classmethod
    def _norm_code(cls, v: str) -> str:
        return v.strip()


class ResendVerificationBody(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _norm_email(cls, v: str) -> str:
        try:
            return validate_email(v.strip(), check_deliverability=False).normalized
        except EmailNotValidError as e:
            raise ValueError(f"invalid email: {e}") from e


class PasswordBody(BaseModel):
    # Length/ordering checks stay in the handler so "wrong old password" still
    # wins (401) over "new password too short" (400), preserving the contract.
    old_password: str = ""
    new_password: str = ""


# ---------------------------------------------------------------------------
# Response bodies (single source of each wire shape)
# ---------------------------------------------------------------------------

class UserInfoOut(BaseModel):
    id: int
    name: str
    email: str | None
    is_registered: bool
    dietary_restrictions: list[str]
    safety_overrides: list[str]
    onboarding_complete: bool
    is_premium: bool
    is_admin: bool
    email_verified: bool

    @classmethod
    def of(cls, row, dietary_mask: int | None = None, safety_mask: int | None = None) -> "UserInfoOut":
        diet = row["dietary_flags_bitmask"] if dietary_mask is None else dietary_mask
        saf = row["safety_overrides_bitmask"] if safety_mask is None else safety_mask
        return cls(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            is_registered=row["email"] is not None,
            dietary_restrictions=safety.dietary_list_from_bitmask(diet),
            safety_overrides=safety.safety_list_from_bitmask(saf),
            onboarding_complete=bool(row["onboarding_complete"]),
            is_premium=bool(row.get("is_premium", 0)),
            is_admin=is_admin_email(row["email"]),
            email_verified=bool(row.get("email_verified", 0)),
        )


class AuthResultOut(BaseModel):
    id: int
    name: str
    email: str | None
    api_token: str
    is_registered: bool
    onboarding_complete: bool
    is_premium: bool
    is_admin: bool
    email_verified: bool = False
