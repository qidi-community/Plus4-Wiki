Qidi Plus 4 is shipped with a single, built-in camera, but is also capable of displaying multiple USB cameras. This can be accomplished using just the Fluidd GUI. No SSH into printer, nor installation of additional software is needed.
<img src="./fluidd%20with%20multiple%20cameras.jpg">

Pre-requisites: 
b) Have all your USB cameras connected to printer and Fluidd interface showing in a browser. 
a) Know the IP address of your printer. 
c) Your printer has a static IP address, and never changes its IP address upon startup.

There are three main phases for adding a USB camera

1. Gather required USB device filepath for each connected camera. The filepaths are used to specify which camera is streamed in next step

2. Create a video streamer for each camera. This is done by defining 1st camera in webcam.txt, 2nd camera in webcam2.txt, 3rd camera in webcam3.txt.

3. Add each video streams as a cameras in Fluidd.

========
Gathering USB camera fileptahs

<img src="./system%20icon.jpg">
Click on the System icon within Fluidd to bring up Fluidd's "system information" page

<img src="./devices%20icon.jpg">
Click on USB device icon. It is shaped like the USB device symbol. This will bring up the USB devices panel

<img src="./devices%20panel.jpg">
Once at the USB device panel, select "video" then click on refresh icon to get currently connected USB video device info.

<img src="./usb%20filepaths.jpg">
You now are looking at info about your USB video devices (cameras). The filepaths for each camera are shown here. This is the information other instructions have users obtain via SSH and command line. As you can see, the same info is available via Fluidd GUI.

Copy down a unique filepath for each camera. You should copy down one filepath for each camera. It is easiest if you paste the fielpaths into a file for later reference.

If you have all different model cameras (no identical model cameras), copy the path_by_id path. Path_by_id doesn't change if you alter which USB port a camera is connected.

If you have more than one camera of the same make/model, they may have identical path_by_id. In that case, copy the path_by_hardware which will be unnique to each camera, but could change if you change where you plug in your cameras.

