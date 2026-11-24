/* VERSION11 - Restore original wall after an incorrect trial doorway patch.
   This script only restores DQ1F3D_WALL_SOLID_001 and removes
   DQ1F3D_WALL_DOORFIX_001 and DQ1F3D_DOORFIX_MARKER_001.
   Save a backup .max scene before running.
*/
(
    local originalWall = getNodeByName "DQ1F3D_WALL_SOLID_001"
    local wrongWall = getNodeByName "DQ1F3D_WALL_DOORFIX_001"
    local wrongMarker = getNodeByName "DQ1F3D_DOORFIX_MARKER_001"

    if originalWall == undefined then
    (
        messageBox "Original DQ1F3D_WALL_SOLID_001 not found. Nothing changed." title:"VERSION11 - Restore aborted"
    )
    else
    (
        if queryBox "Restore original wall and delete ONLY DOORFIX wall + marker?\n\nSave a .max backup first." title:"VERSION11 - Restore original wall" then
        (
            undo "Restore original DQ1F wall" on
            (
                originalWall.isHidden = false
                if wrongWall != undefined do delete wrongWall
                if wrongMarker != undefined do delete wrongMarker
                select originalWall
                redrawViews()
            )
            messageBox "Original wall restored. DOORFIX wall and marker removed if present.\nInspect the scene, then save your .max file." title:"VERSION11 - Restore complete"
        )
    )
)
