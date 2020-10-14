from typing import Optional
from pydantic import BaseModel, validator, Field

PRE_DEFINED_USES = ['_clear', '_pass', '_route', '_merge', '_logforward']

    
class PodBase(BaseModel):
    name: str
    uses: str = Field('_pass', 
                      title=f'Allows yml file path or one among {PRE_DEFINED_USES}')
    read_only: bool = False
    
    @validator('uses')
    def pre_defined_uses(cls, value):
        if value.startswith('_') and value in PRE_DEFINED_USES:
            return value
        raise ValueError(f'Invalid value `{value}` passed for `uses`. '
                         f'Allowed values are {PRE_DEFINED_USES}')


class PodContainer(PodBase):
    image: str = 'jinaai:jina'
    

class PodRemote(PodBase):
    host: str = '0.0.0.0'
    port_expose: int = 52000
