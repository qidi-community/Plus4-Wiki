# PLA/PETG Heat Creep Clogging

## The Issue and suspected causes

This is unfortunately a semi-common issue that is affecting the first batch of Qidi Plus 4 printers.

This issue mostly affects PLA, and sometimes affects PETG as well.  It appears that it is most likely to occur on small models, or models that have high degrees of retraction.

It does not seem to occur when printing with higher temperature filaments.

A major contributing factor appears to be with the first-generation stock nozzles that have the stainless-steel heatbreak between the hot end and the heatsink.

Another contributing factor is the stock heatsink cooling fan is not mounted directly onto the hotend heatsink.
This appears to cause the heatsink to receive insufficient cooling to prevent heat-creep clogging.

## Potential Fixes

The ceramic heatbreak nozzles appear to work, while the other fixes listed here will help to minimise, but not completely address the chance of clogging.

It shoudl be noted that there have been no reports of clogging on the Qidi Discord Community server by users after installing the ceramic heat-break nozzle, along with installing the duct and better fan.

- Install a nozzle from Qidi that has the ceramic heatbreak.  eg. [Ceramic Heatbreak Nozzle](https://qidi3d.com/products/plus-4-bimetal-nozzles-2pcs).
  These nozzles can be easily identified by the white heatbreak section between the upper and lower portions of the nozzle, whereas the stainless steel heatbreaks are silvery in appearance.
- Print, out of ABS or ASA, and install [this heatsink duct model](https://www.thingiverse.com/thing:6782612).
  This model helps to better direct the cooling fan's airflow over the heatsink.
- Install a stronger heatsink cooling fan.
  We recommend the [GDSTime GDA30105F](http://gdstime.com/pro1/62.html) 12,000PM fans.
  These can be purchased from this [US Store](https://west3d.com/products/gdstime-dc-24v-30x30x10-axial-fan-24v-gda30105f-dual-ball-bearing-1200rpm-1w-06a-xh2-54), [EU Store](https://www.hotend.eu/p/gdstime-axial-fan-sleeve-3010-24v) 
- Raise the nozzle temperature by 5-10C.
  This can sometimes resolve the heatcreep clogging as it keeps the filament within the heatbreak molten for longer between retraction events.

