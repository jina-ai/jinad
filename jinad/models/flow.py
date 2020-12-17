from jinad.models.custom import build_pydantic_model

FlowModel = build_pydantic_model(model_name='FlowModel',
                                 module='flow')
