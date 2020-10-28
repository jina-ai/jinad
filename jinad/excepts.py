from jina.excepts import GRPCServerError, ExecutorFailToLoad, PeaFailToStart
from fastapi import HTTPException

class FlowYamlParseException(Exception):
    """ Exception during loading yaml file for Flow creation"""


class FlowCreationFailed(Exception):
    """ Exception during flow creation via pods"""

class FlowStartFailed(Exception):
    """ Exception during flow start"""
