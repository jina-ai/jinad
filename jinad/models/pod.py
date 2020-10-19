from typing import Optional
from pydantic import BaseModel, Field, validator

PRE_DEFINED_USES = ['_clear', '_pass', '_route', '_merge', '_logforward']

    
class PodBase(BaseModel):
    name: str = Field(..., 
                      title='Name of the pod',
                      example='pod1')
    uses: str = Field('_pass', 
                      title=f'Allows yml file path or one among {PRE_DEFINED_USES}',
                      example='_pass')
    read_only: bool = False
    
    @validator('uses')
    def pre_defined_uses(cls, value):
        # TODO: Check for yaml file
        if value.startswith('_') and value in PRE_DEFINED_USES:
            return value
        raise ValueError(f'Invalid value `{value}` passed for `uses`. '
                         f'Allowed values are {PRE_DEFINED_USES}')

PodBaseExample = [
        {
            "name": "pod1",
            "uses": "_pass",
            "read_only": False
        },
        {
            "name": "pod2",
            "uses": "_pass",
            "read_only": False
        }
]

class PodContainer(PodBase):
    image: str = Field('jinaai:jina',
                       title='Container image to be fetched from docker registry',
                       example='jinaai:jina')
    @validator('image')
    def validate_with_registry(cls, value):
        # TODO: Implement
        return value
    

class PodRemote(PodBase):
    host: str = Field('0.0.0.0',
                      title='Host IP of the remote pod',
                      example='0.0.0.0')
    port_expose: int = Field(52000,
                             title='Host IP of the remote pod',
                             example=52000)
