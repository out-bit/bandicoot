Logs
==================

The logs command will display the history of everything run by bandicoot.  Running logs without any options will result in showing all the requests made to the bandicoot api server, even invalid requests that could not be processed.  If you specify a specific type, such as type=changes, it will show all the changes that were made to the bandicoot inventory.  The option type=changes is useful to audit changes made to systems using bandicoot.

.. sourcecode:: bash

    bandicoot> logs
      username      category    action  options date
      superadmin    /users      list    None    06/18/2016 14:20
      superadmin    /           help    None    06/18/2016 14:20
      superadmin    /testing    ls      None    06/18/2016 14:20
      superadmin    /testing    pwd     None    06/18/2016 14:20
    bandicoot> logs type=changes
      inventory_item                desc            job_id          date
      hostname1                     setup           82      07/14/2016 35:04
      hostname1                     apt-get update  82      07/14/2016 35:04
      hostname1                     apt-get upgrade 82      07/14/2016 35:04
      hostname2                     apt-get upgrade 84      07/14/2016 44:04
      hostname3                     apt-get upgrade 83      07/14/2016 44:04
      hostname4                     apt-get upgrade 85      07/14/2016 04:05
    bandicoot> logs type=changes name=hostname4
      inventory_item                desc            job_id          date
      hostname4                     apt-get upgrade 85      07/14/2016 04:05