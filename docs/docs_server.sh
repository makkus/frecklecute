#!/usr/bin/env bash

sphinx-apidoc -f -o docs/source/ frecklecute
sphinx-autobuild -H 0.0.0.0 -p 7072 docs build/html
