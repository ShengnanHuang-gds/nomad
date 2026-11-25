/* VERSION31 - JZ1F label-only overlap repair.
   Run AFTER VERSION31_JZ1F_SEMANTIC_SANITARY.ms. CAD units nominal mm.
   Does not change walls, furniture, fixtures, doors, windows or slabs.
   Uses projected mesh triangles, not whole-building wall bounding boxes.
   Conservative local search; ambiguous wall anchors remain for manual review.
   Undo once to restore all label changes. No geometry is created or deleted. */
(
    local previewOnly = false
    local clearance = 65.0
    local stepSize = 125.0
    local maxShift = 1500.0
    local factors = #(1.0, 0.85, 0.70, 0.55)
    local minTextSize = 110.0
    local patterns = #("DQ1F3D_WALL*", "DQ1F3D_MASONRY*", "DQ1F3D_PREFAB*", "DQ1F3D_GLASS_PARTITIONS*", "DQ1F3D_CONCRETE_COLUMNS*", "DQ1F3D_STRUCT_COMPONENTS*", "DQ1F_SAFE_DW*", "DQ1F_FURNPREV*", "JZ1F_STALL*", "JZ1F_TOILET*", "JZ1F_BASIN*", "JZ1F_URINAL*", "JZ1F_SINK*", "JZ1F_UTILITY_SINK*", "JZ1F_TOTO*")
    fn hitRect a b = (a[1] <= b[3] and a[3] >= b[1] and a[2] <= b[4] and a[4] >= b[2])
    fn boxRect b = #(b[1].x,b[1].y,b[2].x,b[2].y)
    fn padded r p = #(r[1]-p,r[2]-p,r[3]+p,r[4]+p)
    fn rectCenter r = [(r[1]+r[3])/2.0,(r[2]+r[4])/2.0,0]
    fn movedRect r d = #(r[1]+d.x,r[2]+d.y,r[3]+d.x,r[4]+d.y)
    fn triRect t r = (
        if not (hitRect t[1] r) then false else (
            -- Separating axis theorem in XY: rectangle axes handled by bounds.
            local mid = rectCenter r
            local hx = (r[3]-r[1])/2.0
            local hy = (r[4]-r[2])/2.0
            local pts = #(t[2]-mid,t[3]-mid,t[4]-mid)
            local separated = false
            for k = 1 to 3 while not separated do (
                local j = if k == 3 then 1 else k+1
                local e = pts[j]-pts[k]
                local ax = -e.y
                local ay = e.x
                local p1 = pts[1].x*ax+pts[1].y*ay
                local p2 = pts[2].x*ax+pts[2].y*ay
                local p3 = pts[3].x*ax+pts[3].y*ay
                local rad = hx*(abs ax)+hy*(abs ay)
                if ((amin #(p1,p2,p3)) > rad or (amax #(p1,p2,p3)) < -rad) do separated = true
            )
            not separated
        )
    )
    fn blocked r tris = (
        for t in tris do (if (triRect t r) do return true)
        false
    )
    fn bError verts b = (
        local mn = copy verts[1]; local mx = copy verts[1]
        for p in verts do (
            mn = [amin #(mn.x,p.x),amin #(mn.y,p.y),amin #(mn.z,p.z)]
            mx = [amax #(mx.x,p.x),amax #(mx.y,p.y),amax #(mx.z,p.z)]
        )
        (distance mn b[1])+(distance mx b[2])
    )
    fn meshTris n = (
        local m = in coordsys world (snapshotAsMesh n)
        if m.numverts < 3 do return #()
        local b = nodeGetBoundingBox n (matrix3 1)
        local raw = for i = 1 to m.numverts collect (getVert m i)
        local tm = n.objectTransform
        local converted = for v in raw collect (v*tm)
        -- Accommodate snapshot coordinate convention; validate against world bounds.
        local er = bError raw b; local ec = bError converted b
        local vs = if er <= ec then raw else converted
        if (amin #(er,ec)) > 10.0 do throw ("Cannot validate mesh coordinates: " + n.name)
        local out = #()
        for i = 1 to m.numfaces do (
            local f = getFace m i
            local a = vs[f.x as integer]; local c = vs[f.y as integer]; local d = vs[f.z as integer]
            local r = #(amin #(a.x,c.x,d.x),amin #(a.y,c.y,d.y),amax #(a.x,c.x,d.x),amax #(a.y,c.y,d.y))
            append out #(r,a,c,d)
        )
        out
    )
    fn nearTris tris r = (for t in tris where (hitRect t[1] r) collect t)
    fn supported r tris = (
        local ok = true
        for x in #(r[1],(r[1]+r[3])/2.0,r[3]) while ok do (
            for y in #(r[2],(r[2]+r[4])/2.0,r[4]) while ok do (
                if not (blocked #(x,y,x,y) tris) do ok = false
            )
        )
        ok
    )
    fn othersHit r nodes rects currentNode = (
        for i = 1 to nodes.count where nodes[i] != currentNode do (if hitRect r rects[i] do return true)
        false
    )
    fn pathClear a b tris = (
        -- conservative bounding rectangle of path from original insertion point
        local r = #(amin #(a.x,b.x),amin #(a.y,b.y),amax #(a.x,b.x),amax #(a.y,b.y))
        not (blocked r tris)
    )
    local labels = for n in objects where (matchPattern n.name pattern:"JZ1F_LABEL_*" and (getUserProp n "JZ1F_ADDON") == "JZ1F_V1" and isProperty n #size) collect n
    local floorNode = getNodeByName "DQ1F_SLAB_FLOOR_PREVIEW_001"
    local obstacles = #(); local structural = #()
    for n in geometry where not n.isHidden do (
        local matches = false
        for p in patterns while not matches do (if matchPattern n.name pattern:p do matches = true)
        if matches and not (matchPattern n.name pattern:"DQ1F3D_WALL*MARKER*") do (
            append obstacles n
            if (matchPattern n.name pattern:"DQ1F3D_*") do append structural n
        )
    )
    if labels.count == 0 or floorNode == undefined or structural.count == 0 then (
        messageBox "Required VERSION31 floor, walls or JZ1F labels not found. No changes made." title:"JZ1F label repair"
    ) else (
        local obs = #(); local walls = #(); local floors = #(); local valid = true
        try (
            floors = meshTris floorNode
            for n in obstacles do (
                local ts = meshTris n
                join obs ts
                if (findItem structural n) > 0 do join walls ts
            )
            if floors.count == 0 or walls.count == 0 do throw "Missing floor/wall triangles."
        ) catch (valid = false; format "Geometry validation failed: %\n" (getCurrentException()))
        if not valid then (messageBox "Could not validate geometry. No changes made. See MAXScript Listener (F11)." title:"JZ1F label repair") else (
            local rects = for n in labels collect (boxRect (nodeGetBoundingBox n (matrix3 1)))
            local changed = #(); local unresolved = #(); local already = 0
            undo "JZ1F label overlap repair" on (
                with redraw off (
                    for i = 1 to labels.count do (
                        local n = labels[i]
                        local origPos = in coordsys world (copy n.pos)
                        local origSize = n.size
                        local original = rects[i]
                        local near = padded original (maxShift + clearance + origSize)
                        local ot = nearTris obs near
                        local wt = nearTris walls near
                        local ft = nearTris floors near
                        local r0 = padded original clearance
                        if not (blocked r0 ot) and not (othersHit r0 labels rects n) and (supported original ft) then (already += 1) else (
                            local found = false; local bestPos = origPos; local bestSize = origSize; local bestRect = original
                            local anchor = [origPos.x,origPos.y,0]
                            local anchorBlocked = blocked #(anchor.x,anchor.y,anchor.x,anchor.y) wt
                            try (
                                for fac in factors while not found do (
                                    local proposed = amax #(amin #(minTextSize,origSize),origSize*fac)
                                    if proposed <= origSize do (
                                        n.size = proposed
                                        local base = boxRect (nodeGetBoundingBox n (matrix3 1))
                                        local center = rectCenter base
                                        -- Search smallest displacement first; do not cross a wall from CAD anchor.
                                        local rings = (maxShift/stepSize) as integer
                                        for ring = 0 to rings while not found do (
                                            for dir = 0 to 15 while not found do (
                                                if ring > 0 or dir == 0 do (
                                                    local ang = dir*22.5
                                                    local d = [ring*stepSize*cos(ang),ring*stepSize*sin(ang),0]
                                                    local rr = movedRect base d
                                                    local rp = padded rr clearance
                                                    local target = center+d
                                                    local routeOK = if anchorBlocked then (ring == 0) else (pathClear anchor target wt)
                                                    if routeOK and not (blocked rp ot) and not (othersHit rp labels rects n) and (supported rr ft) do (
                                                        found = true; bestPos = origPos+d; bestSize = proposed; bestRect = rr
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            ) catch (found = false; format "Label error %: %\n" n.name (getCurrentException()))
                            n.size = origSize
                            in coordsys world (n.pos = origPos)
                            if found then (
                                if not previewOnly do (
                                    n.size = bestSize
                                    in coordsys world (n.pos = bestPos)
                                )
                                rects[i] = bestRect
                                append changed n
                                format "FIX %: % -> %, size % -> %\n" n.name origPos bestPos origSize bestSize
                            ) else (
                                append unresolved n
                                format "REVIEW %: no verified local placement (anchor in wall: %)\n" n.name anchorBlocked
                            )
                        )
                    )
                )
            )
            format "JZ1F repair: % labels, % clear, % fixed/planned, % review, previewOnly=%\n" labels.count already changed.count unresolved.count previewOnly
            if unresolved.count > 0 do select unresolved
            redrawViews()
            messageBox ("Already clear: " + (already as string) + "\nFixed/planned: " + (changed.count as string) + "\nManual review: " + (unresolved.count as string) + "\nUnresolved labels selected. Details: F11 Listener.") title:"JZ1F label repair"
        )
    )
)
