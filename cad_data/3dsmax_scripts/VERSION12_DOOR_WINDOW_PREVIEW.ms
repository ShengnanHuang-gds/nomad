/* VERSION12 - 1F Door/Window 3D PREVIEW (non-destructive).
   Source: DQ-1F_t3_t3.dxf; filtered to the JZ-1F building outline.
   27 confirmed door-layer blocks; 5 recognized WINLIB windows.
   Door jambs + lintels only: NO door leaves blocking robot passage.
   Window frames and glass are previews; wall holes are NOT cut.
   Only NEW DQ1F_DWPREV_* nodes; no edit/delete/hide original objects.
   Millimetre-like CAD units. Heights are illustrative, not as-built.
   Undo immediately with Ctrl+Z or delete DQ1F_DWPREV_* nodes.
   Inspect before saving/export to Gazebo.
*/
(
    local doors = #(
        #(271946.598,514832.994,0.49744,1500.0),
        #(273446.542,514846.017,0.49744,1500.0),
        #(286401.635,470482.328,295.59680,1500.0),
        #(291505.847,461092.505,301.45931,1500.0),
        #(300522.152,457823.248,305.80968,1500.0),
        #(301831.983,456049.812,307.08830,1500.0),
        #(304328.376,466435.666,302.79011,1500.0),
        #(307003.347,449765.052,311.80966,1500.0),
        #(308491.458,448138.160,313.08835,1500.0),
        #(311311.844,462912.598,307.24769,1500.0),
        #(314291.418,442428.402,317.80970,1500.0),
        #(315941.456,440965.953,319.08840,1500.0),
        #(321980.975,436133.022,323.80759,1500.0),
        #(322715.175,455162.009,46.19476,1000.0),
        #(324819.856,456388.296,316.70124,1000.0),
        #(327112.593,454308.691,318.88019,1000.0),
        #(327120.741,451801.246,320.01872,1000.0),
        #(328075.002,451013.058,320.87005,1000.0),
        #(329292.476,452471.984,320.88674,1000.0),
        #(330359.687,449219.639,322.86797,1000.0),
        #(331519.761,450724.511,322.87955,1000.0),
        #(332709.594,447504.087,324.86933,1000.0),
        #(333815.723,449049.035,324.88032,1000.0),
        #(335112.772,445875.048,326.86642,1000.0),
        #(336168.149,447455.151,326.88056,1000.0),
        #(337579.766,444325.607,328.87034,1000.0),
        #(338574.131,445944.735,328.88028,1000.0)
    )
    local windows = #(
        #(267952.634,528083.068,263.69025,2000.0),
        #(288242.240,537909.932,346.44285,700.0),
        #(291692.282,511443.010,2.69438,700.0),
        #(301539.658,473224.159,28.19438,700.0),
        #(315733.876,453068.622,43.94439,700.0)
    )
    local created = #()
    local success = false
    local err = ""
    fn buildPiece nm xx yy ang lateral bottomZ ww dep hh tint arr =
    (
        local ca = cos ang
        local sa = sin ang
        local b = box name:nm width:ww length:dep height:hh
        append arr b
        b.rotation = (eulerAngles 0 0 ang)
        b.pos = [xx + lateral*ca, yy + lateral*sa, bottomZ]
        b.wirecolor = tint
        b
    )
    local existing = for ob in objects where matchPattern ob.name pattern:"DQ1F_DWPREV_*" collect ob
    if existing.count != 0 then
    (
        messageBox "Door/window preview already exists. No changes made." title:"VERSION12 door/window preview"
    )
    else
    (
        if queryBox "Create 27 door frames and 5 window previews?\n\nOnly NEW objects. No walls or slabs are modified. Save a backup .max first." title:"VERSION12 door/window preview" then
        (
            undo "Create DQ1F door/window previews" on
            (
                try
                (
                    for i=1 to doors.count do
                    (
                        local d=doors[i]
                        local x=d[1]
                        local y=d[2]
                        local a=d[3]
                        local w=d[4]
                        local nameBase="DQ1F_DWPREV_DOOR_" + (formattedPrint i format:"03d")
                        buildPiece (nameBase+"_L") x y a (-w/2.0+35.0) 0.0 70.0 100.0 2100.0 (color 233 169 72) created
                        buildPiece (nameBase+"_R") x y a (w/2.0-35.0) 0.0 70.0 100.0 2100.0 (color 233 169 72) created
                        buildPiece (nameBase+"_TOP") x y a 0.0 2100.0 w 100.0 100.0 (color 233 169 72) created
                    )
                    local glassMaterial=standardMaterial name:"DQ1F_DWPREV_Glass" diffuse:(color 96 183 235) opacity:38 twoSided:true
                    for i=1 to windows.count do
                    (
                        local wdata=windows[i]
                        local x=wdata[1]
                        local y=wdata[2]
                        local a=wdata[3]
                        local w=wdata[4]
                        local nameBase="DQ1F_DWPREV_WINDOW_" + (formattedPrint i format:"03d")
                        buildPiece (nameBase+"_L") x y a (-w/2.0+25.0) 900.0 50.0 95.0 1200.0 (color 85 165 216) created
                        buildPiece (nameBase+"_R") x y a (w/2.0-25.0) 900.0 50.0 95.0 1200.0 (color 85 165 216) created
                        buildPiece (nameBase+"_BOTTOM") x y a 0.0 900.0 w 95.0 50.0 (color 85 165 216) created
                        buildPiece (nameBase+"_TOP") x y a 0.0 2050.0 w 95.0 50.0 (color 85 165 216) created
                        local pane=buildPiece (nameBase+"_GLASS") x y a 0.0 950.0 (w-100.0) 18.0 1100.0 (color 110 194 232) created
                        pane.material=glassMaterial
                    )
                    success=true
                )
                catch
                (
                    err=getCurrentException() as string
                    for ob in created where isValidNode ob do (try(delete ob)catch())
                )
            )
            if success then
                messageBox "Created 27 door frames and 5 windows.\nThese are PREVIEW objects. NO wall openings have been cut.\nInspect placement before saving." title:"Door/window previews ready"
            else
                messageBox ("Failed; created objects cleaned up. Original scene untouched.\n" + err) title:"Door/window preview failed"
        )
    )
)
