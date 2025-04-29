# Disabling the QIDI Link client

## Introduction

The Qidi Plus 4 install has got a similar feature as Bambu Handy, called the [Qidi Link](https://wiki.qidi3d.com/en/app) client, setting it up through the cloud but it's just a compiled binary in the home-directory of root, being called by a bash script at boot. No packaging, just base image... 
On an OS, using nginx, which is deemed "End of Life" (EOL) since 2022.

The security implications are severe, but potentially unfounded. [This comment](https://www.reddit.com/r/3Dprinting/comments/1g91nq9/comment/ltxrq06) on reddit states:

> Enabling Q link associates your printer with an unencrypted publicly accessible url at aws. On top of that, the app barely works to begin with.
>
> If you enable it, anybody on the internet can control your printer if they know the url.
>
> I immediately turned it off and unlinked my x max 3.

## Disable and dismantle service

To turn this off fully, and erradicate it at the root, follow these steps:

1. ssh into your 3D Printer's Linux command shell (see [ssh-access](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/ssh-access) for details)
1. access the root account
    - `sudo -i`
    - log on with mks account password (which you used to enter with SSH).
1. stop and disable the QIDI Link client
    - run the command `systemctl stop QIDILink-client`
    - run the command `systemctl disable --now QIDILink-client`
1. move the data directory
    - run the command `cd /root`
    - run the command `mv 'QIDILink-client' 'QIDILink-client-DoNotTouch'`
1. stop the startup script from running it (ie. comment out a line)
    - run the command `sed -i 's!^\/root\/QIDILink\-client\/udp_server!\#\/root\/QIDILink\-client\/udp_server!' /root/xindi/build/start.sh`
      
      ![image](https://github.com/user-attachments/assets/b09a4d9d-19f7-44df-9789-5024ed48cae8)
1. Disable the systemd service
    - run the command `cd /etc/systemd/system`
    - run the command `mv -v QIDILink-client.service{,.masked}`
    - run the command `systemctl mask QIDILink-client`

      You should now have 2 files in that location, where the "right" one (in the eyes of the OS, called `QIDILink-client.service`) is actually pointing towards the big black hole called `/dev/null`.
      ![image](https://github.com/user-attachments/assets/49fff9cd-b761-41e0-bf94-2653b8074d5a)

## Restart the Printer

The files we've just edited are not necessarily written to disk yet. 
To force this to happen, run the command `sync`. If that comes back with no further remarks and an exitcode of `0`, you can powercycle the printer.

![image](https://github.com/user-attachments/assets/fde60fab-cb96-482a-aad2-c40e5a41a9f3)
