Qidi Plus 4 is shipped with a single, built-in camera, but is also capable of displaying multiple USB cameras. This can be accomplished using just the Fluidd GUI. No SSH into printer, nor installation of additional software is needed.
<img src="./fluidd%20with%20multiple%20cameras.jpg">

Pre-requisets: Have all your USB cameras connected to printer and Fluidd interface showing in a browser.

There are three main steps for adding a USB camera

1. Gather required USB device filepath for each connected camera. The filepaths are used to specify which camera is streamed in next step

2. Create a video streamer for each camera. This is done by defining 1st camera in webcam.txt, 2nd camera in webcam2.txt, 3rd camera in webcam3.txt.

3. Add each video streams as a cameras in Fluidd.

========
Gathering USB camera fileptahs


