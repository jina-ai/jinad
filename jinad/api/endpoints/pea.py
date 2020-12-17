import uuid
from typing import List

from fastapi import status, APIRouter, File, UploadFile
from jina.logging import JinaLogger

from jinad.store import pea_store
from jinad.models.pea import PeaModel
from jinad.excepts import HTTPException, PeaStartException
from jinad.helper import basepea_to_namespace, create_meta_files_from_upload

logger = JinaLogger(context='👻 PEAAPI')
router = APIRouter()


@router.put(
    path='/pea/upload',
    summary='Upload pod context yamls & pymodules',
)
async def _upload(
    uses_files: List[UploadFile] = File(()),
    pymodules_files: List[UploadFile] = File(())
):
    """
    """
    # TODO: This is repetitive code. needs refactoring
    upload_status = 'nothing to upload'
    if uses_files:
        [create_meta_files_from_upload(current_file) for current_file in uses_files]
        upload_status = 'uploaded'

    if pymodules_files:
        [create_meta_files_from_upload(current_file) for current_file in pymodules_files]
        upload_status = 'uploaded'

    return {
        'status_code': status.HTTP_200_OK,
        'status': upload_status
    }


@router.put(
    path='/pea',
    summary='Create a Pea',
)
async def _create(
    pea_arguments: PeaModel
):
    """
    Used to create a Pea on remote
    """
    pea_arguments = basepea_to_namespace(args=pea_arguments)

    with pea_store._session():
        try:
            pea_id = pea_store._create(pea_arguments=pea_arguments)
        except PeaStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Pea couldn\'t get started:  {repr(e)}')
        except Exception as e:
            logger.error(f'Got an error while creating a pea {repr(e)}')
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'pea_id': pea_id,
        'status': 'started'
    }


@router.delete(
    path='/pea',
    summary='Close Pea context',
)
async def _delete(
    pea_id: uuid.UUID
):
    """Close Pea context
    """
    with pea_store._session():
        try:
            pea_store._delete(pea_id=pea_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pea ID {pea_id} not found! Please create a new Pea')


@router.on_event('shutdown')
def _shutdown():
    with pea_store._session():
        pea_store._delete_all()
