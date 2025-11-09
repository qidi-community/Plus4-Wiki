# Securing SSH Access

> [!CAUTION]
> FOLLOWING THESE INSTRUCTIONS HAVE THE POTENTIAL TO PERMANENTLY LOCK YOU OUT OF `ssh` ACCESS. PLEASE FOLLOW ALL INSTRUCTIONS CAREFULLY, NOTE DOWN ALL PASSWORDS, AND BACKUP ANY PRIVATE/PUBLIC KEYS AS APPLICABLE.
>
> If you become locked out due to losing access to your password or public/private key-pairs, the only way to restore access would be to perform a factory result with fresh firmware from QIDI and there is no known way to regain access. Only proceed if you can understand and can bear or mitigate the potential risks involved.

By default, the QIDI Plus4 ships with an insecure SSH configuration, allowing simple password access to both the `root` and `mks` accounts. More details on gaining SSH access can be found [here](../ssh-access/README.md).

As such, any bad actor on your local network or with access to the printer's SSH port is able to gain trivial access with full control, allowing for remote code execution, installation of malware, modifying Klipper configs, etc. As such, it's important to secure SSH access to the printer through:

- Changing default passwords [High Importance]
- Disabling root login [High Importance]
- Setting up public/private key authentication [Moderate Importance]
- Disabling password-based SSH login [Moderate Importance]
- Ensuring local-only SSH access through router/network/firewall configuration [Low Importance - Out of Scope]

It is recommended to perform the first four steps in conjunction, as they involve minimal edits to a single file and vastly improve security of your machine.

## Change Default Passwords

The default password for both `root` and `mks` accounts on the Plus4 is `makerbase`. This should be changed for the `mks` password as soon as practicable if the printer is on the network. 

### Prerequisites
- The IP Address of the printer (obtained through the Printer network screen or your router)
- Ability to SSH (WSL on Windows, Terminal on MacOS / Linux)

### Process

SSH into your printer's `mks` account:

```
ssh mks@<ip-address>
```

Type `passwd` to change the password of the `mks` account. It's recommended to use a complex password here, as the `mks` account can gain privileged access through this password.

If you want to keep `root` login, then it is recommended to change the `root` account password too. You can gain `root` account access from the `mks` account with the below command:

```
sudo -i
```

You will be prompted to type the new password that you just set. Then, run `passwd` as the `root` user to change the `root` password. Ideally, it should be different from the `mks` password to prevent simultaneous compromise, though such risks are low. 

## Disabling Root Login

It is recommended to disable the ability to log into the printer as the `root` user, which has superuser privileges. Instead, all SSH logins should be done through a normal user account, and then escalated to `root` with `sudo` as needed. This helps to reduce one potential vector of compromise. 

### Prerequisites
- The IP Address of the printer (obtained through the Printer network screen or your router)
- Ability to SSH (WSL on Windows, Terminal on MacOS / Linux)
- Use of `nano`, `vim,` or `vi` text editor in the command line

### Process

SSH into your printer's `mks` account.

Edit the file found at `/etc/ssh/sshd_config` with `sudo` privileges:

```
sudo nano /etc/ssh/sshd_config
```

Find the line beginning with `PermitRootLogin` and change "on" to "off". Your end result should look like the below. Mine was found on line 32.

```
PermitRootLogin off
```

Save and exit. Restart the `ssh` daemon with:

```
sudo systemctl restart ssh
```

## Set up Private / Public Key Authentication

Traditionally, SSH authentication is handled with user account passwords. However, passwords can be easily stolen, guessed, or phished and are therefore a less secure means of authentication. Instead, SSH has support for public/private key authentication, whereby a machine generates a key-pair, and the public key of such keypair is shared with the server, and the private key is kept hidden locally. Since these public/private keys are kept cryptographically secure and the private key does not leave your machine in any situation, this is a more resilient form of authentication.

Further details on public/private key authentication is out of scope and can be found [here](https://en.wikipedia.org/wiki/Public-key_cryptography)

As such, it's recommended to enable public/private key authentication to SSH into the printer as opposed to the password-based authentication. You also no longer need to type in your password when SSHing in.

### Prerequisites
- An SSH key-pair has been generated on your computer
  - The exact process varies between OS. Some basic guides are linked below.
    - [WSL/Windows](https://www.howtogeek.com/762863/how-to-generate-ssh-keys-in-windows-10-and-windows-11/)
    - [MacOS/Linux](https://devopscube.com/generate-ssh-key-pair/)
- The IP Address of the printer (obtained through the Printer network screen or your router)
- Ability to SSH (WSL on Windows, Terminal on MacOS / Linux)
- (Optional) The `ssh-copy-id` command **or** a command line text editor (nano / vi / vim)

### Process

There are two options to install the SSH key: (i) automatically with the `ssh-copy-id` command or (ii) manually. If you have the `ssh-copy-id` command in your local computer's command line, it is recommended to use that as it greatly simplifies the process. You can also copy the key manually if preferred, but offers no functional benefits. Most machines will have the `ssh-copy-id` command.

#### Automatic Installation

Once you have generated your SSH key-pair or if you are using an existing SSH key-pair, you will need to copy the ***public*** key of the key-pair onto your printer. ***DO NOT*** under any circumstance, allow your ***private*** key to leave your machine. That is equivalent of a password and should be treated as such. 

Copy the public key to the printer with the following command:

```
ssh-copy-id mks@<ip-address>
```

You will be prompted from the password for the `mks` account. This will install the public key automatically into the `mks` account. You should now be able to `ssh` into the `mks` account without needing to input a password.

#### Manual Installation

If your machine does not have the `ssh-copy-id` command, you will need to copy the key manually. First of all, find the ***public*** key that you generated. Copy the entirety of the public key file. You will need to paste that in a later step.

SSH into your printer:

```
ssh mks@<ip-address>
```

Edit the file found at `~/.ssh/authorized_keys`. This is the listing of all SSH public keys which are allowed to access the printer. You do not need superuser privilege to edit this file.

```
nano ~/.ssh/authorized_keys
```

Paste in the ***public*** key that you copied earlier. You have now installed the SSH public key and you should be able to `ssh` into the `mks` account without needing to input a password.

## Disable Password Authentication

If you are using private / public key authentication with your printer and do not need password authentication, it is recommended that you disable the ability to SSH into the printer with a password. This vastly improves security, particularly if your password is less complex, reused, or easy to guess. While a strong password mitigates the risk significantly, it is still recommended to remove SSH password access to reduce the attack surface. 

### Prerequisites
- The IP Address of the printer (obtained through the Printer network screen or your router)
- Ability to SSH (WSL on Windows, Terminal on MacOS / Linux)
- SSH private / public key authentication set up and working
- Use of `nano`, `vim,` or `vi` text editor in the command line

#### Warning!!!

If you disable password authentication, you will not be able to SSH into your printer except with the private / public key(s) you have set up. Please be mindful that if you lose your private / public key access, you will not be able to SSH into the printer at all, and will need to undergo a complete factory reset. QIDI will not be able to recover access for you, and there is no (known) way to bypass this. Before doing this, it is recommended you have at least two devices with different SSH key-pairs set up for access, in case you lose your primary device.

### Process

SSH into your printer:

```
ssh mks@<ip-address>
```

Edit the file found at `/etc/ssh/sshd_config` with `sudo` privileges:

```
sudo nano /etc/ssh/sshd_config
```

Make the following changes to these SSH parameters within the file:

```
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM no
```

`ChallengeResponseAuthentication` may already be set to `no`. If so, no changes to that line are needed.

Save and exit. Restart the `ssh` daemon with:

```
sudo systemctl restart ssh
```


Password login should now be disabled for the printer, and you must login with one of the existing private / public key pairs.
