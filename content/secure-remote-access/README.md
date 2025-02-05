# Secure Remote Access

## Overview
Instead of using Qidi Link to access your printer, this guide serves to help you
set up a VPN mesh network that allows you to access your printer using various Klipper
apps for mobile devices, using your trusted network as opposed to Qidi's.

## Prerequisites
Comfortable with SSH access to your printer and executing commands
Have a free Tailscale account - https://login.tailscale.com/start

## 1. Setup Tailscale VPN Account
Follow the onboarding guidelines from Tailscale to create and register your first device, preferably your phone since you are replacing Qidi Link! Instructions are [here](https://tailscale.com/kb/1017/install). Once you see your phone listed in the devices, move on to the next step!

## 2. Disable qidi link
Since we don't need this service running anymore, let's scavenge back those resources! SSH into your printer, then disable the Qidi Link service with the following command:

```
sudo systemctl disable --now QIDILink-client.service
```

This command will stop the service and also disable it from starting up! 

## 3. Install Tailscale VPN On The Printer
Following the documentation from tailscale [here](https://tailscale.com/kb/1041/install-debian-buster), install the tailscale client on the printer with the following command:

```
# package signing keys
curl -fsSL https://pkgs.tailscale.com/stable/debian/buster.gpg | sudo apt-key add -
curl -fsSL https://pkgs.tailscale.com/stable/debian/buster.list | sudo tee /etc/apt/sources.list.d/tailscale.list

# install packages
sudo apt-get update
sudo apt-get install tailscale -y

# Start tailscale, show a QR code to add it, and enable ssh!
sudo tailscale up --qr --ssh
```
THe last command will start tailscale and give you a QR code to scan with your mobile device to easily add it to your account activate it. It also enables ssh communication to your device from your trusted devices on tailscale vpn. This is pretty neat so you can access your printer's CLI from anywhere securely without opening up your firewall! 

Last thing to do is to enable the tailscale service once you've registered the device to your account.

```
sudo systemctl enable --now tailscaled
```

Once you confirm that you see your printer associated and live with your tailscale account, proceed to the next step!

## 4. Install a mobile klipper client
Using your device's app store, install a Klipper client. There are multiple options available on Apple devices, with no preferential treatment for any particular one. Try them out and find one you like! The important part is that the app will prompt you for an address for your printer. Enter the IP address or MagicDNS name associated with your printer in this field. That should be all you need to connect your printer!

You can test remote access by disabling Wi-Fi on your mobile device and opening the Klipper app you downloaded to check your printer. Congratulations! You are now using a private network to access your device!

Pictured below is the UI from the iOS app MobileRaker:

![IMG_5422.PNG](./IMG_5422.PNG "Yay, Security!")

## Closing Pointers
While not required, it can be convenient to disable key expiration on the printer. This obviously has security trade-offs, but nothing especially critical, all things considered. Disabling key expiration ensures your printer remains accessible without requiring you to periodically log in to Tailscale from the printer. You can disable key expiration from the Tailscale UI when selecting the printer from your list of hosts.
