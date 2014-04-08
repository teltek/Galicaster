How to configure sudoers so that regular users don't have access (read and write) permissions to galicaster's log and configuration files.

This configuration could be useful for security reasons and in order to create a multiuser environment (see setuprecording plugin).

NOTE: ALL THESE STEPS HAVE BEEN TESTED ON UBUNTU (12.04.4 at the moment).

Steps:

1.- Create a new gcuser user

$ sudo adduser --system --quiet --home /var/lib/gcuser --shell /bin/false --group --gecos "Galicaster Administrator" gcuser

2.- Create a new gcusers group

$ sudo addgroup --system --quiet gcusers

3.- Change galicaster log and conf files permissions.

$ ETCDIR="/etc/galicaster"
$ LOGDIR="/var/log/galicaster"

$ sudo chown -R gcuser:gcuser ${ETCDIR}
$ sudo find ${ETCDIR} -type d -exec chmod 0770 {} \;
$ sudo find ${ETCDIR} -type f -exec chmod 0660 {} \;

$ sudo install -d -o gcuser -g gcuser -m770 ${LOGDIR}
$ sudo touch ${LOGDIR}/galicaster.log
$ sudo chown gcuser:gcuser ${LOGDIR}/galicaster.log
$ sudo chmod 660 ${LOGDIR}/galicaster.log

4.- Add the application to sudoers.d

$ sudo sh -c 'cat >/etc/sudoers.d/galicaster <<EOF
%gcusers ALL=(gcuser:gcuser) NOPASSWD: /usr/bin/python /usr/share/galicaster/run_galicaster.py
EOF'
$ sudo chmod 0440 /etc/sudoers.d/galicaster


5.- Modify galicaster bin

$ sudo sh -c 'cat >/usr/bin/galicaster <<EOF
#!/bin/sh
sudo -g gcuser /usr/bin/python /usr/share/galicaster/run_galicaster.py
EOF'
$ sudo chmod -R 755 /usr/bin/galicaster


6.- Add the normal user to the gcusers group (you need to do this for each user you want to be able to run galicaster)

$ sudo addgroup `whoami` gcusers

Finally you need to close the session so the permission changes are applied correctly.

If you use a single repository for recordings common to all users, permissions have to allow read and write for all those users, so it should allow writing to group gcuser.

NOTE: ALL THE PROFILES CREATED IN /etc/galicaster/profiles SHOULD HAVE THE RIGHT PERMISSIONS (SEE 3)

