# Hotend Expansion Co-efficient Calibration

Calibrating the thermal expansion of the hotend is frustratingly difficult.  If you've decided that you don't have enough drama in your life already, or simply hate yourself, then proceed.

## Goals & Requirements

- Measure as wide of a range as possible across multiple reference points.
- Clear any bed mesh and all Z offset adjustments
- Use lots of heat soaking for the hotend at 50C, and then at 250C.  Basically 2 minutes worth.
- Probe the same reference point multiple times.  

## Preparation

Preparation of the hotend and nozzle are absolutely critical for reliable results.

Important factors:

- Cool-pull any filament from hotend.
  Start with the hotend being cold.
  Then turn on the hotend and keep pulling up on the filament until it yanks out at the earliest opportunity.
  This minimises any stringing and it'll just come out pretty much with the shape of the internal nozzle cavity intact
- Make sure nozzle has been tightened at 300C to minimise the impact joint expansion around the threads
- Poke the nozzle orifice with a fine needle dislodge any filament.  We want absolutely NO oozing at all
- Thoroughly clean the nozzle with a wire brush at 300C to remove any debris.  We want that nozzle tip to be as clean as possible.
- Heat bed to 50C and heat-soak for uniformity

## Helper Macro

I have created a calibration macro that automates the calibration process.  You may [find it here](./beacon_calibrate.cfg)

Copy that macro file to its own file in your printer configuration directory, and include it from your `printer.cfg` file.  Save and restart

The macro may be run with the following console command: `BEACON_CALIBRATE_THERMAL_EXPANSION`

I will stress once again that the nozzle and hotend MUST be cleaned and prepared properly before using this macro,
otherwise it will almost assuredly yield junk results, with the most common outcome being a gross under-representation of the true thermal expansion co-efficient by 50% or possibly worse.
I simply cannot stress this enough how critical having a thoroughly clean hotend without any filament in, or attached, to it is of the greatest importance.

## My Personal Run results

Each run takes about 30 minutes on the Plus 4, with a 20 minute cool-down between runs:

- Nozzle thermal expansion over 200C is 0.0872143mm  =>  0.0004361 mm/°C
- Nozzle thermal expansion over 200C is 0.0910357mm  =>  0.0004552 mm/°C
- Nozzle thermal expansion over 200C is 0.0891429mm  =>  0.0004457 mm/°C

_**Average of those 3 is 0.0004457 mm/°C ± 2.1%**_

From this, and due to the variability, I chose to adopt an expansion co-efficient of 0.00045 mm/°C in practical use.
