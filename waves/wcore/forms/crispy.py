from __future__ import unicode_literals

from crispy_forms import bootstrap
from crispy_forms.helper import FormHelper as CrispyFormHelper
from crispy_forms.layout import Layout, Field, Div, HTML, Reset, Submit

from waves.wcore.forms.helper import WFormHelper
from waves.wcore.models.inputs import FileInputSample, FileInput
from waves.wcore.settings import waves_settings

__all__ = ['FormHelper']


class FormHelper(CrispyFormHelper, WFormHelper):
    """
    Extended WFormHelper based on crispy WFormHelper,
    Dynamic form fields according to inputs types and parameters
    """

    # TODO Created dedicated field for (copy_paste field)

    def __init__(self, form=None, **kwargs):
        form_tag = kwargs.pop('form_tag', True)
        form_class = kwargs.pop('form_class', 'form-horizontal')
        label_class = kwargs.pop('label_class', 'col-lg-4')
        field_class = kwargs.pop('field_class', 'col-lg-8 text-left')
        template_pack = kwargs.pop('template_pack', waves_settings.TEMPLATE_PACK)
        self.form_obj = form
        super(FormHelper, self).__init__(form)
        self.form_tag = form_tag
        self.form_class = form_class
        self.label_class = label_class
        self.field_class = field_class
        self.render_unmentioned_fields = False
        self.layout = Layout()
        self.template_pack = template_pack

    def set_layout(self, service_input, form=None):
        """
        Setup crispy form for a submission
        """
        css_class = ""
        field_id = "id_" + service_input.api_name
        dependent_on = ""
        dependent_4_value = ""
        has_sample = isinstance(service_input, FileInput) and service_input.input_samples.count() > 0
        has_dependent = service_input.dependents_inputs.count() > 0

        if has_dependent or has_sample:
            css_class = "has_dependent"

        field_dict = dict(
            css_class=css_class,
            id=field_id,
            title=service_input.help_text,
        )
        wrapper = dict()
        if service_input.parent is not None and not isinstance(service_input, FileInputSample):
            field_id += '_' + service_input.parent.api_name + '_' + service_input.when_value
            dependent_on = service_input.parent.api_name
            dependent_4_value = service_input.when_value
            field_dict.update(dict(dependent_on=service_input.parent.api_name,
                                   dependent_4_value=service_input.when_value))
            when_value = self.form_obj.data.get(service_input.parent.api_name, service_input.parent.default)
            if service_input.when_value != when_value:
                wrapper = dict(wrapper_class="hid_dep_parameter", disabled="disabled")
            else:
                wrapper = dict(wrapper_class="dis_dep_parameter")
        # file inputs
        if isinstance(service_input, FileInput):
            all_sample = []
            if has_sample:
                for sample in service_input.input_samples.all():
                    all_sample.append(
                        Field('sp_' + service_input.api_name + '_' + str(sample.pk),
                              dependent_on=service_input.api_name,
                              dependent_4_value=dependent_4_value, **wrapper)
                    )
            field_dict.update(wrapper)
            input_field = Div(
                Field(service_input.api_name, **field_dict),
                *all_sample
            )

            if service_input.allow_copy_paste:
                cp_input_field = Field('cp_' + service_input.api_name, css_id='id_' + 'cp_' + service_input.api_name)
                tab_input = bootstrap.Tab(
                    "File Upload",
                    input_field,
                    css_id='tab_' + service_input.api_name
                )
                self.layout.append(
                    Div(
                        bootstrap.TabHolder(
                            tab_input,
                            bootstrap.Tab(
                                "Copy/paste content",
                                cp_input_field,
                                css_class='copypaste',
                                css_id='tab_cp_' + service_input.api_name,
                                dependent_on=dependent_on,
                                dependent_4_value=dependent_4_value,
                            ),
                            css_id='tab_holder_' + service_input.api_name,
                        ),
                        id='tab_pane_' + service_input.api_name,
                        css_class=wrapper['wrapper_class'],
                        dependent_on=dependent_on,
                        dependent_4_value=dependent_4_value
                    )
                )

            else:
                self.layout.append(input_field)
        elif not isinstance(service_input, FileInputSample):
            input_field = Field(service_input.api_name, **field_dict)
            self.layout.append(input_field)

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
            bootstrap.FormActions(
                Reset('reset', 'Reset form'),
                Submit('save', 'Submit a job')
            )
        ])
