/* VERSION12: NON-DESTRUCTIVE FLOOR + CEILING PREVIEW for the original pre-doorfix VERSION11.max
   Source: JZ-1F_t3 (2).dxf, modelspace LWPOLYLINE handle 15D6.
   Curved bulges flattened with max sagitta <=40 drawing units, area ~4664.5 sqm if mm.
   CAUTION: this closed boundary is a candidate, not verified final architectural slab.
   Do not treat 2800 (ceiling level) or 200 (slab thickness) as verified building dimensions.
   Only two new objects are created. Existing walls, columns, doors and groups stay unchanged.
*/
(
  local floorName = "DQ1F_SLAB_FLOOR_PREVIEW_001"
  local ceilingName = "DQ1F_SLAB_CEILING_PREVIEW_001"
  local floorTop = 0.0
  local thickness = 200.0
  local ceilingUnderside = 2800.0
  local footprint = #(
    [309721.439, 546875.895, 0.0],
    [277821.393, 560783.266, 0.0],
    [275907.715, 556147.103, 0.0],
    [274202.986, 551430.105, 0.0],
    [272710.606, 546641.685, 0.0],
    [272979.596, 546564.219, 0.0],
    [272946.638, 546449.275, 0.0],
    [271917.509, 545847.928, 0.0],
    [271027.032, 545055.604, 0.0],
    [270269.684, 544064.435, 0.0],
    [269704.174, 542952.594, 0.0],
    [269349.167, 541756.784, 0.0],
    [268656.610, 538607.886, 0.0],
    [270635.762, 538203.219, 0.0],
    [269596.926, 532361.324, 0.0],
    [268868.109, 526472.713, 0.0],
    [268451.344, 520553.825, 0.0],
    [268347.795, 514621.187, 0.0],
    [268557.751, 508691.361, 0.0],
    [269080.626, 502780.903, 0.0],
    [269914.961, 496906.313, 0.0],
    [277215.709, 498114.048, 0.0],
    [278241.136, 492872.997, 0.0],
    [279531.968, 487690.926, 0.0],
    [281084.859, 482581.264, 0.0],
    [282895.784, 477557.256, 0.0],
    [276008.052, 474851.826, 0.0],
    [278304.551, 469389.461, 0.0],
    [280885.974, 464055.834, 0.0],
    [283745.135, 458865.792, 0.0],
    [286874.073, 453833.786, 0.0],
    [290264.076, 448973.826, 0.0],
    [293905.707, 444299.443, 0.0],
    [297788.826, 439823.650, 0.0],
    [301902.623, 435558.909, 0.0],
    [306235.643, 431517.095, 0.0],
    [310775.824, 427709.458, 0.0],
    [315510.524, 424146.602, 0.0],
    [320426.562, 420838.445, 0.0],
    [325510.251, 417794.197, 0.0],
    [342676.101, 448066.128, 0.0],
    [338667.479, 450480.846, 0.0],
    [334811.907, 453133.106, 0.0],
    [331123.445, 456013.238, 0.0],
    [327615.541, 459110.741, 0.0],
    [324300.986, 462414.321, 0.0],
    [321191.865, 465911.931, 0.0],
    [318299.514, 469590.820, 0.0],
    [315961.498, 472937.452, 0.0],
    [313803.102, 476402.649, 0.0],
    [311830.324, 479976.780, 0.0],
    [310048.649, 483649.912, 0.0],
    [308409.993, 482905.053, 0.0],
    [306927.760, 486396.331, 0.0],
    [305614.413, 489954.583, 0.0],
    [304472.967, 493571.645, 0.0],
    [303506.040, 497239.217, 0.0],
    [302431.828, 502740.830, 0.0],
    [301333.053, 502557.914, 0.0],
    [300977.596, 504935.798, 0.0],
    [302049.303, 505073.862, 0.0],
    [301984.465, 505497.438, 0.0],
    [301818.736, 506625.054, 0.0],
    [303644.127, 506831.237, 0.0],
    [303260.391, 511367.593, 0.0],
    [303143.679, 515918.653, 0.0],
    [303294.395, 520468.715, 0.0],
    [303712.018, 525002.076, 0.0],
    [304395.108, 529503.094, 0.0],
    [305341.307, 533956.237, 0.0],
    [306547.350, 538346.139, 0.0],
    [308009.075, 542657.651, 0.0]
  )
  fn makePreviewSlab nm z h rgb vertices =
  (
    local shp = splineShape name:nm
    addNewSpline shp
    for p in vertices do addKnot shp 1 #corner #line [p.x,p.y,z]
    close shp 1
    updateShape shp
    addModifier shp (Extrude amount:h capStart:true capEnd:true)
    shp.wirecolor = rgb
    shp
  )
  if (getNodeByName "DQ1F3D_WALL_SOLID_001") == undefined then
  (
    messageBox "Original wall object not found. Open your pre-doorfix VERSION11.max scene. Nothing changed." title:"Slab preview: wrong scene"
  )
  else if ((getNodeByName floorName) != undefined or (getNodeByName ceilingName) != undefined) then
  (
    messageBox "Slab previews already exist. Nothing changed. Do not run twice." title:"Slab preview: already exists"
  )
  else if (queryBox "Create 2 NEW, independent slab PREVIEWS from JZ-1F CAD candidate contour?\n\nFloor: -200..0 (visible)\nCeiling: 2800..3000 (hidden)\n\nThe real floor boundary, ceiling elevation and slab thickness are UNVERIFIED. No original walls or columns will be edited. Save your .max backup first." title:"VERSION12 Floor and Ceiling Preview") then
  (
    local newFloor = undefined
    local newCeiling = undefined
    local successful = false
    local err = ""
    undo "Create VERSION12 slab previews" on
    (
      try
      (
        newFloor = makePreviewSlab floorName (floorTop-thickness) thickness (color 50 160 210) footprint
        newCeiling = makePreviewSlab ceilingName ceilingUnderside thickness (color 245 184 70) footprint
        newFloor.isHidden = false
        newCeiling.isHidden = true
        select newFloor
        redrawViews()
        successful = true
      )
      catch
      (
        err = getCurrentException() as string
        if newFloor != undefined do (try(delete newFloor)catch())
        if newCeiling != undefined do (try(delete newCeiling)catch())
      )
    )
    if successful then
      messageBox "Blue FLOOR preview created. Orange CEILING preview created but hidden.\n\nUse Top (T) to inspect the boundary. To show ceiling: F11, run:\n(getNodeByName \"DQ1F_SLAB_CEILING_PREVIEW_001\").isHidden = false\n\nDelete only these two SLAB_PREVIEW objects to remove. No old geometry was modified." title:"Preview done"
    else
      messageBox ("Preview failed and new objects were removed. Error: " + err) title:"Preview failed"
  )
)
