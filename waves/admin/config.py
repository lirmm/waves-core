from django.contrib import admin
from constance.admin import ConstanceAdmin, ConstanceForm, Config


class CustomConfigForm(ConstanceForm):
    def __init__(self, *args, **kwargs):
        super(CustomConfigForm, self).__init__(*args, **kwargs)
        # ... do stuff to make your settings form nice ...


class ConfigAdmin(ConstanceAdmin):
    class Media:
        js = (
            'waves/js/bootstrap-switch.min.js',
        )
        css = {
            'all': ('waves/css/bootstrap-switch.min.css',)
        }
    change_list_form = CustomConfigForm
    # change_list_template = 'admin/config/settings.html'

admin.site.unregister([Config])
admin.site.register([Config], ConfigAdmin)
