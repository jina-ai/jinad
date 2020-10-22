import requests
from pydantic import create_model, validator, Field

JINA_API_URL = 'https://api.jina.ai/latest'


def get_latest_api():
    """Fetches the latest jina cli args"""
    response = requests.get('https://api.jina.ai/latest')
    all_cli_args = response.json()
    return all_cli_args


def get_module_args(all_args: list, module: str):
    """Fetches the cli args for modules like `flow`, `pod`"""
    for current_module in all_args['methods']:
        if current_module['name'] == module:
            module_args = current_module
            return module_args

    
def generate_validator(field: str, choices: list):
    """ Pydantic validator classmethod generator to validate fields exist in choices """
    def validate_arg_choices(v, values):
        if v not in choices:
            raise ValueError(f'Invalid value {v} for field {field}'
                             f'Valid choices are {choices}')
        return v

    validate_arg_choices.__qualname__ = 'validate_' + field
    return validator(field)(validate_arg_choices)


def get_pydantic_fields(module_args: dict):
    """ Creates Pydantic fields from cli args """
    all_options = {}
    choices_validators = {}
    
    for arg in module_args['options']:
        arg_key = arg['name']
        arg_type = arg['type']
        
        if arg_type == 'method':
            choices_validators[f'validator_for_{arg_key}'] = generate_validator(field=arg_key, 
                                                                                choices=arg['choices'])
            if arg['default'] is None:
                arg_type = int
            else:
                arg_type = type(arg['default'])

        if arg_type == 'FileType':
            arg_type = 'str'
        
        current_field = Field(default=arg['default'],
                              description=arg['help'])
        all_options[arg_key] = (arg_type, current_field)

    return all_options, choices_validators


class PydanticConfig:
    arbitrary_types_allowed = True
    schema_extra = {
        "example": {
            "name": "pod1",
            "uses": "_pass"
        }
    }


def build_pydantic_model(model_name: str = 'CustomModel', module: str = 'pod'):
    """ Dynamic Pydantic model creator from jina cli args """
    all_cli_args = get_latest_api()
    module_args = get_module_args(all_args=all_cli_args,
                                  module=module)
    all_fields, field_validators = get_pydantic_fields(module_args=module_args)
    
    custom_model = create_model(model_name, 
                                **all_fields, 
                                __config__=PydanticConfig, 
                                __validators__=field_validators)
    return custom_model
