/* DQ-1F (VERSION11.fbx) - Non-destructive single blocked door opening fix
   Source: DQ-1F_t3_t3.dxf + VERSION11.fbx
   Confirmed gate symbol at X=279136.029, Y=509388.249 (CAD units).
   Original WALL SOLID: 142 splines; one specific source polygon (#97) intersects door baseline.
   Safeguards: copy original node; check original shape and knot; replace only spline #97;
   original node remains in scene HIDDEN, never deleted; no other objects changed.
   To revert: delete DOORFIX and DOORFIX_MARKER nodes; UNHIDE the original WALL.
   Intended for the exact 3ds Max project exported as VERSION11.fbx.
   This is a trial door-hole repair, NOT a fully validated all-doors navigation environment.
*/
(
  local orig = getNodeByName "DQ1F3D_WALL_SOLID_001"
  local prior = getNodeByName "DQ1F3D_WALL_DOORFIX_001"
  local priorMarker = getNodeByName "DQ1F3D_DOORFIX_MARKER_001"
  local ok = true
  if orig == undefined then
  (
    messageBox "Cannot find DQ1F3D_WALL_SOLID_001. Open the correct VERSION11.max scene first." title:"Door fix: scene mismatch"
    ok = false
  )
  if (prior != undefined) or (priorMarker != undefined) then
  (
    messageBox "Door-fix copy already exists. This script will not run twice." title:"Door fix: already applied"
    ok = false
  )
  if ok do
  (
    local shp = orig.baseObject
    if not (isKindOf shp SplineShape) then
    (
      messageBox "Original base object is not SplineShape. Aborting without edits." title:"Door fix: wrong object type"
      ok = false
    )
    if ok do
    (
      if (numSplines shp != 142) then
      (
        messageBox ("Original spline count changed: " + (numSplines shp as string) + " (expected 142). No changes made.") title:"Door fix: topology mismatch"
        ok = false
      )
    )
    if ok do
    (
      if (numKnots shp 97 != 4) then
      (
        messageBox "Door wall spline #97 no longer has 4 knots. No changes made." title:"Door fix: topology mismatch"
        ok = false
      )
    )
    if ok do
    (
      local corner = getKnotPoint shp 97 1
      if ((distance corner [279173.111,510491.503,0.0]) > 3.0) then
      (
        messageBox "Spline #97 does not match the uploaded FBX. Refusing to edit a different wall." title:"Door fix: coordinates mismatch"
        ok = false
      )
    )
    if ok do
    (
      if (queryBox "Create a COPY of DQ1F3D_WALL_SOLID_001 with ONE 1-metre door opening?\nThe original wall node will be HIDDEN (not deleted).\nPlease save a backup before proceeding." title:"VERSION11 - Door Opening Fix") then
      (
        undo "Create corrected door wall (copy)" on
        (
          clearSelection()
          local cloneWall = copy orig
          cloneWall.name = "DQ1F3D_WALL_DOORFIX_001"
          local sh = cloneWall.baseObject
          local k = 0
          deleteSpline sh 97
          addNewSpline sh
          k = numSplines sh
          addKnot sh k #corner #line [279204.089,509913.415,0.0]
          addKnot sh k #corner #line [279134.656,509909.146,0.0]
          addKnot sh k #corner #line [279173.111,510491.503,0.0]
          close sh k
          addNewSpline sh
          k = numSplines sh
          addKnot sh k #corner #line [279108.523,508283.126,0.0]
          addKnot sh k #corner #line [279068.283,508863.102,0.0]
          addKnot sh k #corner #line [279143.606,508867.733,0.0]
          close sh k
          updateShape sh
          cloneWall.wirecolor = (color 85 215 116)
          cloneWall.isHidden = false
          orig.isHidden = true
          local marker = point name:"DQ1F3D_DOORFIX_MARKER_001" pos:[279136.029,509388.249,1300.0] size:230.0 cross:true box:true
          marker.wirecolor = (color 240 70 60)
          select marker
          messageBox "Door opening created on a COPY.\n\nOriginal WALL is hidden, NOT deleted.\nOnly the 97th wall spline was replaced by two separated sections.\nA location marker is selected: press T (Top), then Z to zoom to the doorway.\n\nUndo: delete new DOORFIX and MARKER objects; unhide the original WALL." title:"VERSION11 - Door Fix Preview"
        )
      )
    )
  )
)