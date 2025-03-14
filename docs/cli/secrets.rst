Secrets
==================

The secrets command is used to manage passwords, ssh keys, git keys, credentials, and other sensitive information that might be required by an action.  These values are not visible to users after they are stored in the database, but actions users can execute may access them.

Adding, Editing, and Deleting Secrets

.. sourcecode:: bash

    bandicoot> secrets add name=neptune_rootpw secret='verysecretpassword' desc="root pw for neptune server"
      created secret neptune_rootpw
    bandicoot> secrets edit name=neptune_rootpw secret="newpassword" desc="root pw for neptune server"
      modified secret neptune_rootpw
    bandicoot> secrets list
      desc="root pw for neptune server"   name="neptune_rootpw"   secret="..." status="encrypted"
    bandicoot> secrets del name=neptune_rootpw
      deleted secret neptune_rootpw

Examples of migrating secrets encrypted with an older "encryption_password" or unencrypted secrets

.. sourcecode:: bash

    bandicoot> secrets encryptpw
      secret secretusingoldpw encrypted using new password
    bandicoot> secrets encryptpw name=noencsecret
      secret noencsecret updated to new password
