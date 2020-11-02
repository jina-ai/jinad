from typing import Dict, Union, Optional, Any
from .custom import build_pydantic_model

PodModel = build_pydantic_model(model_name='PodModel',
                                module='pod')

class RemotePodModel:
    args: Dict = {
        'head': None,
        'tail': None,
        'peas': [PodModel]
    }
