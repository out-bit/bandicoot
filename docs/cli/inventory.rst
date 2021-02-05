Inventory
==================

The inventory command is used to manage the bandicoot host inventory. The inventory is automatically discovered when you run an action that uses the ansible plugin.  Changes are logged and can be checked using the "logs" command with the type=changes option.

.. sourcecode:: bash

    bandicoot> inventory list
      hostname1
    bandicoot> inventory del name=hostname1
      deleted inventory item hostname1
