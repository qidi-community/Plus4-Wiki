# How to access your Plus 4 through SSH

SSH access is needed to interact with the Klipper configuration system. You will specifically need to SSH into your printer to add Klipper extensions.

To log into your printer, first detrmine it's IP address from the front panel's network tab.

Then open a shell (or Terminal on Windows) and type:

```ssh mks@x.x.x.x``` 

Where x.x.x.x is the IP address.

The password is **makerbase**

Common config files are in /home/mks/printer_data/config

You can also use popular FTP client filezilla, with Host sftp://IP_ADDRESS (user and pass as above) , then right click a file, choose View/Edit, when you save, go back to filezilla and it will ask if you want to re-upload changes.
