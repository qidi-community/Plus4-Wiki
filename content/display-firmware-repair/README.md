# So you borked your touchscreen...

If a firmware update went sideways, or the screen just spontaneously decided to die, and now the screen is plain white with "DATA ERROR" in red text on it, or similar, you can fix it with a couple simple steps and a usb flash drive. 

### Step-by-step
1) Get a usb drive that is usable with the printer. One formatted into FAT32 will do, size largely doesn't matter. Usb drive that came with the printer was used in testing.
2) Find out, remember, or guess what printer firmware version you had. Example numbers are 1.3.2, 1.4.3, 1.6.0.
3) Download the firmware update for that version, so if you had 1.6.0 installed, get a 1.6.0 update file. You may also reuse one you already downloaded before.
4) Unpack it, and find a file named `QD_Plus4_UI`, rename it to `mksscreen.recovery`, all lowercase exactly as it's written.
5) Put the now renamed `mksscreen.recovery` file in the "root" of the flashdrive (not into any kind of folder, right onto the flash drive).
6) Turn off the printer (flip the power switch) and wait for 30 seconds.
7) Plug the usb drive you just prepared into the printer, and turn it on. 
8) Sit back and relax for an hour while the printer flashes the screen firmware.
9) Once the printer screen reboots and starts working normally, remove the usb flash drive and delete the `mksscreen.recovery` file from it so the printer won't repeat the flashing process every startup.

### Possible problems encountered: 
#### Issue 1: The printer went back to "DATA ERROR!" screen
Repeat the process from step 6. 
#### Issue 2: The printer displays a qidi UI saying update succeeded, but then complaints about a firmware version mismatch. 
Note down the "SOC: XXXXX" number in the bottom right of the error, this is the version the printer thinks it has. You made a mistake in step 2 and need to find a different update file.
#### Issue 3: The screen says UPDATE FAILED in small red text on white background
The screen is possibly lying. Temporarily remove the usb flash drive and restart the printer at the power plug. It may go to issue number 1 mentioned above.
###4 Issue 4 and later: ??????
If you find more, please open an issue on the project (tab in the github interface), and describe what you're having and steps you've taken. Attach a picture if possible.

