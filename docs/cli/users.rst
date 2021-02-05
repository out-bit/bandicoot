Users
==================

The users command is used to manage user accounts that can login and interact with bandicoot.

.. sourcecode:: bash

    bandicoot> users list
      superadmin
    bandicoot> users add username=jdoe1 password=jdoe1
      created user jdoe1
    bandicoot> users edit username=jdoe1 password="new password"
      modified user jdoe1
    bandicoot> users del username=jdoe1
      deleted user jdoe1

To edit your own password, you can use "users edit password=newpassword". In the below example the logged in user is jdoe1. If the username is omitted then it changes the password of the current user.

.. sourcecode:: bash

    bandicoot> users edit password="new password"
      modified user jdoe1
    bandicoot> users edit username=jdoe1 password="new password"
      modified user jdoe1
