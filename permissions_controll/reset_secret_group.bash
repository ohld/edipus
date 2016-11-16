#!/bin/bash
groupdel secret
groupadd secret
chgrp secret /home/secret_docs
chmod g+wrx /home/secret_docs
chmod o-wrx /home/secret_docs
