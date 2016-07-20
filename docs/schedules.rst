Schedules
==================

The schedules command is used to manage scheduled jobs, it works similar to a linux cron.

.. sourcecode:: bash

    outbit> schedules add name=patchdmz hour=16
      created schedule patchdmz
    outbit> schedules edit name=patchdmz category=/ action=patchdmz minute=30 hour=20 day_of_month=* month=* day_of_week=*
      modified schedule patchdmz
    outbit> schedules list
      patchdmz
    outbit> schedules del name=patchdmz
      deleted schedule patchdmz
