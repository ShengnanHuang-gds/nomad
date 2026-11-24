/* VERSION31 - Door/window geometry from verified CAD sources.
Doors: 8 true threshold outlines, both ends within 400 drawing units of a built wall.
Windows: 5 verified WINLIB2D centers/scales. Heights are review assumptions.
Does not move, delete, edit or hide ANY existing object, wall, floor or furniture.
Old DQ1F_DWPREV_* previews must first be removed with Ctrl+Z.
All new nodes start DQ1F_SAFE_DW_. Undo with Ctrl+Z immediately.
*/
(
 local older=for o in objects where matchPattern o.name pattern:"DQ1F_DWPREV_*" collect o
 local prior=for o in objects where matchPattern o.name pattern:"DQ1F_SAFE_DW_*" collect o
 if older.count>0 then
 (
  messageBox "Old incorrect DQ1F_DWPREV_* geometry is still in the scene. Undo it before running this. Nothing changed." title:"Older preview found"
 )
 else if prior.count>0 then
 (
  messageBox "This preview is already present; nothing changed." title:"Door/window preview"
 )
 else
 (
  if queryBox "Make 8 CAD-aligned doors and 5 window frames? No existing geometry will be modified. Save a MAX backup first." title:"Door/window preview" then
  (
   local made=#()
   local ok=false
   local err=""
   local frameCol=color 112 121 133
   local doorCol=color 168 121 77
   local winCol=color 111 144 166
   local glassCol=color 95 176 206
   local glassMat=standardMaterial name:"DQ1F_SAFE_DW_Glass" diffuse:glassCol opacity:45 twoSided:true
   fn p nm x y ang dx dy z sx sy sz clr arr =
   (
    local cs=cos ang
    local sn=sin ang
    local b=box name:nm width:sx length:sy height:sz
    append arr b
    b.rotation=eulerAngles 0 0 ang
    b.pos=[x+dx*cs-dy*sn,y+dx*sn+dy*cs,z]
    b.wirecolor=clr
    b
   )
   fn door nm x y ang w fc dc arr =
   (
    local e=45.0
    local h=2100.0
    p (nm+"_L") x y ang (-w/2+e/2) 0 0 e 80 h fc arr
    p (nm+"_R") x y ang ( w/2-e/2) 0 0 e 80 h fc arr
    p (nm+"_HEAD") x y ang 0 0 h w 80 70 fc arr
    -- Open door leaves rotate away from the opening axis. No solid closed panel.
    if w>1200 then
    (
     local halfLeaf=(w-110.0)/2.0
     local hx=x+(-w/2+55)*cos ang
     local hy=y+(-w/2+55)*sin ang
     local jx=x+(w/2-55)*cos ang
     local jy=y+(w/2-55)*sin ang
     p (nm+"_LEAF_LEFT_OPEN") hx hy (ang+85.0) (halfLeaf/2) 0 0 halfLeaf 28 2000 dc arr
     p (nm+"_LEAF_RIGHT_OPEN") jx jy (ang+265.0) (halfLeaf/2) 0 0 halfLeaf 28 2000 dc arr
    )
    else
    (
     local lw=w-110.0
     local hx=x+(-w/2+55)*cos ang
     local hy=y+(-w/2+55)*sin ang
     p (nm+"_LEAF_OPEN") hx hy (ang+85.0) (lw/2) 0 0 lw 28 2000 dc arr
    )
   )
   fn window nm x y ang w fc gc gm arr =
   (
    local sill=900.0
    local hh=1200.0
    local e=40.0
    p (nm+"_L") x y ang (-w/2+e/2) 0 sill e 60 hh fc arr
    p (nm+"_R") x y ang ( w/2-e/2) 0 sill e 60 hh fc arr
    p (nm+"_BOTTOM") x y ang 0 0 sill w 60 e fc arr
    p (nm+"_TOP") x y ang 0 0 (sill+hh-e) w 60 e fc arr
    local g=p (nm+"_GLASS") x y ang 0 0 (sill+e) (w-2*e) 12 (hh-2*e) gc arr
    g.material=gm
   )
   local doors=#(
    #(300522.15,457823.25,125.81,1500),
    #(301831.98,456049.81,127.09,1500),
    #(307002.85,449765.62,-48.19,1501.5),
    #(308490.94,448138.71,-46.91,1501.5),
    #(314291.42,442428.4,137.81,1500),
    #(286401.63,470482.33,-64.4,1500),
    #(317265.17,457666.97,-137.56,1500),
    #(322715.18,455162.01,-133.81,1000)
   )
   local wins=#(
    #(267952.63,528083.07,263.69,2000),
    #(288242.24,537909.93,346.44,700),
    #(291692.28,511443.01,2.69,700),
    #(301539.66,473224.16,28.19,700),
    #(315733.88,453068.62,43.94,700)
   )
   undo "Version31 CAD aligned doors windows" on
   (
    try
    (
     for i=1 to doors.count do
     (
      local d=doors[i]
      door ("DQ1F_SAFE_DW_DOOR_"+(formattedPrint i format:"02d")) d[1] d[2] d[3] d[4] frameCol doorCol made
     )
     for i=1 to wins.count do
     (
      local w=wins[i]
      window ("DQ1F_SAFE_DW_WINDOW_"+(formattedPrint i format:"02d")) w[1] w[2] w[3] w[4] winCol glassCol glassMat made
     )
     ok=true
    )
    catch
    (
     err=getCurrentException() as string
     for ob in made where isValidNode ob do (try(delete ob)catch())
    )
   )
   if ok then
     messageBox "Added 8 open doors and 5 window frames on verified CAD coordinates. Existing walls/slabs unchanged. Window wall openings have NOT been cut. Ctrl+Z to undo." title:"Door/window preview made"
   else
     messageBox ("No changes to original model. Error: "+err) title:"Door/window preview failed"
  )
 )
)
