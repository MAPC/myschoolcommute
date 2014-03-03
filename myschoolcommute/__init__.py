EXTRA_LANG_INFO = {
    'ht': {
        'bidi': False,
        'code': 'ht',
        'name': 'Haitian Creole',
        'name_local': u'Krey\xf2l',
    },
}

# Add custom languages not provided by Django
import django.conf.locale
from django.conf import global_settings
django.conf.locale.LANG_INFO.update(EXTRA_LANG_INFO)
