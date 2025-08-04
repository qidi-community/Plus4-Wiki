# Better Qidi Box filament list

The Qidi Box introduced a new config file that stores filament types and their acceptable temperature ranges - `officiall_filas_list.cfg`. This file is, in the stock version, filled with poorly selected temperature ranges and even error-causing omissions. It even contains silly typos (as in the file name).

# Adding new filaments or modifying existing ones

Filaments on the list look like this:

```
[fila1]
filament                       = PLA
min_temp                       = 190
max_temp                       = 240
box_min_temp                   = 0
box_max_temp                   = 0
type                           = PLA
```

- `filament` - this name is displayed on the printer screen
- `min_temp` - minimum hotend temperature
- `max_temp` - maximum hotend temperature
- `box_min_temp` - minimum temperature inside the box
- `box_max_temp` - maximum temperature inside the box, 0 if unheated only
- `type` - if you're using Qidi Studio, this corresponds to the filament type in your print profile and is used to check whether the Box slot used for printing is of a matching filament type from your printing profile.

You can modify the parameters above for all filaments on the list. You may see that the list also contains blank spots - these can be used for adding your own filaments to the list!

# Community-curated filament list

Want to just use a good filament list, without making one yourself?

Use our community-curated [officiall_filas_list.cfg](./officiall_filas_list.cfg)!

Just replace the current list on your printer with the one us, and you're good to go. The following changes are included in the list:
 - `box_max_temp` is increased to 45 to PLA and 65 for other filaments
 - `box_min_temp` for fiber reinforced filaments is set to 45 degC. This is recommended by Qidi, it softens rigid filaments reducing wear of components and preventing cracking of filament
 - fixed typo in PETG Tough name
