from django.core import serializers
from django_hbase.models import HBaseModel
from utils.json_encoder import JSONEncoder

import json


class DjangoModelSerializer:

    @classmethod
    def serialize(cls, instance):
        # Django 的 serializers 默认需要一个 QuerySet 或者 list 类型的数据来进行序列化
        # 因此需要给 instance 加一个 [] 变成 list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        # 需要加 .object 来得到原始的 model 类型的 object 数据，要不然得到的数据并不是一个
        # ORM 的 object，而是一个 DeserializedObject 的类型
        return list(serializers.deserialize('json', serialized_data))[0].object


class HBaseModelSerializer:

    @classmethod
    def get_model_class(cls, model_class_name):
        for subclass in HBaseModel.__subclasses__():
            if subclass.__name__ == model_class_name:
                return subclass
        raise Exception('HBaseModel {} not found'.format(model_class_name))

    @classmethod
    def serialize(cls, instance):
        json_data = {'model_class_name': instance.__class__.__name__}
        for key in instance.get_field_hash():
            value = getattr(instance, key)
            json_data[key] = value
        return json.dumps(json_data)

    @classmethod
    def deserialize(cls, serialized_data):
        json_data = json.loads(serialized_data)
        model_class = cls.get_model_class(json_data['model_class_name'])
        del json_data['model_class_name']
        return model_class(**json_data)