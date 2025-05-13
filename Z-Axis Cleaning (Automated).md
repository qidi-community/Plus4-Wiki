
# Scrubaxy: Automated Z-Axis Lead Screw Cleaner for Qidi Plus 4

**TLDR:** Scrubaxy is a 2 -part 3D-printed tool for cleaning your Qidi Plus 4's Z-axis lead screws. It clamps onto the screw, uses IPA and a cloth to remove grime, and has relief cuts to keep buildup in the tool and not to spread it around. A custom G-code automates the cleaning process with a "bounce" method and audible notifications.

## Introduction

This project introduces 'Scrubaxi' a tool inspired by the 'Rod Sloth' for efficient cleaning of Z-axis lead screws on 3D printers, specifically the trapezoidal left-hand thread T10 screw found on the Qidi Plus 4.

## Tool Design

'Scrubaxi' employs a clamp mechanism with an internal M10 thread, featuring relief cuts to accommodate debris without spreading the tool and compromising its clamping ability. It houses a user-replaceable cloth saturated with isopropyl alcohol. The included insert allows for slow drainage of IPA directly onto the lead screw, ensuring the cloth remains damp throughout the process.

## Cleaning Process

The cleaning process is analogous to deburring a hole with a tap and die, using a 'bounce' method where the printer bed moves 10mm upwards to clean, then retracts 5mm downwards, repeating this 50 times. This ensures thorough removal of accumulated grease and debris, even heavily contaminated grease as observed after only 40 hours of printing. The tool is designed for ease of use, with a complete cleaning cycle, including three full passes of the lead screw, taking place within a single G-code sequence. This project aims to simplify 3D printer maintenance and improve the longevity of lead screw components. 'Scrubaxy' has been lengthened to provide better stability and its handle is designed to fit flush against the vertical guide rails, minimizing unwanted movement.

## G-code and Automation

A custom G-code has been created for the Qidi Plus 4 to automate the cleaning process. This G-code utilizes four macro modules: 'Z Rod Clean' for initial setup and instructions, 'Exit Z Clean' for final reports, and 'Z Proc' and 'Z Proc 2' to control the automated cleaning process. 'Z Proc 2' executes the 'bounce' cleaning method, running the bed through 50 controlled reciprocating movements, and repeats this cycle three times to ensure thorough cleaning. The macros include audible notifications to indicate when user input is required or when a process is complete. 'Exit Z Clean' plays a single long tone upon completion, 'Z Proc' plays a single short beep when waiting for tool installation and two short beeps when starting, and 'Z Proc 2' plays four short beeps upon completion.

```
#   MRBEAN.CROM'S ZCLEAN MACRO (QIDI P4): 
#   YOU WILL NEED ALL 4 MACROS BELOW and insert into gcode_macro.cfg
#   CALL THE MACRO WITH z_rod_clean
#   z_rod_clean
#   _exitzclean
#   _zproc
#   _zproc2
[gcode_macro z_rod_clean]
gcode:
#   Generates pop-up to verify z cleaning tools are not already fitted
    RESPOND TYPE=command MSG="action:prompt_begin !!! CAUTION !!!"
    RESPOND TYPE=command MSG="action:prompt_text MACHINE IS ABOUT TO HOME"
    RESPOND TYPE=command MSG="action:prompt_text ENSURE Z-AXIS TOOLS ARE NOT IN THE MACHINE"
    RESPOND TYPE=command MSG="action:prompt_text !!! MACHINE DAMAGE MAY OCCUR IF TOOLS ARE CURRENTLY INSTALLED !!!"
    RESPOND TYPE=command MSG="action:prompt_footer_button NO TOOLS INSTALLED - OK TO PROCEED|_zproc|warning|RESPOND TYPE=command MSG=action:prompt_end"
    RESPOND TYPE=command MSG="action:prompt_footer_button EXIT|_exitzclean|error|RESPOND TYPE=command MSG=action:prompt_end"
    RESPOND TYPE=command MSG="action:prompt_show"

[gcode_macro _exitzclean]
gcode:
#   Generates pop-up to verify process has been aborted with long audible tone
    RESPOND TYPE=command MSG="action:prompt_begin CONFIRM"
    RESPOND TYPE=command MSG="action:prompt_text CLEAN CYCLE REPORT:"
    RESPOND TYPE=command MSG="action:prompt_text "
    #{% if (printer.gcode_move.position.z ) < 35 %}
    {% if (printer['fan_generic cooling_fan'].speed) > 0.005 %}
    RESPOND TYPE=command MSG="action:prompt_text {printer['fan_generic cooling_fan'].speed * 255} CYCLES COMPLETED OF 3 EXPECTED WITH A TOTAL OF"
    RESPOND TYPE=command MSG="action:prompt_text "
    RESPOND TYPE=command MSG="action:prompt_text {printer['fan_generic cooling_fan'].speed * 26520} Z MOVEMENTS COMPLETED AND {printer['fan_generic cooling_fan'].speed * 2403715}MM OF THREAD ENGAGEMENT CLEANED"
    {% else %}
    RESPOND TYPE=command MSG="action:prompt_text NO REPORT TO PROVIDE AS"
    RESPOND TYPE=command MSG="action:prompt_text {printer['fan_generic cooling_fan'].speed * 255} CYCLES COMPLETED OF 3 EXPECTED"
    {% endif %}
    RESPOND TYPE=command MSG="action:prompt_text "
    RESPOND TYPE=command MSG="action:prompt_text ONCE FINAL HOMING HAS COMPLETED"
    RESPOND TYPE=command MSG="action:prompt_text YOU CAN CLOSE THIS BOX"
    RESPOND TYPE=command MSG="action:prompt_show" 
    SET_PIN PIN=beeper VALUE=1
    G4 P2500
    SET_PIN PIN=beeper VALUE=0
    G4 P2500
    M106 S0
    CLEAR_LAST_FILE
    # cLOSE OUT WITH HOME
    G28

[gcode_macro _zproc]
gcode:
#   Stops the Chamber Circulation Fan
    M106 S0
#   Generates ETA pop-up
    G91
    RESPOND TYPE=command MSG="action:prompt_begin NOTICE!"
    RESPOND TYPE=command MSG="action:prompt_text ETA TO COMPLETE PROCESS"
    RESPOND TYPE=command MSG="action:prompt_text 6M 30S"
    RESPOND TYPE=command MSG="action:prompt_show"
    G4 P5000
    RESPOND TYPE=command MSG=action:prompt_end""
#   Generates pop-up to verify homing to commence
    RESPOND TYPE=command MSG="action:prompt_begin NOTICE!"
    RESPOND TYPE=command MSG="action:prompt_text HOMING"
    RESPOND TYPE=command MSG="action:prompt_show"
    G4 P2000
    RESPOND TYPE=command MSG=action:prompt_end""
    G28
#   Generates pop-up of movement top Z lower limit (less 5mm margin as 280 is hard limit and if machine halts at this stage, a home command drives down into the machine base causing a fatal error, starting at 270 avoids this)
    RESPOND TYPE=command MSG="Home Complete Moving To_Z270_"
    G0 Z270 F1200
    G4 P100
#   AUDIBLE WAIT NOTIFICATION
    SET_PIN PIN=beeper VALUE=1
    G4 P1000
    SET_PIN PIN=beeper VALUE=0
    G4 P1
#   Generates pop-up to verify process has paused while cleaning tools are fitted
    RESPOND TYPE=command MSG="action:prompt_begin WAITING"
    RESPOND TYPE=command MSG="action:prompt_text INSTALL BOTH ScrubAxi TOOLS NOW"
#   Command button to resume process
    RESPOND TYPE=command MSG="action:prompt_footer_button CLICK TO PROCEED|_zproc2"
    RESPOND TYPE=command MSG="action:prompt_show"    
   
[gcode_macro _zproc2]
gcode:
#   AUDIBLE START CYCLE NOTIFICATION
    SET_PIN PIN=beeper VALUE=1
    G4 P200
    SET_PIN PIN=beeper VALUE=0
    G4 P200
    SET_PIN PIN=beeper VALUE=1
    G4 P200
    SET_PIN PIN=beeper VALUE=0
    G4 P200
#   Generates pop-up to notify clean cycle starting
    RESPOND TYPE=command MSG="action:prompt_begin STARTING"
    RESPOND TYPE=command MSG="action:prompt_text Z CLEAN STARTED"
    RESPOND TYPE=command MSG="action:prompt_show"
    G4 P2500
    RESPOND TYPE=command MSG=action:prompt_end""
    SET_PIN PIN=beeper VALUE=1
    G4 P1500
    SET_PIN PIN=beeper VALUE=0
    G4 P1
    M204 S400
    RESPOND TYPE=command MSG="action:prompt_begin NOTICE!"
    RESPOND TYPE=command MSG="action:prompt_text Z BED WILL CYCLE 3 TIMES WITH PULSES 50 EACH"
    RESPOND TYPE=command MSG="action:prompt_show"
    G4 P5000
#   Cleaning cycle loop instructions start
    {% for j in range(3) %}
    RESPOND TYPE=command MSG="RETURN BED TO Z265"
    G0 Z265
    RESPOND TYPE=command MSG="action:prompt_begin NOTICE!"
    RESPOND TYPE=command MSG="action:prompt_text BED IS LOWERING FOR NEXT CYCLE"
    RESPOND TYPE=command MSG="action:prompt_text CLEAN CYCLE: {j+0} of 3 COMPLETE"
    RESPOND TYPE=command MSG="action:prompt_text "
    RESPOND TYPE=command MSG="action:prompt_text THIS MESSAGE WILL CLOSE AUTOMATICALLY"
    RESPOND TYPE=command MSG="action:prompt_show"
    M106 S{j+1}
    G4 P1
    RESPOND TYPE=command MSG=action:prompt_end""
    {% for i in range(50) %}
    G91
    G1 Z5 F800 #move bed down 5mm @ 800mm/min
    G1 Z-10 F800 #move bed up 10mm @800mm/min
    RESPOND TYPE=command MSG="BED PULSE:{i+1} of 50: CYCLE:{j+1} of 3"
    {% endfor %}
    G90
    RESPOND TYPE=command MSG="CYCLE COMPLETE"
    G0 Z270 F800
      {% endfor %}
#   Cleaning cycle loop instructions end
    G0 Z140 F1600
#   PROMPT TO REMOVE TOOLS PRIOR TO HOME
    RESPOND TYPE=command MSG="action:prompt_begin !!! CAUTION !!!"
    RESPOND TYPE=command MSG="action:prompt_text ! WAIT FOR BED TO STOP MOVING !"
    RESPOND TYPE=command MSG="action:prompt_text WHEN MACHINE BEEPS - REMOVE BOTH ScrubAxi TOOLS"
    RESPOND TYPE=command MSG="action:prompt_text "
    RESPOND TYPE=command MSG="action:prompt_text "
    RESPOND TYPE=command MSG="action:prompt_text !!!  MACHINE DAMAGE MAY OCCUR   !!!"
    RESPOND TYPE=command MSG="action:prompt_text !!! IF TOOLS ARE LEFT INSTALLED !!!"
    RESPOND TYPE=command MSG="action:prompt_footer_button REMOVE TOOLS AND CLICK TO PROCEED|_exitzclean"
    RESPOND TYPE=command MSG="action:prompt_show"
#   AUDIBLE END NOTIFICATION 
    SET_PIN PIN=beeper VALUE=1
    G4 P1000
    SET_PIN PIN=beeper VALUE=0
    G4 P100
    SET_PIN PIN=beeper VALUE=1
    G4 P200
    SET_PIN PIN=beeper VALUE=0
    G4 P100
    SET_PIN PIN=beeper VALUE=1
    G4 P200
    SET_PIN PIN=beeper VALUE=0
    G4 P100
    SET_PIN PIN=beeper VALUE=1
    G4 P200
    SET_PIN PIN=beeper VALUE=0
    G4 P1
#   MRBEAN.CROM'S ZCLEAN MACRO (QIDI P4):
```
