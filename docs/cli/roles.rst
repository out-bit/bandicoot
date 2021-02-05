Roles
==================

The roles command is used to manage Role Base Access control. With the roles command you can limit what actions and secrets users have access to. By default, when a user is created they do not have access to anything within bandicoot.  By creating and assigning users to roles you can extend there permissions and ability to perform actions within bandicoot. On a default install of bandicoot the "super" role is created, this role has access to all actions "/" and by default only the superadmin is assigned to this role.

.. sourcecode:: bash

    bandicoot> roles list
      actions="/"   name="super"   users="superadmin"
    bandicoot> roles add name=auditor action="/logs" users="jdoe1,jdoe2"
      created role auditor
    bandicoot> roles edit name=auditor action="/logs" users="jdoe1" secrets="secret1"
      modified role auditor
    bandicoot> roles del name=auditor
      deleted role auditor
