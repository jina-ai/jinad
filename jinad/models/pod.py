from .custom import build_pydantic_model

PodModel = build_pydantic_model(model_name='PodModel', 
                                module='pod')
