Hide certain tabs in the recording UI
=====================================                                     

The 'hidetabs' plugin allows for the tabs in the recording UI to be hidden. Also, the default tab, shown displayed when the UI is shown for the first time, can be defined.

Tabs that SHOULD NOT be displayed are specified with the 'hide' parameter. This parameter admits the following values (unquoted), which meaning should be self-evident:
   - 'events'
   - 'recording'
   - 'status'
The parameter may contain a space-separated list with any of the previous labels.

The tab shown by default after starting Galicaster may be specified with the 'default' parameter. This parameter may contain one (and only one) label from the ones defined in the previous paragraph.

Usage example:

[hidetabs]
hide = events
default = recording


In order to activate this plugin:

[plugins]
hidetabs = True
