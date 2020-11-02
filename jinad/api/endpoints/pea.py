import uuid
from typing import Dict, List, Any

from jina.logging import JinaLogger
from fastapi import status, APIRouter, Body, File, UploadFile

from store import pea_store
from models.pea import PeaModel
from helper import pea_dict_to_namespace, create_meta_files_from_upload
from excepts import HTTPException, PeaStartException
from config import openapitags_config, hypercorn_config


TAG = openapitags_config.PEA_API_TAGS[0]['name']
logger = JinaLogger(context='👻 PEAAPI')
router = APIRouter()


@router.on_event('startup')
async def startup():
    logger.info(f'Hypercorn + FastAPI running on {hypercorn_config.HOST}:{hypercorn_config.PORT}')
    logger.info('Welcome to Jina daemon for remote peas')


@router.put(
    path='/upload',
    summary='Upload pod context yamls & pymodules',
    tags=[TAG]
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
    tags=[TAG]
)
async def _create(
    pea_arguments: PeaModel
):
    """
    Used to create a Pea on remote
    """
    pea_arguments = pea_dict_to_namespace(args=pea_arguments)

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
        'pod_id': pea_id,
        'status': 'started'
    }

@router.delete(
    path='/pea',
    summary='Close Pea context',
    tags=[TAG]
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
                                detail=f'Pea ID {pea_id} not found! Please create a new Pod')


@router.on_event('shutdown')
def _shutdown():
    with pea_store._session():
        pea_store._delete_all()
