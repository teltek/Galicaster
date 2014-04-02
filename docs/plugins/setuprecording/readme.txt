Displays an editor to confirm/modify the recording metadata before starting it
==============================================================================

The 'setuprecording' plugin pops up a metadata editor when the "REC" button is pressed. This editor can be used to confirm and/or edit metadata before the recording starts.

Additionally, the plugin may be configured to set up a default value for any of the metadata types currently available, thus relieving the user from the need to input the same data again and again.

Combined with the ability to block the edition of certain metadata (see the 'metadata' section), this feature may be used to force some metadata values (the specific metadatum takes the default value, but the user cannot edit it).

The following (unquoted) configuration keys are available:
   - 'title': Sets up the recording's default title.
   - 'presenter' or 'creator': Sets up the recording's default "Presenter".
   - 'description': Sets up the recording's default "Description".
   - 'language': Sets up the recording's default language.
   - 'series', 'ispartof' or 'isPartOf': Sets up the recording's default series ID. 
                                         Such ID must exist in the attached Matterhorn system,
					 otherwise it will be ignored.

All the previous parameters (except 'series' and its equivalents) can include "placeholders", i.e. tags that are automatically substituted by other values on runtime. Currently, only one placeholder is available:
   - '{user}': Every appearance of this tag in the previous parameters will be substituted by the current Unix username. 


For instance, to make the "Presenter" metadatum be the current Unix username by default, one could add the following snippet to the 'conf.ini' file:

[setuprecording]
presenter = {user}

A more complex example:

[setuprecording]
title = {user}'s recording
description = Default description
presenter = {user}


To activate this plugin:

[plugins]
setuprecording = True
