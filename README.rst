===========
frecklecute
===========


.. image:: https://img.shields.io/pypi/v/frecklecute.svg
        :target: https://pypi.python.org/pypi/frecklecute

.. image:: https://img.shields.io/travis/makkus/frecklecute.svg
        :target: https://travis-ci.org/makkus/frecklecute

.. image:: https://readthedocs.org/projects/frecklecute/badge/?version=latest
        :target: https://frecklecute.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/makkus/frecklecute/shield.svg
     :target: https://pyup.io/repos/github/makkus/frecklecute/
     :alt: Updates


An interpreter for simple scriptlets that let you get your machine quickly into a desired state. Cross-platform (Linux, Mac OS X), cross-host-type (physical, remote, virtual, container).

Always thought having a reproducible, share-able and managed way to setup a machine or working/project-environment would be neat, but setting up a fully-fledged  `configuration-management <https://en.wikipedia.org/wiki/Configuration_management>`_ environment like `Ansible <https://ansible.com>`_, `Puppet <https://puppet.com>`_, or `SaltStack <https://saltstack.com>`_ seemed just a tad to intimidating? Or it'd be a bit overkill to do for just this one small project? But writing shell scripts is a tad too low-level and cumbersome?

Then, give *frecklecute* a go! It provides a quick way to provision/set-up single machines in a descriptive and reproducible manner. Independent of the machine type (physical, virtual, container), platform and distribution.


Examples? Sure!
---------------

Create a 'passwordless-sudo' user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's a small scriptlet ('``create-pwless-sudo-user``') -- I call those '*frecklecutables*' -- to create a new user (whose username can be specified as a command-line argument) who will be allowed to use passwordless sudo:

.. code-block:: yaml

    args:
      - user

    tasks:
      - USER:
          name: "{{:: user ::}}"
          state: present
          password: "$6$C5muYRFv$dOmuxzHScMNWbrSQ94QXbzShEZ5r4HPZdQK/Ybj3ypKkcYcuYzcf.p1Oh.XNeZ4NM5SrY74b0GaEcDWI/CJWj0"
      - LINEINFILE:
          dest: /etc/sudoers
          state: present
          regexp: "^%{{:: user ::}}"
          line: "%{{:: user ::}} ALL=(ALL) NOPASSWD: ALL"

Now, we can execute the script like so:

.. code-block:: console

    > frecklecute create-pwless-sudo-user --user makkus

    * executing tasks (on 'localhost')...

      * starting custom tasks:
         * GROUP... ok (no change)
         * USER... ok (changed)
         * LINEINFILE... ok (changed)
        => ok (changed)

The newly created user will have the password '*change_me*' (hash was created with: ``mkpasswd -m sha-512 change_me``)This will work on (probably) all Linux distributions, as well as on most recent versions of Mac OS X. The only requirement is that the ``sudo`` command is available.

If you want to know how this works, and also for a nicer, more complete version of this *frecklecutable* (including command-line help text and a group creation task), check out the writeup `here <XXX>`_.


Features
--------

* dynamic creation of command-line options/arguments
* enables the use of all existing Ansible `modules <http://docs.ansible.com/ansible/latest/list_of_all_modules.html>`_ and `roles <https://galaxy.ansible.com/>`_
* supports task lists in Ansible format, as well as it's own internal one
* easy sharing and hosting of provisioning scripts
*

License / Documentation
-----------------------

* Free software: GNU General Public License v3
* Documentation: https://frecklecute.readthedocs.io.
