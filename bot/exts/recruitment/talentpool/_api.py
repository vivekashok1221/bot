from datetime import datetime

from pydantic import BaseModel, Field, parse_obj_as
from pydis_core.site_api import APIClient


class NominationEntry(BaseModel):
    """Pydantic model representing a nomination entry."""

    actor_id: int = Field(alias="actor")
    reason: str
    inserted_at: datetime


class Nomination(BaseModel):
    """Pydantic model representing a nomination."""

    id: int
    active: bool
    user_id: int = Field(alias="user")
    inserted_at: datetime
    end_reason: str
    ended_at: datetime | None = None
    entries: list[NominationEntry]
    reviewed: bool
    thread_id: int | None = None


class NominationAPI:
    """Abstraction of site API interaction for talentpool."""

    def __init__(self, site_api: APIClient):
        self.site_api = site_api

    async def get_nominations(
        self,
        user_id: int | None = None,
        active: bool | None = None,
        ordering: str = "-inserted_at"
    ) -> list[Nomination]:
        """
        Fetch a list of nominations.

        Passing a value of `None` indicates it shouldn't filtered by.
        """
        params = {"ordering": ordering}
        if active is not None:
            params["active"] = str(active)
        if user_id is not None:
            params["user__id"] = str(user_id)

        data = await self.site_api.get("bot/nominations", params=params)
        nominations = parse_obj_as(list[Nomination], data)
        return nominations

    async def get_nomination(self, nomination_id: int) -> Nomination:
        """Fetch a nomination by ID."""
        data = await self.site_api.get(f"bot/nominations/{nomination_id}")
        nomination = Nomination.parse_obj(data)
        return nomination

    async def edit_nomination(
        self,
        nomination_id: int,
        *,
        end_reason: str | None = None,
        active: bool | None = None,
        reviewed: bool | None = None,
        thread_id: int | None = None,
    ) -> Nomination:
        """
        Edit a nomination.

        Passing a value of `None` indicates it shouldn't be updated.
        """
        data = {}
        if end_reason is not None:
            data["end_reason"] = end_reason
        if active is not None:
            data["active"] = active
        if reviewed is not None:
            data["reviewed"] = reviewed
        if thread_id is not None:
            data["thread_id"] = thread_id

        result = await self.site_api.patch(f"bot/nominations/{nomination_id}", json=data)
        return Nomination.parse_obj(result)

    async def edit_nomination_entry(
        self,
        nomination_id: int,
        *,
        actor_id: int,
        reason: str,
    ) -> Nomination:
        """Edit a nomination entry."""
        data = {"actor": actor_id, "reason": reason}
        result = await self.site_api.patch(f"bot/nominations/{nomination_id}", json=data)
        return Nomination.parse_obj(result)

    async def post_nomination(
        self,
        user_id: int,
        actor_id: int,
        reason: str,
    ) -> Nomination:
        """Post a nomination to site."""
        data = {
            "actor": actor_id,
            "reason": reason,
            "user": user_id,
        }
        result = await self.site_api.post("bot/nominations", json=data)
        return Nomination.parse_obj(result)

    async def get_activity(
        self,
        user_ids: list[int],
        *,
        days: int,
    ) -> dict[int, int]:
        """
        Get the number of messages sent in the past `days` days by users with the given IDs.

        Returns a dictionary mapping user ID to message count.
        """
        if not user_ids:
            return {}

        result = await self.site_api.post(
            "bot/users/metricity_activity_data",
            json=user_ids,
            params={"days": str(days)}
        )
        return {int(user_id): message_count for user_id, message_count in result.items()}
