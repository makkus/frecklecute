###################
Creating a new user
###################

This is (obviously) a rather trivial example, but I hope it'll show how, compared to writing a shell script, this approach is both simpler, quicker, and also probably more robust. For the purpose of this example, we'll assume the ``sudo`` executable is available on our system.

Simplest usecase, hardcoded username/password
*********************************************

We're going to write a *frecklecutable* that will create a new user (username: makkus) on our system, with the initial password 'change_me'. We'll also make sure that that new user will be able to `use password-less sudo <https://www.simplified.guide/linux/enable-passwordless-sudo>`_. If you've never needed password-less sudo, just assume (for now) that it is necessary every now and then.

Here's the most simple, and also shortest *frecklecutable* to do this, we'll save it in a file called ``new-admin-user``:

.. code-block:: yaml

    tasks:
      - USER:
          name: "makkus"
          state: present
          password: "$6$C5muYRFv$dOmuxzHScMNWbrSQ94QXbzShEZ5r4HPZdQK/Ybj3ypKkcYcuYzcf.p1Oh.XNeZ4NM5SrY74b0GaEcDWI/CJWj0"
      - LINEINFILE:
          dest: /etc/sudoers
          state: present
          regexp: "^%makkus"
          line: "%makkus ALL=(ALL) NOPASSWD: ALL"

Let's go through every section, to understand what this is doing:

``tasks``:
    ``tasks`` is the only keyword that is necessary for a *frecklecutable* to be useful. It indicates to *frecklecute* that it's value is a list of tasks to be executed.

``USER``:
    the first task to be executed. This refers to the `Ansible user module <http://docs.ansible.com/ansible/latest/modules/user_module.html#user-module>`_, which is a fairly basic and central one which helps to manage every aspect of a user account on a system. *frecklecute* uses the convention that, if a task-name is written in all-uppercase, elevated (root) privileges are required to execute it.

    In this example we are using it to create a new user. To be exact, we are using it to ensure that a certain user account exists on our system. For now, let's hard-code the user name and password (which is created `using the `mkpasswd tool <http://docs.ansible.com/ansible/latest/reference_appendices/faq.html#how-do-i-generate-crypted-passwords-for-the-user-module>`_) in our script.

``LINEINFILE``:
    this second task uses the `lineinfile Ansible module <http://docs.ansible.com/ansible/latest/lineinfile_module.html>`, which helps making sure that a certain line of text is present in a file.

    The module documentation explains all the ways this can be done, in our example we use it to look for a line in the file ``/etc/sudoers`` that starts with ``%makkus``. If that exists, it will make sure that the whole line equals ``%makkus ALL=(ALL) NOPASSWD: ALL`` (which is telling ``sudo`` to not require a password when user ``makkus`` executes a command with it.

    As with the task above, this task will be executed with elevated privileges as the task-name is all upper-case.

Right, let's execute the *frecklecutable*:

.. code-block:: console

    > frecklecute new-admin-user

    Please enter sudo password for this run: <user_password_entry>

    * executing tasks (on 'localhost')...

     * starting custom tasks:
       * USER... ok (changed)
       * LINEINFILE... ok (changed)
     => ok (no change)

We need to use the ``--password ask`` option, because at least one of the tasks in our *frecklecutable* needs elevated privileges. If the user that executes this is root, or has password-less sudo privileges themselves, this is not necessary.

Now we can get some information for this new user with the ``finger`` command:

.. code-block:: console

   >  finger makkus
   Login: makkus                       Name:
   Directory: /home/makkus             Shell: /bin/sh
   Never logged in.
   No mail.
   No Plan.

Looks good.

Using cli args for username/password
************************************

Cool. Now let's make that script more useful by allowing other user-names than *'makkus'*, and also a specific (hashed) password. We also want every new user to have ``bash`` as their default shell, not just ``sh``:

.. code-block:: yaml

    args:
      - user
      - password

    tasks:
      - USER:
          name: "{{:: user ::}}"
          shell: /bin/bash
          state: present
          password: "{{:: password ::}}"
      - LINEINFILE:
          dest: /etc/sudoers
          state: present
          regexp: "^%{{:: user ::}}"
          line: "%{{:: user ::}} ALL=(ALL) NOPASSWD: ALL"

Here's what the new keys mean:

``args``
    the ``args`` keyword is optional, it contains a list of keywords that can be used as variables within the *frecklecutable* itself, for templating purposes. Those keywords will also dynamically create command-line arguments for the scriptlet, so users can specify the values easily.

    Here, we create two such variables: ``user`` and ``password``. The user-specified values to each of those variables will be used to replace the placeholders anywhere under the ``tasks`` keyword. The format of such a placeholder is ``{{:: <var-name> ::}}``.

Here's how our new *frecklecutable* renders it's help string:

.. code-block:: console

    > frecklecute new-admin-user --help

    Usage: frecklecute new-admin-user [OPTIONS]

    Options:
      --user TEXT       n/a
      --password TEXT   n/a
      --help            Show this message and exit.

    Details:
      Local path:  /frecklecute/examples/new-admin-user

And here is how we use it:

.. code-block:: console

    > frecklecute new-admin-user --user makkus2 --password '$6$C5muYRFv$dOmuxzHScMNWbrSQ94QXbzShEZ5r4HPZdQK/Ybj3ypKkcYcuYzcf.p1Oh.XNeZ4NM5SrY74b0GaEcDWI/CJWj0"'

    * executing tasks (on 'localhost')...

      * starting custom tasks:
        * USER... ok (changed)
        * LINEINFILE... ok (changed)
      => ok (changed)


Better command-line arguments
*****************************

This is already quite use-able, but there are a few improvements to how we describe those command-line arguments that would make the user-experience quite a bit better:

.. code-block:: yaml

    doc:
      help: |
         Creates a new admin user.

         The new user will be able to use sudo without having to enter their password.

    args:
      - user:
          required: true
          doc:
            help: "the name of the new user"
          click:
            argument:
              metavar: USERNAME
              type: str
              nargs: 1
      - password:
          required: false
          default: "$6$C5muYRFv$dOmuxzHScMNWbrSQ94QXbzShEZ5r4HPZdQK/Ybj3ypKkcYcuYzcf.p1Oh.XNeZ4NM5SrY74b0GaEcDWI/CJWj0"
          doc:
            help: "the hash of the users' password (use 'mpkasswd' or similar to create)"
          click:
            option:
              metavar: PASSWORD
              type: str
              param_decls:
                - "--password"
                - "-p"

    tasks:
      - USER:
          name: "{{:: user ::}}"
          shell: /bin/bash
          state: present
          password: "{{:: password ::}}"
      - LINEINFILE:
          dest: /etc/sudoers
          state: present
          regexp: "^%{{:: user ::}}"
          line: "%{{:: user ::}} ALL=(ALL) NOPASSWD: ALL"

What did we do here? Let's see:

``doc``:
    this (optional) block let's us write some documentation about the script and/or parameter, to be displayed to the user.

    the ``help`` sub-key is the most important one, as it's value will be displayed as parameter info or a mult-line help text for the whole script when the user requests it (see below). We use the ``|`` to specify a multi-line string as value (see `here <https://yaml-multiline.info/>`_ for all possible ways to do that).

``required``:
    this is one of the allowed keys to describe a variable (see here for more info: `variables <XXX>`_. We use it to make sure this variable is set by the user.

``click``:
    *'click'* is the name of the command-line argument parsing library that is used by *frecklecute*: `Click <http://click.pocoo.org/>`_. The value of this (optional) key is forwarded to the argument parsing engine of this library, and can be used to fine-tune the appearance of the command-line arguments you want to have displayed. More details: `click parameter specification <http://click.pocoo.org/6/api/#parameters>`_.

    In our case, we make the *user* key an argument to be used as single string at the end of the command, with 'USERNAME' as the value descriptor. And we specify that the value of *password* must be a string, and can be set by either using ``--password`` or the short-form ``-p``.


Let's see the new help output:

.. code-block:: console

    > frecklecute new-admin-user --help
    Usage: frecklecute new-admin-user [OPTIONS] USERNAME

     Creates a new admin user.

     The new user will be able to use sudo without having to enter their
     password.

    Options:
     -p, --password PASSWORD  the hash of the users' password (use 'mpkasswd' or
                              similar to create)
     --help                   Show this message and exit.

    Details:
      Local path:  /frecklecute/examples/new-admin-user

We need to specify a user-name now, otherwise there'll be an error:

.. code-block:: console

     > frecklecute new-admin-user
     Usage: frecklecute new-admin-user [OPTIONS] USERNAME

     Error: Missing argument "user".

We can create a new user with the default password:

.. code-block:: console

    > frecklecute new-admin-user makkus3
    * executing tasks (on 'localhost')...

     * starting custom tasks:
         * USER... ok (changed)
         * LINEINFILE... ok (changed)
       => ok (changed)

Or, we use a custom one (again, generated with ``mkpasswd``):

.. code-block:: console

    > frecklecute new-admin-user --password $6$WZZ/765yB0WjT$k76fu74SO8puQtAUQCsDRmwYOUdpDG6absOQ7SwOuHom.707fsthDO/F40C.3ZNv6CRM5DQI2t4nfWOeoGuJs1 makkus4

Alternative, non-short way to describe tasks
********************************************

Up until now, we used a short-form, convention-based format to write our tasks. This is fine for quick scripts, and (I think) makes it very easy to read them and figure out what they do.

If we want to be more formal, and have nicer output while *frecklecute* is running, we can also write it in a way that separates the task-item metadata and it's variables. In our case that would like this (ommitting the ``doc`` and ``args`` section, as that doesn't change:

.. code-block:: yaml

    tasks:
     - meta:
         name: user
         become: true
         task-desc: "creating user '{{:: user ::}}'"
       vars:
         name: "{{:: user ::}}"
         shell: /bin/bash
         state: present
         password: "{{:: password ::}}"
     - meta:
         name: lineinfile
         become: true
         task-desc: "setting up passwordless sudo for user '{{:: user ::}}'"
       vars:
         dest: /etc/sudoers
         state: present
         regexp: "^%{{:: user ::}}"
         line: "%{{:: user ::}} ALL=(ALL) NOPASSWD: ALL"

As you can see, we replaced every task with a dictionary containing two keywords: ``meta``, ``vars``. For more information about this format, please check out: `long tasks format <XXX>`_

This is how *frecklecute* looks like now, when run:

.. code-block:: console

    > frecklecute new-admin-user makkus5

    * executing tasks (on 'localhost')...

     * starting custom tasks:
         * creating user 'makkus5'... ok (changed)
         * setting up passwordless sudo for user 'makkus5'... ok (changed)
       => ok (changed)

Bit nicer, right?

Using "Ansible" task-list format
********************************

As *frecklecute* uses `Ansible <https://ansible.com>`_ as it's task execution engine, it is also possible, if you prefer or have some of those laying around, to use a plain `Ansible task list <http://docs.ansible.com/ansible/latest/user_guide/playbooks_intro.html#tasks-list>`_ in a *frecklecutable*. How this works exactly is `described here <XXX>`_.

Apart from the slightly different way the task items are written up, nothing much changes. You can, for example, still use the ``{{:: <var_name> ::}}" variable placeholders (at the same time as 'normal' Ansible variabls like ``{{ ansible_env.USER }}``.

As this is an a bit more advanced topic, I'll not go into any more details. But I'll show how our *frecklecutable* would look like in 'Ansible format' (again, with everything apart from the ``tasks`` value staying the same):

.. code-block:: yaml

    tasks:
      - name: "creating user '{{:: user ::}}'"
        user:
          name: "{{:: user ::}}"
          shell: /bin/bash
          state: present
          password: "{{:: password ::}}"
        become: true
      - name: "setting up passwordless sudo for user '{{:: user ::}}'"
        lineinfile:
          dest: /etc/sudoers
          state: present
          regexp: "^%{{:: user ::}}"
          line: "%{{:: user ::}} ALL=(ALL) NOPASSWD: ALL"
        become: true
