/* DISABLED - DO NOT USE
   The previous VERSION11 door-opening patch was found to create
   incorrect triangular wall geometry, confirmed in 3ds Max.
   This script is deliberately disabled to prevent further edits.

   To restore the original wall, run:
   cad_data/3dsmax_scripts/VERSION11_RESTORE_ORIGINAL_WALL.ms

   A new door-opening fix must be regenerated from verified
   CAD wall footprints, not the malformed source spline #97.
*/
messageBox "This door-opening patch has been DISABLED: it creates incorrect triangular wall geometry.\n\nUse VERSION11_RESTORE_ORIGINAL_WALL.ms to return to the original scene. Nothing was changed." title:"VERSION11 - Unsafe door fix disabled"
