Stats
==================

The actions command is used to create user defined actions.  This is how the functionality of outbit is extended and customized for each environment.

.. sourcecode:: bash

    outbit> stats
      Jobs Submitted Per User
    ###############################################################################
    ███████████████████████████████████████████████████████████████  99  superadmin
                                                                      1  user1

    outbit> stats type=system
      Changes Per Inventory Item
    ######################################################################################################
    ██████████████████████████████████████████████████  22  testhost1
    █████████████████████████████████████████████████   21  testhost2

    outbit> stats type=jobs
      Jobs Submitted By Date
    ###############################################################################
    ██████████████████████████████████████████████████████████  3  07/14/2016
    ███████████████████                                         1  08/31/2016
    ███████████████████                                         1  01/29/2017
