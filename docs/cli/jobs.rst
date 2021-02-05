Jobs
==================

The jobs command is used to manage running and previously completed jobs. A job is when you execute a specific action that is long running.  The "jobs list" command will print the list of recently run jobs.  The "jobs status" command will show the result of the job.

This example assumes an action named ansibletest exists and uses the ansible plugin. Below is an example for creating the ansibletest action.

.. sourcecode:: bash

  bandicoot> actions add name=ansibletest action=ansibletest category=/ desc="test ansible" playbook="update_webserver.yml" plugin="ansible" source_url="https://gitexample/something.git" sudo="yes"

Below shows running the action which creates a job.  ctrl-z is then pressed to background the job and the "jobs list" command is used to see the running job and previously run jobs.  The "job status" command is used to check the result of the job.

.. sourcecode:: bash

  bandicoot> ansibletest

  Job is running with id=17. Press ctrl-z to background job.

  bandicoot> jobs list
    Job ID        Is Running?     User    Command
    16            False           superadmin              /ansibletest
    17            True            superadmin              /ansibletest

  bandicoot> jobs status id=17
    Cloning into '/tmp/bandicoot/1467473131.22'...

  bandicoot> jobs kill id=17
    The job 17, was terminated