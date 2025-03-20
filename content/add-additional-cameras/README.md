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



===================================

Gathering USB camera fileptahs

Click on the System icon within Fluidd to bring up Fluidd's "system information" page
<img src="./system%20icon.jpg">


Click on USB device icon. It is shaped like the USB device symbol. This will bring up the USB devices panel
<img src="./devices%20icon.jpg">

Once at the USB device panel, select "video" then click on refresh icon to get currently connected USB video device info.
<img src="./devices%20panel.jpg">


You now are looking at info about your USB video devices (cameras). The filepaths for each camera are shown here. This is the information other instructions have users obtain via SSH and command line. As you see, this info is available via Fluidd GUI.
<img src="./usb%20filepaths.jpg">

Copy down a unique filepath for each camera. Get the entire filepath starting with "/dev" 
You should obtain one filepath for each camera. It is easiest if you paste your fielpaths into a file for use in phase 2, creating the video streams.

If all your cameras are different models (no identical cameras), copy the path_by_id path. Path_by_id doesn't change if you alter which USB port a camera is connected.

If you have more than one camera of the same make/model, they will have identical path_by_id. In that case, copy the path_by_hardware which will be unnique to each camera, but could change if you change where you plug in your cameras.

===================================

Create Video Streamers

We will create one webcam txt file for each camera. There is already webcam.txt in your fluid configuration files for the stock camera. 

webcam.txt <- 1st camera
webcam2.txt <- 2nd camera
webcam3.txt <- 3rd camera

--- webcam.txt
You will need to edit two lines in webcam.txt.

line 24 should be uncommented and editied to specify camera fielpath
It will becomes like below. Of course, use YOUR filepath for first camera rather than the one in below example.

24 camera_usb_options="-r 1920x1080 -f 10 -d /dev/v4l/by-id/usb-SYX-231020-J_HD_Camera-video-index0"

line 72 should be uncommented and edited to specify port 8080
72 camera_http_options="-n -p 8080"

Select All and COPY to clipboard (We will be reusing nearly all the same info for next camera streamer)

Save and Close to write our your edits to webcam.txt

--- webcam2.txt
Have fluid create a new webcam2.txt file. It will be empty.
Paste the previously copied webcam.txt contents into webcam2.txt

Again we need to chagne two lines.

Line 24 gets the filepath for your next camera. It will be like....

24 camera_usb_options="-r 1920x1080 -f 10 -d /dev/v4l/by-id/usb-UnionImage_Co._Ltd_CCX2F3298_1234567890-video-index0"

Line 72 specifies next port (8081)

72 camera_http_options="-n -p 8081"

Save and Close to write our your edits to webcam2.txt

--- webcam3.text
Do same for creating webcam3 if you have yet another camera.
In example below, we'll use the by_hardware id so you know how that would look.

24 camera_usb_options="-r 1920x1080 -f 10 -d /dev/v4l/by-path/platform-ff5c0000.usb-usb-0:1.2:1.0-video-index0"

Line 72 would specify next port (8082)

72 camera_http_options="-n -p 8082"

Save and Close to write our your edits to webcam3.txt

---
Activate newly definite video streams.
Restart webcamd service to apply your newly definied streamers.



=====================
Add cameras to Fluidd















