class FlowYamlParseException(Exception):
    """ Exception during loading yaml file for Flow creation"""


class FlowCreationException(Exception):
    """ Exception during flow creation via pods"""


class FlowStartException(Exception):
    """ Exception during flow start"""


class PodStartException(Exception):
    """ Exception during pod start """


class PeaStartException(Exception):
    """ Exception during pod start """
