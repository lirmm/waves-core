from __future__ import unicode_literals

from django.forms import ModelForm, ChoiceField, PasswordInput
from django.core.exceptions import ValidationError
from django.db.models import Q

from waves.wcore.adaptors.adaptor import JobAdaptor
from waves.wcore.models import AdaptorInitParam, get_submission_model, get_service_model

Service = get_service_model()
Submission = get_submission_model()


class AdaptorInitParamForm(ModelForm):
    """
    Runner defaults param form
    """

    class Meta:
        """ Metas """
        model = AdaptorInitParam
        fields = ['name', "value", 'prevent_override']

    def __init__(self, **kwargs):
        super(AdaptorInitParamForm, self).__init__(**kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            try:
                from django.utils.module_loading import import_string
                from ast import literal_eval
                concrete = instance.content_object.adaptor
                if concrete is not None:
                    assert isinstance(concrete, JobAdaptor)
                    default_value = None
                    initial = instance.value if instance.value else default_value
                    choices = getattr(concrete, instance.name + '_choices', None)
                    if choices:
                        self.fields['value'] = ChoiceField(choices=choices, initial=initial)
                    if not concrete.init_value_editable(instance.name):
                        self.fields['value'].widget.attrs['readonly'] = True
                        if 'prevent_override' in self.fields:
                            self.fields['prevent_override'].widget.attrs['checked'] = True
                            self.fields['prevent_override'].widget.attrs['readonly'] = True
                if instance.name == "password":
                    self.fields['value'].widget = PasswordInput(render_value="",
                                                                attrs={'autocomplete': 'new-password'})
            except ValueError:
                pass

    def clean(self):
        if not self.cleaned_data['value']:
            if isinstance(self.instance.content_object, Submission):
                raise ValidationError({'value': 'Value is mandatory'})
            elif self.cleaned_data['prevent_override'] is True:
                raise ValidationError({'value': 'Value is mandatory when override is prevented'})
            elif isinstance(self.instance.content_object, Service) \
                    and Submission.objects.filter(runner__isnull=True,
                                                  service=self.instance.content_object).count() > 0:
                raise ValidationError({'value': 'Value is mandatory for forms with no overrides'})

        return super(AdaptorInitParamForm, self).clean()
