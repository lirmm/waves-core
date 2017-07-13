from __future__ import unicode_literals

from django.forms import ModelForm, ChoiceField, PasswordInput

from waves.wcore.adaptors.adaptor import JobAdaptor
from waves.wcore.models.adaptors import AdaptorInitParam


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
                        self.fields['prevent_override'].widget.attrs['checked'] = True
                        self.fields['prevent_override'].widget.attrs['readonly'] = True
                if instance.name == "password":
                    self.fields['value'].widget = PasswordInput(render_value="",
                                                                attrs={'autocomplete': 'new-password'})
            except ValueError:
                pass
