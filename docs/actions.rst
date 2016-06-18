outbit Actions
==================

The actions command is used to create user defined actions.  This is how the functionality of outbit is extended and customized for each environment.

.. sourcecode:: bash
    outbit> actions add name=helloworld action=helloworld category=/testing command_run="echo 'hello world'" desc="print hello world" plugin=command
    outbit> actions list
      action="helloworld"   category="/testing"   command_run="echo 'hello world'"   desc="print hello world"   name="helloworld"   plugin="command"
    outbit> help
      ...
      ....
      testing helloworld            print hello world
    outbit> actions edit name=helloworld action=helloworld category=/ command_run="echo 'hello world'" desc="print hello world" plugin=command
    outbit> help
      ...
      ....
      helloworld            print hello world
    outbit> actions del name=helloworld
      deleted action pwd
