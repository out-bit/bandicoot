GUI
==================

The bandicoot GUI is best run using Docker.

Install and Starting the bandicoot api server, gui, and cli using Docker.

.. sourcecode:: bash

  $ docker pull starboarder2001/bandicoot
  $ docker run -d -p 8088:8088 -p 80:80 -p 443:443 starboarder2001/bandicoot


Connect using the cli with the below command and make sure to change the default password of 'superadmin'.

.. sourcecode:: bash
  $ bandicoot -k -s $hostname

Connect to the host on port 443 for the GUI.
