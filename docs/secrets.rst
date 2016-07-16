Secrets
==================

The secrets command is used to manage passwords, ssh keys, git keys, credentials, and other sensitive information that might be required by an action.  These values are not visible to users after they are stored in the database, but actions users can execute may access them.

.. sourcecode:: bash

    outbit> secrets add name=neptune_rootpw secret='verysecretpassword' desc="root pw for neptune server"
      created secret neptune_rootpw
    outbit> secrets edit name=neptune_rootpw secret="newpassword" desc="root pw for neptune server"
      modified secret neptune_rootpw
    outbit> secrets list
      desc="root pw for neptune server"   name="neptune_rootpw"   secret="..."
    outbit> secrets del name=neptune_rootpw
      deleted secret neptune_rootpw
