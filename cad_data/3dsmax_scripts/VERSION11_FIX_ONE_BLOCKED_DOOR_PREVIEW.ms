/* DQ-1F (VERSION11.fbx) - Non-destructive single blocked door opening fix - V2
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
    if not (isKindOf orig.baseObject SplineShape) then
    (
      messageBox "Original base object is not an Editable Spline. Nothing changed." title:"Door fix V2: wrong base type"
      ok = false
    )
  )
  if ok do
  (
    if orig.modifiers.count != 1 then
    (
      messageBox "Expected exactly one Extrude modifier. Nothing changed." title:"Door fix V2: modifier stack changed"
      ok = false
    )
    else
    (
      if not (isKindOf orig.modifiers[1] Extrude) then
      (
        messageBox "Expected Extrude modifier. Nothing changed." title:"Door fix V2: unexpected modifier"
        ok = false
      )
    )
  )
  if ok do
  (
    if (queryBox "Save your MAX scene first.\n\nCreate a COPY with one trial door opening? The original WALL is hidden only if creation succeeds." title:"VERSION11 Door Fix V2") then
    (
      local newWall = undefined
      local markerObj = undefined
      local wasHidden = orig.isHidden
      local done = false
      local errorInfo = ""
      local oldAmount = orig.modifiers[1].amount
      local oldCapStart = orig.modifiers[1].capStart
      local oldCapEnd = orig.modifiers[1].capEnd
      undo "Door opening preview V2" on
      (
        try
        (
          clearSelection()
          newWall = copy orig
          newWall.name = "DQ1F3D_WALL_DOORFIX_001"
          newWall.isHidden = true
          -- Spline API needs a shape NODE without the Extrude modifier above it.
          -- Only remove Extrude from the COPY; the original stays untouched.
          deleteModifier newWall 1
          if not (isKindOf newWall.baseObject SplineShape) do
            throw "Copied shape is no longer an Editable Spline."
          local count = numSplines newWall
          if count != 142 do
            throw ("Expected 142 splines; found " + (count as string) + ".")
          if (numKnots newWall 97) != 4 do
            throw "Spline 97 no longer has four knots."
          local corner = getKnotPoint newWall 97 1
          if (distance corner [279173.111,510491.503,0.0]) > 3.0 do
            throw "Spline 97 coordinates do not match the target geometry."
          deleteSpline newWall 97
          addNewSpline newWall
          local k = numSplines newWall
          addKnot newWall k #corner #line [279204.089,509913.415,0.0]
          addKnot newWall k #corner #line [279134.656,509909.146,0.0]
          addKnot newWall k #corner #line [279173.111,510491.503,0.0]
          close newWall k
          addNewSpline newWall
          k = numSplines newWall
          addKnot newWall k #corner #line [279108.523,508283.126,0.0]
          addKnot newWall k #corner #line [279068.283,508863.102,0.0]
          addKnot newWall k #corner #line [279143.606,508867.733,0.0]
          close newWall k
          updateShape newWall
          addModifier newWall (Extrude amount:oldAmount capStart:oldCapStart capEnd:oldCapEnd)
          newWall.wirecolor = (color 85 215 116)
          local markerPos = [279136.029,509388.249,1300.0] * orig.objectTransform
          markerObj = point name:"DQ1F3D_DOORFIX_MARKER_001" pos:markerPos size:230.0 cross:true box:true
          markerObj.wirecolor = (color 240 70 60)
          newWall.isHidden = false
          orig.isHidden = true
          select markerObj
          done = true
        )
        catch
        (
          errorInfo = getCurrentException() as string
          if markerObj != undefined do (try(delete markerObj)catch())
          if newWall != undefined do (try(delete newWall)catch())
          orig.isHidden = wasHidden
        )
      )
      if done then
      (
        messageBox "Created a one-door corrected COPY. Original WALL is hidden, not deleted.\nPress T then Z to inspect the selected marker.\nTo undo, delete DOORFIX and MARKER and unhide WALL." title:"VERSION11 Door Fix V2: success"
      )
      else
      (
        messageBox ("Aborted safely. Original WALL unchanged.\n\nError: " + errorInfo) title:"VERSION11 Door Fix V2: failed"
      )
    )
  )
)
