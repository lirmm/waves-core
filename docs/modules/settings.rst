Application custom settings
===========================

WAVES application defines a waves_settings attributes generated from WAVES_CORE Django settings dictionary,

    .. automodule:: waves.wcore.settings
        :members: waves_settings

    .. note::
        You may override these values in settings with a dict named WAVES_CORE


Here are the defaults values:

    .. literalinclude:: ../../waves/wcore/settings.py
        :language: python
        :lines: 52-86
