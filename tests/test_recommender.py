"""Direct tests for the Recommender seam — the test surface unlocked by collapsing
the guest/registered branches out of the routes. These exercise GuestRecommender
without the HTTP stack, and lock the reward policy that used to drift between paths."""

from dataclasses import replace

import pytest

import swipe
from recommender import GuestRecommender, RegisteredRecommender, make_recommender
from swipe.recorder import reward_for_direction
from swipe.session import SessionStore
from swipe.snapshot import capture_guest, seal


class _SpyModel:
    """Stands in for a session-scoped Local Model; captures the reward it's trained on."""

    def __init__(self):
        self.rewards: list[float] = []

    def record_swipe(self, item, context, reward):
        self.rewards.append(reward)

    def set_prior_from_onboarding(self, prefs):  # pragma: no cover - not hit when preseeded
        pass


def _guest_token(session_id: str) -> str:
    return seal(capture_guest(session_id, None))


def _guest_token_bound(session_id: str, ids: list[int]) -> str:
    """Token bound to a specific served-item set, like intake.shape_results issues."""
    return seal(replace(capture_guest(session_id, None), item_ids=tuple(ids)))


def _guest(sessions: SessionStore, session_id: str) -> GuestRecommender:
    return GuestRecommender(
        conn=None, sessions=sessions, base_path="", session_max_swipes=10,
        session_id=session_id, dietary_restrictions=[], safety_overrides=[], taste_prefs={},
    )


# ── reward policy (single source of truth) ──────────────────────────────────

def test_reward_for_direction_defaults():
    assert reward_for_direction("right") == 1.0
    assert reward_for_direction("left") == 0.3
    assert reward_for_direction("never") == 0.0


def test_reward_for_direction_rejects_unknown():
    with pytest.raises(swipe.SwipeError):
        reward_for_direction("sideways")


# ── guest record() honors the shared reward policy (regression for the 0.0 drift) ──

@pytest.mark.asyncio
async def test_guest_left_swipe_uses_configurable_reward(monkeypatch):
    monkeypatch.setenv("CRAVINGS_LEFT_SWIPE_REWARD", "0.3")
    sessions = SessionStore()
    model = _SpyModel()
    await sessions.set_model("s1", model)
    rec = _guest(sessions, "s1")

    await rec.record(item={"id": 1}, direction="left", token=_guest_token("s1"))

    # Pre-refactor the guest path hardcoded 0.0 here; now it must match registered.
    assert model.rewards == [0.3]


@pytest.mark.asyncio
async def test_guest_right_swipe_reward_is_one(monkeypatch):
    sessions = SessionStore()
    model = _SpyModel()
    await sessions.set_model("s1", model)
    rec = _guest(sessions, "s1")

    await rec.record(item={"id": 1}, direction="right", token=_guest_token("s1"))

    assert model.rewards == [1.0]


@pytest.mark.asyncio
async def test_guest_never_swipe_honors_never_reward(monkeypatch):
    monkeypatch.setenv("CRAVINGS_NEVER_REWARD", "0.0")
    sessions = SessionStore()
    model = _SpyModel()
    await sessions.set_model("s1", model)
    rec = _guest(sessions, "s1")

    await rec.record(item={"id": 1}, direction="never", token=_guest_token("s1"))

    assert model.rewards == [0.0]


@pytest.mark.asyncio
async def test_guest_invalid_direction_raises(monkeypatch):
    sessions = SessionStore()
    await sessions.set_model("s1", _SpyModel())
    rec = _guest(sessions, "s1")

    with pytest.raises(swipe.SwipeError):
        await rec.record(item={"id": 1}, direction="sideways", token=_guest_token("s1"))


@pytest.mark.asyncio
async def test_guest_record_marks_seen_and_reports_session_complete():
    sessions = SessionStore()
    rec = GuestRecommender(
        conn=None, sessions=sessions, base_path="", session_max_swipes=1,
        session_id="s1", dietary_restrictions=[], safety_overrides=[], taste_prefs={},
    )

    out = await rec.record(item={"id": 7}, direction="right", token=_guest_token("s1"))

    assert out == {"total_swipes": 0, "session_complete": True}
    assert 7 in await sessions.seen("s1")


@pytest.mark.asyncio
async def test_guest_record_rejects_mismatched_session():
    sessions = SessionStore()
    rec = _guest(sessions, "s1")
    with pytest.raises(swipe.SnapshotError):
        await rec.record(item={"id": 1}, direction="right", token=_guest_token("other"))


# ── H1: swipe must target an item the token actually recommended ─────────────

@pytest.mark.asyncio
async def test_guest_record_rejects_unserved_item():
    """A token bound to served ids [7, 8] must reject a swipe on any other id, so
    the model can't be trained on an arbitrary (possibly filtered) item."""
    sessions = SessionStore()
    model = _SpyModel()
    await sessions.set_model("s1", model)
    rec = _guest(sessions, "s1")

    with pytest.raises(swipe.SnapshotError):
        await rec.record(item={"id": 999}, direction="right",
                         token=_guest_token_bound("s1", [7, 8]))
    assert model.rewards == []  # never trained on the unserved item


@pytest.mark.asyncio
async def test_guest_record_accepts_served_item():
    sessions = SessionStore()
    model = _SpyModel()
    await sessions.set_model("s1", model)
    rec = _guest(sessions, "s1")

    await rec.record(item={"id": 7}, direction="right",
                     token=_guest_token_bound("s1", [7, 8]))
    assert model.rewards == [1.0]


# ── factory resolves identity once ──────────────────────────────────────────

def test_make_recommender_resolves_guest_when_no_user():
    rec = make_recommender(
        conn=None, user=None, sessions=SessionStore(), model_service=None,
        base_path="", session_max_swipes=10, session_id="s1",
    )
    assert isinstance(rec, GuestRecommender)


def test_make_recommender_resolves_registered_with_user():
    rec = make_recommender(
        conn=None, user={"id": 1}, sessions=SessionStore(), model_service=None,
        base_path="", session_max_swipes=10, session_id="s1",
    )
    assert isinstance(rec, RegisteredRecommender)
