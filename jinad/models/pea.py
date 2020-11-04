from typing import Dict, Union, Optional, Any
from .custom import build_pydantic_model

PeaModel = build_pydantic_model(model_name='PeaModel',
                                module='pea')
