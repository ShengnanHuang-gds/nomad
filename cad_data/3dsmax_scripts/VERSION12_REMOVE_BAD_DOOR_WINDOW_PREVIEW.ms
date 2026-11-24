/* VERSION12 - Remove only the bad door/window preview objects
   Name prefix: DQ1F_DWPREV_
   Does NOT edit walls, columns, floor or ceiling.
   Save a backup .max file before running.
*/
(
    local targets = for obj in objects where matchPattern obj.name pattern:"DQ1F_DWPREV_*" collect obj
    if targets.count == 0 then
    (
        messageBox "No DQ1F_DWPREV_* preview objects were found. Nothing changed." title:"VERSION12 - Cleanup"
    )
    else
    (
        local prompt = "Found " + (targets.count as string) + " door/window preview objects.\n\nDelete ONLY these objects?\nOriginal walls, columns, floor and ceiling will stay unchanged."
        if queryBox prompt title:"VERSION12 - Remove bad door/window preview" then
        (
            undo "Remove DQ1F door and window previews" on
            (
                clearSelection()
                for obj in targets where isValidNode obj do delete obj
                redrawViews()
            )
            messageBox ("Removed " + (targets.count as string) + " door/window preview objects.\nOriginal wall and slab objects were not modified.") title:"VERSION12 - Cleanup complete"
        )
    )
)
