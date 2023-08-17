def convert_model_to_dict(model):
    if isinstance(model, list):
        model_list = []
        for item in model:
            model_data = item.__dict__.copy()
            model_data.pop('_sa_instance_state', None)
            model_list.append(model_data)
        return model_list
    else:
        model_data = model.__dict__.copy()
        model_data.pop('_sa_instance_state', None)
        return model_data
