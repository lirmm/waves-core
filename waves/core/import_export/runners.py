"""WAVES models export module for Services """
from __future__ import unicode_literals

from django.db import transaction
from rest_framework import serializers

from waves.core.models import Runner, AdaptorInitParam
from waves.core.import_export import RelatedSerializerMixin


class RunnerParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptorInitParam
        fields = ('name', 'value', 'prevent_override')

    def to_representation(self, instance):
        repre = super(RunnerParamSerializer, self).to_representation(instance)
        if instance.name == 'password' or instance.crypt:
            repre['value'] = "xxxxxx"
        return repre


class RunnerSerializer(serializers.ModelSerializer, RelatedSerializerMixin):
    class Meta:
        model = Runner
        fields = ('name', 'clazz', 'runner_params')

    runner_params = RunnerParamSerializer(many=True, source='adaptor_params')

    @transaction.atomic
    def create(self, validated_data):
        runner_params = validated_data.pop('runner_params')
        runner = Runner.objects.create(**validated_data)
        runner.runner_run_params.all().delete()
        runner.runner_run_params = self.create_related(foreign={'runner': runner},
                                                       serializer=RunnerParamSerializer,
                                                       datas=runner_params)
        return runner
