from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from wallstr.auth.dependencies import Auth
from wallstr.auth.schemas import HTTPUnauthorizedError
from wallstr.auth.services import UserService

from .tasks_backoffice import reprocess_documents as task_reprocess_documents

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={401: {"model": HTTPUnauthorizedError}},
)


@router.post("/reprocess", responses={403: {"description": "Forbidden"}})
async def reprocess_documents(
    auth: Auth,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> None:
    """
    Current api triggers reparsing documents
    It either sync with the latest inference_model and version or all existing documents in the database
    """
    # TODO: needs to move is_admin check to the dependency
    # as an example lazy load auth.is_admin with db query
    user = await user_svc.get_user(auth.user_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
            headers={"WWW-Authenticate": "Bearer"},
        )

    task_reprocess_documents.send()
