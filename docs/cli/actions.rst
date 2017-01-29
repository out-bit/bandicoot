Actions
==================

The actions command is used to create user defined actions.  This is how the functionality of outbit is extended and customized for each environment.

.. sourcecode:: bash

    outbit> actions add name=helloworld action=helloworld category=/testing command_run="echo 'hello world'" desc="print hello world" plugin=command
    outbit> actions add name="ansibletest" action="ansibletest"   category="/"   desc="test ansible"  playbook="playbooks/update_webserver.yml"   plugin="ansible"   source_url="https://github.com/starboarder2001/yourgitrepo.git"   sudo="yes"
    outbit> actions list
      name="helloworld" action="helloworld"   category="/testing"   command_run="echo 'hello world'"   desc="print hello world"   plugin="command"
      name="ansibletest" action="ansibletest"   category="/"   desc="test ansible"  playbook="playbooks/update_webserver.yml"   plugin="ansible"   source_url="https://github.com/yourusername/yourgitrepo.git"   sudo="yes"
    outbit> help
      ...
      ....
      testing helloworld
    outbit> actions edit name=helloworld action=helloworld category=/ command_run="echo 'hello world'" desc="print hello world" plugin=command
    outbit> help
      ...
      ....
      helloworld
    outbit> actions del name=helloworld
      deleted action pwd
