/* VERSION31 - Furniture preview for the 1F floorplan.
   Uses CAD coordinates. These are review placements, NOT as-built furniture.
   The script only creates DQ1F_FURNPREV_* nodes. No existing nodes are edited,
   deleted, moved or hidden. To revert, undo immediately with Ctrl+Z.
   Save a copy of your .max file before running. Heights assume CAD millimetres.
*/
(
 local existing = for o in objects where matchPattern o.name pattern:"DQ1F_FURNPREV_*" collect o
 if existing.count > 0 then
 (
   messageBox ("Furniture preview already exists: " + (existing.count as string) + " pieces. No changes.") title:"Furniture preview"
 )
 else
 (
  if queryBox "Create 6 desk/chair sets, 2 lounge groups, 1 reception and 2 cabinets?\n\nOnly new furniture nodes. Existing walls/floor/columns not touched. Save a backup scene first." title:"VERSION31 Furniture preview" then
  (
   local made = #()
   local success = false
   local failure = ""
   local brown = (color 160 121 84)
   local gray = (color 85 107 120)
   local green = (color 67 141 123)
   local navy = (color 66 90 123)
   local ochre = (color 210 157 90)
   fn piece nm x y angle dx dy bottomZ sx sy sz tint collector =
   (
     local ca = cos angle
     local sa = sin angle
     local b = box name:(uniqueName nm) width:sx length:sy height:sz
     append collector b
     b.rotation = (eulerAngles 0 0 angle)
     b.pos = [x + dx*ca - dy*sa, y + dx*sa + dy*ca, bottomZ]
     b.wirecolor = tint
     b
   )
   fn desk nm x y angle collector =
   (
     piece (nm+"_TOP_") x y angle 0 0 715 1250 650 45 brown collector
     for dx in #(-555,555) do for dy in #(-250,250) do
       piece (nm+"_LEG_") x y angle dx dy 0 65 65 715 gray collector
     piece (nm+"_CHAIR_SEAT_") x y angle 0 (-850) 435 440 440 65 navy collector
     piece (nm+"_CHAIR_BACK_") x y angle 0 (-1065) 475 440 55 430 navy collector
     for dx in #(-170,170) do for dy in #(-1020,-680) do
       piece (nm+"_CHAIR_LEG_") x y angle dx dy 0 40 40 435 gray collector
   )
   fn lounge nm x y angle collector =
   (
     piece (nm+"_SOFA_BASE_") x y angle 0 0 0 1700 750 420 green collector
     piece (nm+"_SOFA_BACK_") x y angle 0 310 400 1700 120 420 green collector
     piece (nm+"_TABLE_") x y angle 0 (-1100) 360 950 500 60 brown collector
     for dx in #(-380,380) do
       piece (nm+"_TABLE_LEG_") x y angle dx (-1100) 0 45 45 360 gray collector
   )
   fn reception nm x y angle collector =
   (
     piece (nm+"_COUNTER_BASE_") x y angle 0 0 0 1750 650 1000 brown collector
     piece (nm+"_COUNTER_TOP_") x y angle 0 0 1000 1850 750 60 ochre collector
   )
   fn cabinet nm x y angle collector =
   (
     piece (nm+"_CABINET_") x y angle 0 0 0 1300 420 1250 gray collector
   )
   undo "VERSION31 Furniture Preview" on
   (
    try
    (
     desk "DQ1F_FURNPREV_DESK_A" 283500.0 537000.0 0.0 made
     desk "DQ1F_FURNPREV_DESK_B" 292000.0 542000.0 0.0 made
     desk "DQ1F_FURNPREV_DESK_E" 299500.0 510000.0 -20.0 made
     desk "DQ1F_FURNPREV_DESK_F" 289000.0 473000.0 25.0 made
     desk "DQ1F_FURNPREV_DESK_H" 321500.0 440500.0 45.0 made
     desk "DQ1F_FURNPREV_DESK_I" 332000.0 437000.0 45.0 made
     lounge "DQ1F_FURNPREV_SOFA_A" 273500.0 525500.0 0.0 made
     lounge "DQ1F_FURNPREV_SOFA_B" 282000.0 492000.0 -20.0 made
     reception "DQ1F_FURNPREV_RECEPTION" 286000.0 484000.0 25.0 made
     cabinet "DQ1F_FURNPREV_CABINET_A" 291500.0 503500.0 -20.0 made
     cabinet "DQ1F_FURNPREV_CABINET_B" 309000.0 454000.0 45.0 made
     success = true
    )
    catch
    (
      failure = getCurrentException() as string
      for obj in made where isValidNode obj do (try(delete obj)catch())
    )
   )
   if success then
     messageBox ("Created " + (made.count as string) + " furniture components. Preview only.\nAll names begin with DQ1F_FURNPREV_. Original geometry unchanged.") title:"Furniture created"
   else
     messageBox ("Furniture preview failed; new objects removed.\n" + failure) title:"Furniture preview failed"
  )
 )
)
