Obtain a root shell on your printer like so:

```
sudo bash
```

Now run the following commands:

```
wget -O - https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/system-tuning/tuning > /etc/init.d/tuning
chmod 755 /etc/init.d/tuning
ln -sf /etc/init.d/tuning /etc/rc3.d/S99tuning
/etc/init.d/tuning reload
```

Now exit out of the root shell like so with the following command:

```
exit
```
