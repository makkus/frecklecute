###################
Creating a new user
###################

This is (obviously) a rather trivial example, but I hope it'll show how, compared to writing a shell script, this approach is both simpler, quicker, and also probably more robust. For the purpose of this example, we'll assume the ``sudo`` executable is available on our system.

Simplest, usecase. Hardcoded username
*************************************

We're going to write a *frecklecutable* that will create a new user (username: makkus) on our system, with the initial password 'change_me'. We'll also make sure that that new user will be able to `use password-less sudo <https://www.simplified.guide/linux/enable-passwordless-sudo>`_. If you've never needed password-less sudo, just assume (for now) that it is necessary every now and then.

Here's the most simple, and also shortest *frecklecutable* to do this:

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
    this is the only keyword that is necessary for a *frecklecutable* to be useful. It indicates to *frecklecute* that it's value is a list of tasks to be executed.

``USER``:
    *frecklecute* is built on top of `Ansible <https://ansible.com>`_, and the ``USER`` keyword refers to an `Ansible module <http://docs.ansible.com/ansible/latest/user_guide/modules.html>`_. An 'Ansible module' is a basic building block that manages a single component on a system, in an idempotent way. That means, however often you run that task with the same configuration on the same machine, that machine's state will always be the same after every such run (if the task doesn't fail, of course). This is a very important concept in configuration management, as otherwise you could not be sure about the state your machine is in after your run.

    Ansible ships with a `ton of such <http://docs.ansible.com/ansible/latest/modules/list_of_all_modules.html>`_ modules, and there is one for every task imaginable. In our example, we are referring to the `user module <http://docs.ansible.com/ansible/latest/modules/user_module.html#user-module>`_. The 'user module' is a fairly basic and central one that is often used, and which helps to manage every aspect of a user account on a system. We are using it here to create a new user. Actually, to be exact, we are using it to ensure that a certain user account exists on our system. This is the idempotency-thing I was talking about earlier: if the user exists already, this will not error out or do anything extra. This removes a lot of exception handling and similar boilerplate we would have to do otherwise (e.g. in a shell script).
