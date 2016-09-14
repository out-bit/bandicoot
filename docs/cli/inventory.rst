Inventory
==================

The inventory command is used to manage the outbit host inventory. The inventory is automatically discovered when you run an action that uses the ansible plugin.  Changes are logged and can be checked using the "logs" command with the type=changes option.

.. sourcecode:: bash

    outbit> inventory list
      hostname1
    outbit> inventory del name=hostname1
      deleted inventory item hostname1
