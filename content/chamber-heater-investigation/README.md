# Chamber Temperature Investigation

![Under Construction](./under-construction.jpg "Mind the gaps!")

## Before we get started

_**Even if you read nothing else in this page, go to this page and make the config recommendations that it recommends.**_

https://github.com/qidi-community/Plus4-Wiki/blob/main/content/chamber-heater-issue/README.md#additional-safety-configurations
___


## What If I told you...

![What if I told you](./what_if_I_told_you.jpg "The cake...err...the temps are a lie!")

Yep, you read it right.  The chamber temperatures that the stock Qidi Plus4, with its chamber sensor located where it is, are lying to you.

Read on, and let's see how deep this rabbit hole goes!

## So where is that little sucker anyway?

A lot of people have asked me where is the Plus4's chamber temperature sensor.

I won't keep you in suspense.  That sneaky thing is hiding here!

In the back right corner of the print chamber, below and to the right of the right stepper motor, and under the frame bar.

![Chamber Sensor Location](./sensor_location.jpg "Sneaky little sucker!")


## Wait!  How do you know it's lying?

Good question! First let's figure out how to determine the truth.  The print chamber is fairly large, and air is swirling about
everywhere.  The print head moves about, some fans are on, the print bed is emitting a bunch of heat, it's all a bit of
a mess really.

The main point of a chamber heater is reduce the cooldown "shock" for hot filament after it leaves the nozzle.  Hot filament
will contract, and if it contracts too quickly then when the next layer is put on top, it won't sit directly on top of the
layer below it, because that layer will have shifted a bit due to contraction.  Keep repeating this and newer layers will
try to pull back the lower layers as the newer layers cool down, and so we get warping, misaligned layers, and all other
sorts of shenanigans that you can imagine.

So, the role of the chamber heater is to SLOW DOWN this whole cooling and contraction gig, and give time for freshly laid
filament to settle and slowly take the desired shape.  If we think about this for a bit, it should be fairly obvious that
the most important sections to keep warm are the upper sections where fresh filament is being laid down, and the lower layers
can continue to slowly cool down the further away from the action they are.

Now keep in mind, there's a large chunk of hot metal (that's the print bed) under the printed part(s) that always emitting heat.
Your printed part is basically sitting on a stove top, so it's not like the lower sections are exactly getting the chills either.

So, considering all of that, the best way to measure the chamber air, as far as the printed part "cares" about it, is in the
vicinity of where the printing action happens.

So, I put a thermal probe to measure the chamber air temps where it really matters, and that's right here!

![Watch it!](./Thermal-Probe.jpg "Hey! Watch where you stick that thing!")

Here the probe is moving about with the print head, sampling the air temperature from all over the print area, and the part
cooling fan will also be generally pulling air in, helping the probe to get a good reading on the true chamber temperature
as a whole.


## Okay, so what are we talking about here?  How much is it off by?

First, let's establish our testing scenario.  The following tests were conducted with the following conditions:

* Target Chamber Temperature is 60°C
* Target Print Bed Temperature is 100°C
* The glass lid is on, with no additional sealing
* The printer door is shut, with no additional sealing
* The exhuast fan (Qidi calls it the circulation fan) is set to 40% speed
* The room temperature was 21-24°C (70-75°F)
* A window is open in the room with a fan exhausting air to the outside, so fresh air is also coming into the room
* A typical household ceiling fan is operational, spinning at full speed, to circulate the air in the room
* The macro as [described in detail here](../chamber-heater-issue/README.md) was employed to disable the heating elements of the chamber heater above 270mm of Z height

Two different printing scenarios were run.

1. A 270mm tall, 30x30mm tower to assess typical chamber temperatures throughout a print run
2. A special purpose top-heavy model that takes 3 hours to climb to 270mm Z, and then 3 hours to progress from 270mm to 280mm in Z-height

*NOTE:* The 0-270mm model was printed later in the day after the room had warmed slightly (about 23-24C), hence the slightly
higher reported temperatures at Z=270mm when compared to the 270-280mm model where the room was around 21-22C.

Without further ado, here's the results:

![0-270mm](./Sensor-vs-Reality-0-270.png "0mm-270mm Z-height")

![270-280mm](./Sensor-vs-Reality-270-280.png "270mm-280mm Z-height")

![WTF](./wtf-blink.gif "Yeah, that was my reaction too Steve!")

Yep, you saw it right.  When it comes to reporting the chamber temperatures accurately, Qidi's trusty chamber sensor is basically the thermal probe equivalent of this guy!

![Ruprecht](./stevemartin-cork.gif "Ruprecht!")


## Well then! How do we fix this mess?

Don't worry, I got you!

So, within the print-head on the Qidi Plus4, there is a STM32F103XE clone CPU being used as the MCU.

This bad boy has a peak power consumption of just 0.2W at full load (usually MUCH less) and what's more it has a thermal probe built in that the Qidi firmware has access to!  Qidi's FluiddUI config plots this as the GD32 temperature.

So, let's overlay the GD32 temperature atop the above 2 graphs.

![0-270mm](./GD32-0-270.png "0mm-270mm Z-height")

![270-280mm](./GD32-270-280.png "270mm-280mm Z-height")

Pretty close to the chamber temperature reality huh?  A little bit high, but what if I told you we've got a useful trick up out sleeves.

(LOTS OF STUFF TO COME)

## Don't bore me with the details, just tell me what to do!
