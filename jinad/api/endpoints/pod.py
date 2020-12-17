import uuid
from typing import Dict, List

from fastapi import status, APIRouter, File, UploadFile
from jina.logging import JinaLogger

from jinad.store import pod_store
from jinad.models.pod import PodModel
from jinad.excepts import HTTPException, PodStartException
from jinad.helper import flowpod_to_namespace, basepod_to_namespace, create_meta_files_from_upload

logger = JinaLogger(context='👻 PODAPI')
router = APIRouter()


@router.put(
    path='/upload',
    summary='Upload pod context yamls & pymodules',
)
async def _upload(
    uses_files: List[UploadFile] = File(()),
    pymodules_files: List[UploadFile] = File(())
):
    """

    """
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
    path='/pod/cli',
    summary='Create an independent MutablePod',
)
async def _create_independent(
    pod_arguments: PodModel
):
    """
    This is used to create an independent remote MutablePod which stays out of Flow context
    """
    pod_arguments = basepod_to_namespace(args=pod_arguments)

    with pod_store._session():
        try:
            pod_id = pod_store._create(pod_arguments=pod_arguments)
        except PodStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Pod couldn\'t get started:  {repr(e)}')
        except Exception as e:
            logger.error(f'Got an error while creating a pod {repr(e)}')
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'pod_id': pod_id,
        'status': 'started'
    }


@router.put(
    path='/pod/flow',
    summary='Create a MutablePod via Flow',
)
async def _create_via_flow(
    pod_arguments: Dict
):
    """
    This is used to create a remote MutablePod which gets triggered by a Flow context

    > Shouldn't be created with manual trigger

    Args: pod_arguments (Dict)

        {
            'head': PodModel,
            'tail': PodModel,
            'peas': [PodModel]
        }


    """
    pod_arguments = flowpod_to_namespace(args=pod_arguments)

    with pod_store._session():
        try:
            pod_id = pod_store._create(pod_arguments=pod_arguments)
        except PodStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Pod couldn\'t get started:  {repr(e)}')
        except Exception as e:
            logger.error(f'Got an error while creating a pod {repr(e)}')
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'pod_id': pod_id,
        'status': 'started'
    }


@router.delete(
    path='/pod',
    summary='Delete pod',
)
async def _delete(
    pod_id: uuid.UUID
):
    """Close Pod context
    """
    with pod_store._session():
        try:
            pod_store._delete(pod_id=pod_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pod ID {pod_id} not found! Please create a new Pod')


@router.on_event('shutdown')
def _shutdown():
    with pod_store._session():
        pod_store._delete_all()
