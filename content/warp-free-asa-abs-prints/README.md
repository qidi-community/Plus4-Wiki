### Warp free ASA / ABS prints

Well that is a big claim, and Im not saying it will fix all problems, as there can be many reasons for this, but I found several related problem with orca slicers default filament settings, that was causing the corners of my prints to warp up.

First I just want to highly recommend "Filaform bed adhesive spray" the stuff works wonders, and is much cleaner, easier to work with, stronger, and last longer than glue stick.

But thats not what this is about, as even with that i was still getting warp...

What it turned out to be were 3 settings in the filament "Cooling" menu:
* "No cooling for the first"
* "Min fan speed threshold"
* "Keep fan always on"

See ASA/ABS is very sensitive to cooling, and generally you dont need any parts cooling, but at high speed and or/and short layer time (small parts) it is still needed.

But having it on always, even at 10% at the start is a killer.

By default it is set with "No cooling for the first" = 3 layers which helps, but its too little, the print is still tee flexible at only 3 layer high, so i recommend 10-15 layers first.

Also I set  "Min fan speed threshold" to 0, (from 10) as you want it to not run at all if its a large enough part that is being printed. I set the layer time to 40s. (I have max set to 50% and 4s. Thes 2 can be tweaked, by looking at the "Fan Seed" display mode in the part preview once sliced you can see what the speed will be at centain layers and areas.

And finally the other killer is "Keep fan always on", this also is not needed and should be unticked, this allows  0% fan when not needed, creating the strongest warp free prints possible, while it still being able to ramp up for small detail, bridges & overhangs.

Here is an example

<img width="864" height="771" alt="image" src="https://github.com/user-attachments/assets/796ac80a-8463-4292-9942-6a26d9c32f69" />

<img width="778" height="356" alt="image" src="https://github.com/user-attachments/assets/420ce69a-a7ba-4174-b43f-da84c8e8bf00" />
