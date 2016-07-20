Users
==================

The users command is used to manage user accounts that can login and interact with outbit.

.. sourcecode:: bash

    outbit> users list
      superadmin
    outbit> users add username=jdoe1 password=jdoe1
      created user jdoe1
    outbit> users edit username=jdoe1 password="new password"
      modified user jdoe1
    outbit> users del username=jdoe1
      deleted user jdoe1

To edit your own password, you can use "users edit password=newpassword". In the below example the logged in user is jdoe1. If the username is omitted then it changes the password of the current user.

.. sourcecode:: bash

    outbit> users edit password="new password"
      modified user jdoe1
    outbit> users edit username=jdoe1 password="new password"
      modified user jdoe1
