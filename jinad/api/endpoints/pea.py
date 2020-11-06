import time
import uuid
from typing import List

from config import openapitags_config, hypercorn_config
from excepts import HTTPException, PeaStartException
from fastapi import status, APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from helper import basepea_to_namespace, create_meta_files_from_upload
from jina.logging import JinaLogger
from models.pea import PeaModel
from store import pea_store

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


def streamer(generator):
    try:
        for i in generator:
            yield i
            time.sleep(.001)

    except GeneratorExit:
        logger.info("Exiting from Pod log_iterator")


@router.get(
    path='/log',
    summary='Stream log using log_iterator',
    tags=[TAG]
)
def _log(
    pea_id: uuid.UUID
):
    """
    Stream logs from remote pea using log_iterator (This will be changed!)
    """
    with pea_store._session():
        try:
            current_pea = pea_store._store[pea_id]['pea']
            return StreamingResponse(streamer(current_pea.log_iterator))
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pea ID {pea_id} not found! Please create a new Pea')


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
