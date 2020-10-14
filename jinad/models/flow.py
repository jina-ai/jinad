from typing import Optional
from pydantic import BaseModel, Field, validator


class FlowBase(BaseModel):
    uses: Optional[str] = Field(None,
                                title='YAML file describing the Flow')
    log_server: bool = Field(True,
                             title='True if logserver needs to be enabled',
                             example=True)
    @validator('uses')
    def check_yml(cls, value):
        # TODO Implement yml check
        return value
