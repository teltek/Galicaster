REST interface - Experimental
=============================

This plugin provides a simple REST web interface to retrieve information or control some actions on a running Galicaster instance.
This module requires the installation of the additional package python-bottle.

The available endpoints are:

    /state: Show several state values.
    /repository: List all the recordings.
    /repository/<id>: Get the manifest of the MediaPackage with the ID <id> in XML format.
    /metadata/<id>: Get the manifest of the MediaPackage with the ID <id> in JSON format.
    /start: Start a manual recording.
    /stop: Stop current recording.
    /operation/ingest/<id>: Ingest the MediaPackage with ID <id>.
    /operation/sidebyside/<id>: Export the MediaPackage with ID <id> as a side-by-side composition.
    /operation/exporttozip/<id>: Export the Mediapackage with ID <id> as a ZIP file.
    /screen: get a screenshoot of the active screen.
    /logstale": check if log is stale (threads crashed).

The REST server is listening in the port 8080 in all interfaces.
It can be accessed via localhost:8080 when the application is running.
It is posible to modify both the host and the port.

Loading and configuration
-------------------------

In the configuration file, include the following code with your values of choice:

[plugins]
rest = True

[rest]
host = 0.0.0.0
port = 8080
