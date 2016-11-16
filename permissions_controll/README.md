# permissions' controll model
### (for Linux)

### What does it do:
Access to `/home/secret_docs` only for users with 'secret' group.

### How to use it:
1. open terminal 
2. switch to a root user:
```
sudo su root
```
3. create `/home/common/` directory and give it all permissions:
```
mkdir /home/common
chmod a+wrx /home/common
```
4. add 2 strings to `/etc/rc.local` file:
```
/home/reset_secret_group.bash
/home/give_permissions &
```
This script runs automatically on every boot of the system.
Fist one resets 'secret' group: delete all users from it.
Second one starts daemon process on the background of the ststem. This daemon adds users to the group 'secret'
5. create a group 'secret':
```
groupadd secret
```
6. create secret directory under 'secret' group and restrinc access to it:
```
mkdir /home/secret_docs
chgrp secret /home/secret_docs
chmod a-wrx, /home/secret_docs
chmod ug=wrx /home/secret_docs
```

Now any user will be able to get into `/home/secret_docs` directory only after running `checkpass` binary with a right password.
Password is 'edipus':
```
bin/checkpass edipus
access has been granted
```
To apply changing in the group user needs to log out and log in again.
Access should be renewed after every reboot.

### How to use it with EDIPUS:
The script which anlyses faces should do exactly the same as `checkpass` binary instead of it.
And 'if' condition should check a face, not a password.
