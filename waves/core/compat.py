"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from django.conf import settings

__all__ = ["available_themes", "list_themes", "RichTextField", "CompactInline", "SortableInlineAdminMixin"]


if 'jet' in settings.INSTALLED_APPS:
    _temp = __import__('jet.admin', globals(), locals(), ['CompactInline'], -1)
    CompactInline = _temp.CompactInline
else:
    from django.contrib.admin import StackedInline

    class CompactInline(StackedInline):
        """ Inherit base class """
        pass

if 'ckeditor' in settings.INSTALLED_APPS:
    _temp = __import__('ckeditor.fields', globals(), locals(), ['RichTextField'], -1)
    RichTextField = _temp.RichTextField
else:
    from django.db.models import TextField

    class RichTextField(TextField):
        """ Override RichTextField """
        pass

if 'bootstrap_themes' in settings.INSTALLED_APPS:
    _temp = __import__('bootstrap_themes', globals(), locals(), ['list_themes', 'available_themes'], -1)
    list_themes = _temp.list_themes
    available_themes = _temp.available_themes
else:
    available_themes = (
        ('default', 'Default'),
    )

    def list_themes():
        return available_themes

if 'adminsortable2' in settings.INSTALLED_APPS:
    _temp = __import__('adminsortable2.admin', globals(), locals(), ['SortableInlineAdminMixin'])
    SortableInlineAdminMixin = _temp.SortableInlineAdminMixin
else:
    class SortableInlineAdminMixin(object):
        pass
