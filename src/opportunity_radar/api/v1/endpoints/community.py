"""Community and sharing API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId

from ....models.user import User
from ....models.shared_list import SharedList
from ....models.opportunity import Opportunity
from ....schemas.shared_list import (
    SharedListCreate,
    SharedListUpdate,
    SharedListResponse,
    SharedListDetailResponse,
    SharedListListResponse,
    CommentCreate,
    CommentResponse,
    OpportunityBrief,
    ShareLinkResponse,
)
from ....services.sharing_service import get_sharing_service
from ....core.security import get_current_user

router = APIRouter()


def _list_to_response(
    shared_list: SharedList,
    current_user_id: Optional[PydanticObjectId] = None,
) -> SharedListResponse:
    """Convert shared list to response schema."""
    is_liked = current_user_id in shared_list.liked_by if current_user_id else False

    return SharedListResponse(
        id=str(shared_list.id),
        owner_id=str(shared_list.owner_id),
        owner_name=shared_list.owner_name,
        title=shared_list.title,
        slug=shared_list.slug,
        description=shared_list.description,
        cover_image_url=shared_list.cover_image_url,
        visibility=shared_list.visibility,
        opportunity_count=len(shared_list.opportunity_ids),
        tags=shared_list.tags,
        view_count=shared_list.view_count,
        like_count=shared_list.like_count,
        is_liked=is_liked,
        comment_count=len(shared_list.comments),
        is_featured=shared_list.is_featured,
        created_at=shared_list.created_at,
        updated_at=shared_list.updated_at,
    )


async def _list_to_detail_response(
    shared_list: SharedList,
    current_user_id: Optional[PydanticObjectId] = None,
) -> SharedListDetailResponse:
    """Convert shared list to detailed response with opportunities."""
    base = _list_to_response(shared_list, current_user_id)

    # Get opportunities
    opportunities = []
    for opp_id in shared_list.opportunity_ids:
        opp = await Opportunity.get(opp_id)
        if opp:
            opportunities.append(
                OpportunityBrief(
                    id=str(opp.id),
                    title=opp.title,
                    opportunity_type=opp.opportunity_type,
                    website_url=opp.website_url,
                    application_deadline=opp.application_deadline,
                    total_prize_value=opp.total_prize_value,
                )
            )

    # Get comments
    comments = [
        CommentResponse(
            user_id=str(c.user_id),
            user_name=c.user_name,
            content=c.content,
            created_at=c.created_at,
        )
        for c in shared_list.comments[-20:]  # Last 20 comments
    ]

    return SharedListDetailResponse(
        **base.model_dump(),
        opportunities=opportunities,
        comments=comments,
    )


# Public endpoints

@router.get("/lists", response_model=SharedListListResponse)
async def list_public_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    sort_by: str = Query("created_at", description="Sort by: created_at or popular"),
):
    """
    List all public shared lists.

    Anyone can view public lists without authentication.
    """
    service = get_sharing_service()

    lists, total = await service.get_public_lists(
        skip=skip,
        limit=limit,
        tags=tags,
        sort_by=sort_by,
    )

    return SharedListListResponse(
        items=[_list_to_response(lst) for lst in lists],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/lists/featured", response_model=List[SharedListResponse])
async def get_featured_lists(
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get featured public lists.
    """
    service = get_sharing_service()
    lists = await service.get_featured_lists(limit=limit)
    return [_list_to_response(lst) for lst in lists]


@router.get("/lists/{slug}", response_model=SharedListDetailResponse)
async def get_public_list(
    slug: str,
):
    """
    Get a public or unlisted list by slug.

    Records a view for public lists.
    """
    service = get_sharing_service()

    shared_list = await service.get_list_by_slug(slug)
    if not shared_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if shared_list.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    # Record view for public lists
    if shared_list.visibility == "public":
        await service.record_view(shared_list)

    return await _list_to_detail_response(shared_list)


# Authenticated endpoints

@router.post("/lists", response_model=SharedListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    data: SharedListCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new shared list.
    """
    service = get_sharing_service()

    shared_list = await service.create_list(
        user=current_user,
        title=data.title,
        description=data.description,
        visibility=data.visibility,
        tags=data.tags,
        opportunity_ids=data.opportunity_ids,
        cover_image_url=data.cover_image_url,
    )

    return _list_to_response(shared_list, current_user.id)


@router.get("/my-lists", response_model=SharedListListResponse)
async def list_my_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    List all lists owned by the current user.
    """
    service = get_sharing_service()

    lists, total = await service.get_user_lists(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    return SharedListListResponse(
        items=[_list_to_response(lst, current_user.id) for lst in lists],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/my-lists/{list_id}", response_model=SharedListDetailResponse)
async def get_my_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific list owned by the current user.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if shared_list.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this list",
        )

    return await _list_to_detail_response(shared_list, current_user.id)


@router.patch("/my-lists/{list_id}", response_model=SharedListResponse)
async def update_my_list(
    list_id: str,
    data: SharedListUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update a list owned by the current user.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if shared_list.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this list",
        )

    shared_list = await service.update_list(
        shared_list=shared_list,
        data=data.model_dump(exclude_unset=True),
    )

    return _list_to_response(shared_list, current_user.id)


@router.delete("/my-lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a list owned by the current user.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if shared_list.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this list",
        )

    await service.delete_list(shared_list)


@router.post("/my-lists/{list_id}/opportunities/{opportunity_id}")
async def add_opportunity_to_list(
    list_id: str,
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Add an opportunity to a list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    try:
        opp_id = PydanticObjectId(opportunity_id)
        opp = await Opportunity.get(opp_id)
        if not opp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid opportunity ID",
        )

    await service.add_opportunity_to_list(shared_list, opp_id)

    return {"message": "Opportunity added to list"}


@router.delete("/my-lists/{list_id}/opportunities/{opportunity_id}")
async def remove_opportunity_from_list(
    list_id: str,
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Remove an opportunity from a list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    try:
        opp_id = PydanticObjectId(opportunity_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid opportunity ID",
        )

    await service.remove_opportunity_from_list(shared_list, opp_id)

    return {"message": "Opportunity removed from list"}


@router.post("/lists/{list_id}/like")
async def toggle_like(
    list_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Toggle like on a public list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    is_liked = await service.toggle_like(shared_list, current_user.id)

    return {"is_liked": is_liked, "like_count": shared_list.like_count}


@router.post("/lists/{list_id}/comments", response_model=CommentResponse)
async def add_comment(
    list_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Add a comment to a public list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    shared_list = await service.add_comment(shared_list, current_user, data.content)

    # Return the newly added comment
    new_comment = shared_list.comments[-1]
    return CommentResponse(
        user_id=str(new_comment.user_id),
        user_name=new_comment.user_name,
        content=new_comment.content,
        created_at=new_comment.created_at,
    )


@router.get("/lists/{list_id}/share", response_model=ShareLinkResponse)
async def get_share_links(
    list_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get share links for a list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if shared_list.owner_id != current_user.id and shared_list.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    return ShareLinkResponse(
        url=service.generate_share_url(shared_list),
        embed_code=service.generate_embed_code(shared_list) if shared_list.visibility != "private" else None,
    )


@router.post("/lists/{list_id}/generate-description")
async def generate_description(
    list_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Use AI to generate a description for a list.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    description = await service.generate_list_description(shared_list)

    return {"description": description}


@router.get("/lists/{list_id}/similar", response_model=List[SharedListResponse])
async def get_similar_lists(
    list_id: str,
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get similar public lists.
    """
    service = get_sharing_service()

    try:
        shared_list = await service.get_list(PydanticObjectId(list_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    if not shared_list or shared_list.visibility == "private":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found",
        )

    similar = await service.get_similar_lists(shared_list, limit=limit)

    return [_list_to_response(lst) for lst in similar]
