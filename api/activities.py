from fastapi import APIRouter, Depends, HTTPException, Request

from models.user import TokenMetadata
from services.jwt_service import JwtService
from services.supabase_client import supabase_client
from utils.cookies import get_token_from_cookie


router = APIRouter(prefix="/api", tags=["Activities"])


async def _get_current_user(token: str | None) -> TokenMetadata:
    """
    Resolve the current user metadata from JWT token.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")

    metadata = await JwtService.validate_token(token)
    if not metadata:
        raise HTTPException(status_code=401, detail="Invalid token")

    return metadata


@router.post("/activities/create")
async def create_activity(request: Request, token=Depends(get_token_from_cookie)):
    """
    Create a new activity for the authenticated user.

    Flow:
      1. Ensure the user is authenticated
      2. Check that the provided activity ID exists in app.pre_defined_activities
      3. If it does, insert the activity into the activities table
      4. If it does not, return an error
    """
    metadata = await _get_current_user(token)
    data = await request.json()

    activity = data.get("activity") or {}
    activity_id = activity.get("id")
    if not activity_id:
        raise HTTPException(status_code=400, detail="Missing activity id")

    # Validate predefined activity exists (in app schema)
    activities = await supabase_client.table_select(
        "pre_defined_activities",
        filters={"id": activity_id},
        limit=1,
        schema="app",
        token=token,
    )
    if not activities:
        raise HTTPException(status_code=400, detail="Invalid activity id")

    # Insert into activities_assignments table
    await supabase_client.table_insert(
        "activities_assignments",
        {
            "user_id": metadata.user_id,
            "notes": data.get("notes"),
            "activity_id": activity_id,  # Column is named 'activity_id' in DB
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
        },
        schema="app",
        token=token,
    )

    return {"message": "Activity created successfully"}


@router.get("/activities/history")
async def get_history(token=Depends(get_token_from_cookie)):
    """
    Retrieve all activities for the authenticated user.
    """
    metadata = await _get_current_user(token)
    activities = await supabase_client.table_select(
        "activities_assignments",  # Correct table name
        filters={"user_id": metadata.user_id},
        schema="app",
        token=token,
    )
    if not activities:
        raise HTTPException(status_code=400, detail="No activities found")

    return activities


@router.get("/activities/tags")
async def get_tags(token=Depends(get_token_from_cookie)):
    """
    Protected Endpoint: Only accessible to authenticated users.

    Retrieves all predefined activities as tags.
    """
    metadata = await _get_current_user(token)
    tags = await supabase_client.table_select(
        "pre_defined_activities",
        schema="app",
        token=token,
    )
    if not tags:
        raise HTTPException(status_code=400, detail="No tags found")

    return {"data": tags}
