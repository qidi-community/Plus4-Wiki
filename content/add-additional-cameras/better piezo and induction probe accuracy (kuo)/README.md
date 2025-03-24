I employ multiple strategies from the community wiki to improved the odds of accurate and repeatable z-offset and bed mesh. To those recommendations, I have added tweaks based upon days of sensor reliablity testing at various temperatures, speeds, and probing distances. An entire string of things must all happen correctly for first layer accuracy. Break any item in the accuracy chain, and the result is flawed first layer bed / nozzle positioning. My goal was to optimize the following requirements for reliable operation....

Qidi Plus 4 printers come equipped with nozzle touch and bed proxumity sensors to enable automatic z-offset, bed leveling, and per-print meshbed functionality. The user expectation is that the printer will automatically level the bed and repeatably place nozzle distance appropriate for printing. Unfortunately, the stock implementaiton is not entirely reliable. Multiple owners have reported unreliable first layers or even gouged print plate despite the advanced sensors. 

I implemented multiple firmware setting changes to improve reliability of 1st print layer placement. You can skip directly to my settings that are later in this document, but I recommend you read the next section to understand what is being adjusted and why.

Reading about the z-offset, bed tramming, and bed mesh can be confusing because we tend to re-use the same phrase for mutiple different things. For the purpose of this discussion I define the some terms to differentiate them. They may not be exactly how Klipper and the Qidi firmware implement them, but should be adequate to convey 

z-screw-position-count: This is the underlying z-screw position that Klipper tracks. It is kept by the system counting and keeping track of how many steps the motors have been moved.

z-nozzle-touch: This is the z at which the system detects nozzle touching print bed. It is the zero point of the z coordinates for printing. 

z-offset-internal: The printer has a formula determined distance that it considers the correct position for first layer when z-offset-user is zero.

z-offset-user: This is the z-offset that users set. It is in added to the z-offset-base. If you set z-offset-user to place bed 0.1 mm below nozzle, the actual bed to nozzle distance is your z-offset-user combined with z-offset-internal.

stored-Z-offset: Qidi firmware tries to store z-offset-user at the end of each print job. This feature is intended to let users manually tweak z-offset via the printer control panel and have their adjustment stored for later print jobs.

bed-mesh: This is an induction probe mapping of bed shape created by probing the print plate. The zero for these measurements is calibrated by the printer measuring induction probe reading vs z-nozzle-touch. After that calibration, all distances from nozzle to bed are done via induction probe rather than nozzle touch. 

The bed mesh measurements are used to moved the bed up/down to compensate for bed height variation. The printer attempts to keep nozzle distance equal to z-offset-internal + z-offset-user. The percent of bed mesh compensation varies with z-height. Typically, printers fade out bed compensation after several layers height printing.

As a KAMP printer, there are actually two bed meshes potentially in use. The default mesh is that saved after performing a "tune" mesh bed operation. That is the whole print bed mesh and can serve as the bed mesh when a KAMP mesh is not available. Print jobs on the Qidi Plus4 typically include a KAMP mesh measurement step wherein a more specific bed mesh of the actual print area is done. The print job then uses the KAMP mesh to do  bed mesh compensation rather than the default mesh.

Note: Because the vast majority of distance measurements are performed using the induction probe, accuracy of BOTH nozzle touch and induction probe are needed for bed mesh, bed z-tilt, and bed mesh compensation. 

NB: Induction probes (and even Beacon probes) do not measure reliably near the edges of the print plate. Also, probe offset and mechanical limits mean the printer can never actually take measurements of bed mesh all the way out to print bed edges. Therefore, bed mesh may be dramatically wrong when printing is at extreme edge of bed.


Problems on the Qidi Plus 4:

a: Piezo bed sensors at incorrect pre-tension: Nozzle touch sensing becomes unreliable at low PLA bed temperatures, and increasingly worse at high bed temperatures.

b: Piezo bed sensor mechanically damaged or poorly built: Piezo sensor discs are bonded to their brackets using glue. There are reports of a batch of sensor discs having weakened glue that deteriorates at high temperatures. Also, hard impacts to print bed can overstress mounting glue for the sensor discs. The majority of piezo sensor are okay, but if they break, z-nozzle-touch may not be detected. As a result, the user sees x-carriage lifted during nozzle touch and subsequently suffer a gouged print plate because z-nozzle-touch was incorrectly detected too high (too late). Once piezo sensors fail, they need to be replaced or possibly repaired via re-bonding.

c: Bed downward mechanical stop is uneven without leveling blocks due to shape of platform bottom: Letting the printer lower bed to bottom, without leveling blocks, does not repeatably bottom out the z screws in same position. Leveling blocks must be used. These should be exactly the same height give SOLID stops for both left and right z-screws. 

d: Z-stepper motor microstepping and driver interpolation settings in firmware 1.6.0 may cause a Klipper issue with accuratetly counting and tracking z position.

e: Induction probe accuracy and reliability are not fully optimized in firmware 1.6.0. The firmware settings for probing distance and speed fail to work properly with some induction probes. The default 5 mm distance and 5 mm/sec speed works for most induciton probes, but for some units the distance, especially, is too short. The bed must move far enough to be reliably out of hysteresis range of the induction probe. My measurements suggest that at least 6.5 mm probing distance is needed to be compatible with probes that trigger at a longer distance.

f: Stored-Z-offset unpredictably changes. Users report stored z-offset can mysteriously become zero and seem to stack up over a series of prints.



What I Did (After Removing Packing Materials)

1. Download and install firmware 1.6.0. Everything I did is with firmware 1.6.0


2. Set Piezo Sensors to Reasonble Pre-tension
Before doing any bed leveling, set bed screw knobs to position the bottom of the plastic knobs to 9-10 mm away from bottom of metal bed plate above. If your printer has just the locking nut (no lock washer), that leaves about three threads visible below lock nut. Once at this position, lock the front left screw in place and do bed leveling ONLY with the other three screws. That should keep you in good pre-tension range for the piezos.



3&4 Preamble: For background, see Better Bed Meshing, but note that I do NOT do everything identically to the wiki https://github.com/qidi-community/Plus4-Wiki/blob/main/content/more-accurate-bed-meshing/README.md


3. Z /Z1Stepper and Driver Settings for Better Kiipper Z tracking
Follow the instructions the wiki to set in sections...
 
[stepper_z] and [stepper_z1]  Microsteps: 16

Also follow the instructions there to set in sections...

[tmc2209 stepper_z] and [tmc2209 stepper_z1] interpolate FALSE

4. Induction Probing Distance and Speed
My testing at multiple bed temperatures, probing speeds, and distances demonstrates that the firmware 1.6.0 speed and distance are not optimal. Probing distances of 6.5 mm or greater has fewer pre-triggered sensor errors. Probing speed is less critical and can be faster than the stock 5 mm/sec.
My settings for [smart_effector] and [bed_mesh] are below. I have commented my changes.
Be careful of spaces. There must be a spaces after the number and before ;comment

[smart_effector]
pin:U_1:PC1
recovery_time:0
x_offset: 25
y_offset: 1.3
z_offset: 0.000001
speed: 6 ;faster probing speed
lift_speed:18 ;faster drop away from probe
probe_accel:50
samples: 1 ;leave this at two until you verify probe is reliable
samples_result: submaxmin
sample_retract_dist: 7 ;probing distance
samples_tolerance: 0.025 ;no greater than this for tolerance
samples_tolerance_retries:5

[bed_mesh]
speed: 600 ;faster xy move between sample locations
horizontal_move_z: 7 ;probing distance
mesh_min:25,10
mesh_max:295,295
probe_count:9,9
algorithm:bicubic
bicubic_tension:0.4
mesh_pps: 2,2



5. Leveling Blocks:
Use whatever whatever SOLID, same height objects you have for initial setup, but
once you have permanent leveling blocks installed, redo your bed screws adjust and "tune" for bed mesh.

Permanent z-leveling blocks by Stew675 is a convenient design. They can be left in place permanently with minimal loss in max vertical printing height. https://www.printables.com/model/1212350-permanent-bed-platform-levelling-blocks-for-the-qi





6. Screws_Tilt_Calculate / Bed Left/Right Tramming
Now that we have the Piezo and induction probes optimized by our [smart_effector] and [bed_mesh] changes, we can use the probes to help with bed leveling.

I perform Screws_Tilt_Calculate (and bed meshes) with print bed at 90C because that is my most common print material PETG uses. If you typically print hotter, consider doing the adjust and bed mesh at the elevated bed temp. Doing this at room temp gives a different result than when performed at printing temperature.

NOTE: We already set left front screw to known good piezo pre-tension. LEAVE THAT LEFT FRONT SCREW ALONE and it will tend to leave the other three at also reasonable positions. Be leary of big adjustments tightening the adjustment knobs.

Do the steps in https://github.com/qidi-community/Plus4-Wiki/tree/main/content/Screws-Tilt-Adjust to enable Screws_Tilt_Calculate. This is faster than working with paper or feeler gauges. 





7. Make z-offset-user and stored z_offset permanently zero
I make these permanently zero to avoid the bug that unpredictably changes z-offset.
In the next step, I store z-offset-internal explicity for each printer. That lets me permanently and reliably know what the printer is using for actual distance between bed and nozzle for first layer.

See wiki Making Z_offset Permanent for background understanding, but do NOT do the changes presented there. I only follow the instructions for disabling storage of z_offset and for making it zero in saved_variables. 

Do not mess with smart_effector as described in the wiki.
https://github.com/qidi-community/Plus4-Wiki/tree/main/content/making-z-offset-permanent

In Saved_variables.cfg 

Nake sure that the stored z_offset is zero.

z_offset = 0


Next, prevent automatic storage of z_offset

Open gcode_macro.cfg

We disable storage of z_offset from PRINT_END and safe_zoffset by commenting out three lines in each of two macros.


[gcode_macro PRINT_END]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}



[gcode_macro save_zoffset]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}



8. Set Desired Z-offset for 1st Layer.
I set desired distance between bed and nozzle directly in the formulat that specifies z-offset-internal

Notice the formula....
    {% set p=(-0.15 + printer.gcode_move.homing_origin.z)|float %}

The -0.15 means the bed should be placed 0.15 mm below z_nozzle_touch for first print layer.

-0.10 would be closer to nozzle
-0.20 would be farther away from nozzle

Higher temps tend to make induction probes trigger at a shorter distance. So consider going more towards -0.20 if printing is going to be with high temp filaments. You will need to experiment to find your best offset. One way is to manually tweak z-0ffset while printing and adding that change to your formula value.

Each of my printers does best with a slightly different z-offset. It is between -0.12 and -0.15 for my four Plus4 printers.





[gcode_macro get_zoffset]
gcode:
    TOGGLE_CHAMBER_FAN
    G1 Z10 F600
    Z_VIBRATE
    QIDI_PROBE_PIN_1
    m204 S50
    G4 P500
    probe probe_speed=6 lift_speed=18 samples=5 sample_retract_dist=10
    move_subzoffset
    M114
    {% set p=(-0.15 + printer.gcode_move.homing_origin.z)|float %} ;typically -0.12 to -0.15 works well for my printers
    SET_KINEMATIC_POSITION Z={p}
    G1 Z30 F600
    QIDI_PROBE_PIN_2
    m204 S10000
    TOGGLE_CHAMBER_FAN



Save and Restart for changs to take place.


This concludes the changes I made for better piezo and induction probe performance.
