Obtain a shell on your printer and run the following commands

```
sudo wget -O - https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/system-tuning/tuning > /etc/init.d/tuning
sudo chmod 755 /etc/init.d/tuning
sudo ln -sf /etc/init.d/tuning /etc/rc3.d/S99tuning
sudo /etc/init.d/tuning reload
```
