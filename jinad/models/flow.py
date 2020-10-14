from typing import Optional
from pydantic import BaseModel


class FlowBase(BaseModel):
    log_server: bool = True
