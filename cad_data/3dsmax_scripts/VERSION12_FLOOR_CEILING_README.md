# VERSION12 floor and ceiling preview — 3ds Max 2027

## Purpose
Create two **new, non-destructive** trial slab objects from the curved first-floor CAD contour in `JZ-1F_t3 (2).dxf` (modelspace closed LWPOLYLINE, handle `15D6`). The closed polygon is valid, area approximately 4,664.5 m² if CAD units are mm. This is a **candidate footprint**, not a verified structural or ceiling design.

## Run
1. Open the **pre-door-fix** `VERSION11.max` and use **File > Save As** to create `VERSION12.max`.
2. Download `cad_data/3dsmax_scripts/VERSION12_FLOOR_CEILING_PREVIEW.ms`.
3. In 3ds Max select **Scripting > Run Script** and choose this .ms file; confirm **Yes**.
4. Press **T** to inspect the top view and check the blue floor's curved outline matches the intended built area.

## New objects
- `DQ1F_SLAB_FLOOR_PREVIEW_001`: visible blue preview, Z -200 to 0.
- `DQ1F_SLAB_CEILING_PREVIEW_001`: hidden orange preview, Z 2800 to 3000.

These Z coordinates are **trial values**. The previously generated wall height was 2800, but the real structural floor/soffit height and slab thickness have NOT been established.

To show the ceiling, open **F11** MAXScript Listener and evaluate:
```maxscript
(getNodeByName "DQ1F_SLAB_CEILING_PREVIEW_001").isHidden = false
```
To hide it again, set `isHidden = true`.

If the footprint is wrong, **Ctrl+Z immediately**, or delete **only** these two `SLAB_PREVIEW` objects. The original scene objects are not modified.

## Important checks before using in Gazebo
- The source candidate contour covers most of the main building but leaves several structure/column elements outside its footprint; verify whether these are exterior features or omitted floor regions.
- Confirm the actual CAD unit scale.
- Identify courtyards, outdoor voids and slab openings. A single solid slab may otherwise cover areas that should remain uncovered.
- Confirm the real ceiling/underside elevation, floor thickness, material, and collisions.

The code is statically checked against Autodesk's documented SplineShape and Extrude APIs, but it has **not been executed in 3ds Max**.
