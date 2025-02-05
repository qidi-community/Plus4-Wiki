# Secure Remote Access

## Overview
Instead of using qidi link to access your printer, this guide servces to help you 
setup a VPN mesh network that allows you to access your printer using various klipper
apps for mobile devices using your trusted network as opposed to using Qidi's. 

## Prerequisites
* Comfortable with SSH access to your printer and executing commands
* Have an free tailscale account - https://tailscale.com/signup/

## 1. Setup Tailscale VPN Account
Follow the onboarding guidelines from tailscale to create and register your first device, preferabbly your phone since you are replacing qidi link! Instructions are [here](https://tailscale.com/kb/1017/install). Once you see your phone listed in the devices, move on to the next step!

## 2. Disable qidi link
Since we don't need this service running anymore, let's scavange back those resources! SSH to your printer and then we will disable the qidi link service with the following command:

```
sudo systemctl disable --now QIDILink-client.service
```

This command will stop the service and also disable it from starting up! 

## 3. Install Tailscale VPN On The Printer
Following the documentation from tailscale [here](https://tailscale.com/kb/1041/install-debian-buster), we will install the tailscale client on the printer with the following command:

```
# package signing ketys
curl -fsSL https://pkgs.tailscale.com/stable/debian/buster.gpg | sudo apt-key add -
curl -fsSL https://pkgs.tailscale.com/stable/debian/buster.list | sudo tee /etc/apt/sources.list.d/tailscale.list

# install packages
sudo apt-get update
sudo apt-get install tailscale

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
Using the app store on your device, install a klipper client. There are multiple options available on apple with no preferential treatment over the other. Try them and find one you like!  The important bit here is it'll prompt your for an address for your printer. We'll use the IP address or MagicDNS name associated with your printer in this field. That should be all you need to connect your printer! You can test remote access by disabling wifi on your mobile device and opening the klipper app you downloaded and reviewing your printer! Congratulations, you are now using a private network to access your device! Pictured is the UI from the iOS app MobileRaker. 

![IMG_5422.PNG](./IMG_5422.PNG "Yay, Security!")

## Closing Pointers
While not required, it can be convenient to disable key expiration on the printer. This obviously has security trade offs, but nothing especially critical with all things considered. This will ensure your printer is available all the time instead of having to periodically log in to tailscale from the printer periodically.

