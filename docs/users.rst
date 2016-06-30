Users
==================

The users command is used to manage user accounts that can login and interact with outbit.

.. sourcecode:: bash

    outbit> users list
      superadmin
    outbit> users add username=jdoe1 password=jdoe1
      created user jdoe1
    outbit> users add username=jdoe1 password="new password"
      modified user jdoe1
    outbit> users del username=jdoe1
      deleted user jdoe1
