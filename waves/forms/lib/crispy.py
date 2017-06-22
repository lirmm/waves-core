from __future__ import unicode_literals

from crispy_forms.bootstrap import *
from crispy_forms.helper import FormHelper as BaseFormHelper
from crispy_forms.layout import *

from waves.models.inputs import *
from waves.models.samples import FileInputSample
from . import BaseHelper

__all__ = ['FormHelper', 'FormLayout']


class FormHelper(BaseFormHelper, BaseHelper):
    """
    Extended FormHelper based on crispy FormHelper,
    Dynamic form fields according to inputs types and parameters
    """

    # TODO clean dirty code for tab layout (copy_paste field)

    def __init__(self, form=None, **kwargs):
        form_tag = kwargs.pop('form_tag', True)
        form_class = kwargs.pop('form_class', 'form-horizontal')
        label_class = kwargs.pop('label_class', 'col-lg-4')
        field_class = kwargs.pop('field_class', 'col-lg-8 text-left')
        super(FormHelper, self).__init__(form)
        self.form_tag = form_tag
        self.form_class = form_class
        self.label_class = label_class
        self.field_class = field_class
        self.render_unmentioned_fields = False
        self.layout = Layout()

    def set_layout(self, service_input, form):
        """
        Setup layout for displaying a form for a Service, append extra fields for forms if needed
        """
        css_class = ""
        field_id = "id_" + service_input.name
        dependent_on = ""
        dependent_4_value = ""
        if service_input.dependents_inputs.count() > 0:
            css_class = "has_dependent"
        field_dict = dict(
            css_class=css_class,
            id=field_id,
            title=service_input.help_text,
        )
        if service_input.parent is not None:
            field_id += '_' + service_input.parent.name + '_' + service_input.when_value
            dependent_on = service_input.parent.name
            dependent_4_value = service_input.when_value
            field_dict.update(dict(dependent_on=service_input.parent.name,
                                   dependent_4_value=service_input.when_value))
            when_value = form.data.get(service_input.parent.name, service_input.parent.default)
            if service_input.when_value != when_value:
                field_dict.update(dict(wrapper_class="hid_dep_parameter", disabled="disabled"))
            else:
                field_dict.update(dict(wrapper_class="dis_dep_parameter"))
        input_field = Field(service_input.name, **field_dict)
        if isinstance(service_input, FileInput) and not service_input.multiple:
            cp_input_field = Field('cp_' + service_input.name, css_id='id_' + 'cp_' + service_input.name)
            tab_input = Tab(
                "File Upload",
                input_field,
                css_id='tab_' + service_input.name
            )
            if service_input.input_samples.count() > 0:
                all_sample = []
                for sample in service_input.input_samples.all():
                    all_sample.append(Field('sp_' + service_input.name + '_' + str(sample.pk)))
                tab_input.extend(all_sample)
            self.layout.append(
                Div(
                    TabHolder(
                        tab_input,
                        Tab(
                            "Copy/paste content",
                            cp_input_field,
                            css_class='copypaste',
                            css_id='tab_cp_' + service_input.name,
                        ),
                        css_id='tab_holder_' + service_input.name,
                    ),
                    id='tab_pane_' + service_input.name,
                    css_class='copypaste',
                    dependent_on=dependent_on,
                    dependent_4_value=dependent_4_value
                )
            )
        elif not isinstance(service_input, FileInputSample):
            self.layout.append(
                input_field
            )

    def init_layout(self, fields):
        l_fields = []
        for field in fields:
            l_fields.append(Field(field))
        self.layout = Layout()
        self.layout.extend(l_fields)
        return self.layout

    def end_layout(self):
        self.layout.extend([
            HTML('<HR/>'),
            FormActions(
                Reset('reset', 'Reset form'),
                Submit('save', 'Submit a job')
            )
        ])
