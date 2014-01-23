== Extra symbols used in the code ==

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
