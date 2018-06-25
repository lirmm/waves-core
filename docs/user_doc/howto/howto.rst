How to build a simple service in WAVES-core
===========================================

Here you can follow a step by step process to create from scratch your first "hello world" service on your computer.
We assume WAVES-core is installed (see :ref:`installation-label` section)

Add a Computing infrastructure
------------------------------

In WAVES-core menu, click on "Add", this will display the "Add Computing infrastructure" page.
A second way is to click on "Computing infrastructure" and on the top right button "ADD COMPUTING INFRASTRUCTURE" of the listing page.

Click "Show" behind "Main"

Name the computing infrastructure t ocreate. Caution, this label will be displayed later on services forms, choose an explicit name.\
If left empty, it will be automatically named.

**Run on:**
Select "Local script", the *label* is automatically filled with "LocalShellAdaptor".

Click "Save".

You may check by clicking the "TEST CONNECTION" button on top right corner.


Add a Service
-------------
Go back to main menu, click "Add" on "Services" line or click "Services" and "ADD SERVICE" on the top right of the listing page.

Give a name to the service to create :
**Service name:** SayHello

And select an infrastructure (the one we've just created) :
**Computing infrastructure** LocalShellAdaptor

Click "Save and continue editing".

Click "Show" behind "Execution parameters".
Add the command to be executed.
**command** echo

Click "Save and continue editing".

Now, the service is configured to pass the command "echo" on a local shell. \
This command requires an input (the string to echo). This is acheived bt configurung the submission method.


Modify Submission methods
-------------------------
Click "Show" behind "Submission methods".
Click "Change" on top left of the default method line.
Click "Show" behind "Inputs"

Click "Add another input", a new window popup:
Choose "Text Input" and "SAVE" on the popup window
Fill the "Add Text Input" form :
**Label:** Some words
**Parameter name:** value
**Command line format:** Positional parameter: value
Click "SAVE", the popup window closes

Click "Save and back"

The new service is created. We can try it right now !

Try your new service
--------------------
Click "PREVIEW" on top right button

The popup window displays the automatically generated form.

**Some words** Hello world

Remember the name of your analysis or the ID created when submitting the job.
Click "Submit a job", the message "Job successfully submitted xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" appears.
Click the bottom right button "Close".

Now, you may check if your job is well executed.

Follow the Job execution
------------------------
Click "JOBS" on top right button.
This page list all the jobs, find yours by the ID or name previously noted.
Click "VIEW ON WEBSITE" on the top right button.
Look at job details, on "Standard output" you can note your "Hello world" was echoed successfully.
