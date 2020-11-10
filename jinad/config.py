from pydantic import BaseSettings, validator


class BaseConfig(BaseSettings):
    class Config:
        env_prefix = 'JINAD_'


class FastAPIConfig(BaseConfig):
    NAME: str = 'Jina Remote Manager'
    DESCRIPTION: str = 'REST API for managing Jina on Remote'
    VERSION: str = '0.1.0'
    PREFIX: str = '/v1'


class OpenAPITags(BaseConfig):
    API_TAGS: list = [{
        "name": "Jina Remote Management",
        "description": "API to invoke remote Flows/Pods/Peas",
        "externalDocs": {
            "description": "Jina Remote Context Manager",
            "url": "https://docs.jina.ai/",
        },
    }],
    FLOW_API_TAGS: list = [{
        "name": "Remote Flow Manager",
        "description": "API to invoke local/remote Flows",
        "externalDocs": {
            "description": "Jina Flow Context Manager",
            "url": "https://docs.jina.ai/chapters/flow/index.html",
        },
    }]
    POD_API_TAGS: list = [{
        "name": "Remote Pod Manager",
        "description": "API to invoke remote Pods (__should be used by Flow APIs only__)",
        "externalDocs": {
            "description": "Jina 101",
            "url": "https://docs.jina.ai/chapters/101/.sphinx.html",
        },
    }]
    PEA_API_TAGS: list = [{
        "name": "Remote Pea Manager",
        "description": "API to invoke remote Peas",
        "externalDocs": {
            "description": "Jina 101",
            "url": "https://docs.jina.ai/chapters/101/.sphinx.html",
        },
    }]
    LOG_API_TAGS: list = [{
        "name": "logs",
        "description": "Endpoint to get streaming logs from flows/pods",
    }]


class HypercornConfig(BaseConfig):
    # TODO: check if HOST can be a ipaddress.IPv4Address in hypercorn
    HOST: str = '0.0.0.0'
    PORT: int = 8000


class JinaDConfig(BaseConfig):
    CONTEXT: str = 'all'

    @validator('CONTEXT')
    def validate_name(cls, value):
        if value.lower() not in ['all', 'flow', 'pod', 'pea']:
            raise ValueError('CONTEXT must be either all, flow or pod or pea')
        return value.lower()


jinad_config = JinaDConfig()
fastapi_config = FastAPIConfig()
hypercorn_config = HypercornConfig()
openapitags_config = OpenAPITags()
