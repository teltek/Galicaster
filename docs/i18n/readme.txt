== Internationalizing Galicaster ==

Galicaster is using the standard 'gettext' utilities to provide support for localizing the UI messages. 

The approach for l10n Galicaster is as follows:

1- Create a new directory in <GALICASTER_HOME>/i18n corresponding to your language. <GALICASTER_HOME> is the location 
   of the source code of Galicaster.
   * You may use an ISO-639 language code (like 'en' for English or 'es' for Spanish), or the standard Unix-like
     locale format (for instance 'en_US' for "United States English" vs. 'en_GB' for "British English" or 
     'es_ES' for "Castilian Spanish" vs. 'es_AR' for "Argentinian Spanish"). 

2- Copy the .pot file in <GALICASTER_HOME>/i18n/galicaster.pot into your newly-created language directory and rename
   it to 'galicaster.po'.

3- Translate the strings present in the 'galicaster.po' file. The translatable strings are those starting with the
   keyword 'msgid', and their translation is expected in the lines starting with 'msgstr' that follow.
   * The headers at the beginning of the file are not mandatory, but translations are welcome to fill in those, too,
     because they provide more information about the translation process and help maintaining them through different
     versions.

4- To test your translated .po file: 
   * Create a folder named LC_MESSAGES into your specific language directory (the one created in the step #1).
   * Run the following command in a terminal:
  
     $> msgfmt <GALICASTER_HOME>/i18n/<YOUR_LANGUAGE_DIR>/galicaster.po -o <GALICASTER_HOME>/i18n/<YOUR_LANGUAGE_DIR>/LC_MESSAGES/galicaster.mo

     , where <GALICASTER_HOME> is the location of Galicaster's source code and <YOUR_LANGUAGE_DIR> is the directory created in the step #1.
     This should create a galicaster.mo file in the LC_MESSAGES subdirectory. 

   * If your system language is set to the same language you are localizing to, simply running Galicaster should show the UI in your language.
     Otherwise, you may "force" a specific language by using the following command line to launch Galicaster:

     $> 'LANGUAGE="<LANGUAGE_CODE>" python <GALICASTER_HOME>/run_galicaster.py'

     , where <LANGUAGE_CODE> is your preferred code language, which should be the same as the name of the directory created in the step #1

5- Issue a 'pull request' of your translated file, so that it is included in the Galicaster codebase. 



-- A word on the gettext workflow.

The following is a summary of the main steps in the whole gettext software i18n process. You may find the detailed explanation in the
official online manual here: http://www.gnu.org/software/gettext/manual/gettext.html

1- The strings that are to be localized into different languages are marked in the source code. A special function, accepting a string in the
   source language (normally English) and returning the appropriate translation is used. This function is usually '_', in order to introduce
   a minimun overhead in the source code. 
   Other patterns can be used to mark strings for i18n. Please read the 'Extra symbols used in the code' section below.

2- Create a translation template. In this step, an analyzing tool is used to extract the strings used as arguments for the '_' function from 
   the source code. The command line used in Galicaster (run from the root source directory) is:
   
   $> xgettext -p i18n -kN_ $(find . -name '*.py' -o -name '*.glade') -o galicaster.pot

3- Translations to the different languages are created from the template 'galicaster.pot' file, as described in the previous section. If a
   translated .po file already exists, it can be updated with a new .pot file by using the command 'msgmerge'. The updated .po file will 
   keep the already translated strings, so that the translator can concentrate on the new ones.

4- The translated .po files must be converted into a machine-readable format in order to be used by the program. This conversion can be done
   with the command: 

   $> msgfmt <GALICASTER_HOME>/i18n/<YOUR_LANGUAGE_DIR>/galicaster.po -o <GALICASTER_HOME>/i18n/<YOUR_LANGUAGE_DIR>/LC_MESSAGES/galicaster.mo

   In this case, the .mo file is stored at a custom location, but there are standard locations for the .mo files in the directory structure
   (normally /usr/share/locale or similar locations).


-- Extra symbols used in the Galicaster code

When recreating the .pot file, remember to include the symbol 'N_' in the command xgettext. 
This function is a "no-op" that is used to mark the strings to be i18n'ed, but leave them as they are, because
the original string is used "as-is" in the code, and cannot be translated until the very moment it is printed
on the screen. For instance:

    myvar = "Recording"
    ...

    if myvar == "Recording":
       #do stuff       
    ...

    fancy_display_function(myvar, etc...)


If the translation function '_()' is added to 'myvar' when it is created, then it has to be applied to all the
string literals that appear in the code:

    myvar = _("Recording")
    ...

    if myvar == _("Recording"):
       #do stuff       
    ...

    fancy_display_function(myvar, etc...)


This is a clumsy approach to i18n, because all the strings (even those that will never be displayed) have to be
i18n'ed, and we cannot anticipate whether their translated value will cause problems in the program.


Also, if the code includes something like the following snippet:

    if "ing" in myvar:
       # do other stuff
    ...

there is no way to anticipate whether the pattern "ing" will remain the same in other languages (there may not
be a pattern in the translated terms at all). Of course this is a very exaggerated example, but similar issues 
may appear in real code.

The right approach would be defining 'N_()' as a no-op function and use it in the definition of the variable, then
use the real '_()' when the value is displayed:

    # N_() simply returns what it gets
    def N_(string): return string

    myvar = N_("Recording")
    ...

    if myvar == "Recording":
       #do stuff       
    ...

    # 'myvar' is "Recording", because 'N_()' does nothing
    if "ing" in myvar:
       # do other stuff
    ...

    # Translate the value of 'myvar' here, when it's displayed
    fancy_display_function(_(myvar), etc...)


'N_' is simply a marker for the xgettext command to collect that string and make it localizable. Therefore, the 
command line must include the parameter -kN_ (--keyword=N_) to let xgettext know that has to pay attention to collect
the arguments of the 'N_' function too.
