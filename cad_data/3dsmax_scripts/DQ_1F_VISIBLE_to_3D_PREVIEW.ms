/* DQ-1F 3D geometry preview (generated from DQ_1F_MAIN_ALL_RECOMMENDED_VISIBLE.dxf)
   3ds Max 2027 / MAXScript - self-contained, no external DXF or plugin required.
   Source coordinates are preserved. Coordinate units assumed millimetres: verify scale.
   DO NOT use as a validated collision map; door/window openings are NOT cut automatically.
   Open/unmatched WALL line panels are created HIDDEN for inspection only.
   This script never edits, moves, deletes or hides the ORIGINAL objects.
*/
(
  local wallHeight = 2800.0  -- CAD coordinate units (adjust after checking real height)
  local columnHeight = 2800.0
  local makeReviewWalls = true
  local makeReference2D = true
  local proceed = true
  if ((getNodeByName "Layer:WALL" != undefined) or (getNodeByName "Layer:WALL001" != undefined)) do
  (
    proceed = queryBox "Your scene already contains WALL/WALL001 objects. This script ADDS new objects (it does not replace old walls). Overlapping walls are possible. Continue?" title:"DQ1F 3D Preview - duplicate wall warning"
  )
  if proceed then
  (
    undo "DQ1F 3D preview creation" on
    (
      local made = #()
      local k = 0
      local sh = undefined
      -- WALL: 142 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_WALL_SOLID_")
      sh.wirecolor = (color 178 178 178)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [324907.029,437650.178,0.0]
      addKnot sh k #corner #line [324790.730,437487.467,0.0]
      addKnot sh k #corner #line [324629.556,437605.915,0.0]
      addKnot sh k #corner #line [324745.824,437768.583,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [324745.824,437768.583,0.0]
      addKnot sh k #corner #line [324629.556,437605.915,0.0]
      addKnot sh k #corner #line [324468.363,437724.375,0.0]
      addKnot sh k #corner #line [324584.603,437886.999,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [337457.451,439876.724,0.0]
      addKnot sh k #corner #line [337630.107,439775.743,0.0]
      addKnot sh k #corner #line [336520.365,437818.696,0.0]
      addKnot sh k #corner #line [336346.389,437917.349,0.0]
      addKnot sh k #corner #line [337358.790,439702.733,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [337630.107,439775.743,0.0]
      addKnot sh k #corner #line [337457.451,439876.724,0.0]
      addKnot sh k #corner #line [337505.458,439961.384,0.0]
      addKnot sh k #corner #line [337679.434,439862.731,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [324468.363,437724.375,0.0]
      addKnot sh k #corner #line [324307.198,437842.815,0.0]
      addKnot sh k #corner #line [324423.407,438005.398,0.0]
      addKnot sh k #corner #line [324584.603,437886.999,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316425.875,453596.694,0.0]
      addKnot sh k #corner #line [316497.877,453666.089,0.0]
      addKnot sh k #corner #line [316668.568,453488.983,0.0]
      addKnot sh k #corner #line [316596.565,453419.589,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [320975.027,453283.794,0.0]
      addKnot sh k #corner #line [320488.581,452776.701,0.0]
      addKnot sh k #corner #line [320345.211,452916.152,0.0]
      addKnot sh k #corner #line [320830.698,453422.247,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296045.112,535925.528,0.0]
      addKnot sh k #corner #line [296044.478,535925.681,0.0]
      addKnot sh k #corner #line [296067.940,536022.890,0.0]
      addKnot sh k #corner #line [296092.034,536119.946,0.0]
      addKnot sh k #corner #line [296576.097,536003.113,0.0]
      addKnot sh k #corner #line [296529.173,535808.696,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294382.531,509201.927,0.0]
      addKnot sh k #corner #line [293883.475,509165.488,0.0]
      addKnot sh k #corner #line [293883.427,509166.134,0.0]
      addKnot sh k #corner #line [293869.398,509364.993,0.0]
      addKnot sh k #corner #line [294367.967,509401.396,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [299311.403,538550.745,0.0]
      addKnot sh k #corner #line [296907.061,539231.423,0.0]
      addKnot sh k #corner #line [296925.996,539298.821,0.0]
      addKnot sh k #corner #line [296961.406,539423.898,0.0]
      addKnot sh k #corner #line [299365.882,538743.182,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313261.826,476756.386,0.0]
      addKnot sh k #corner #line [313521.142,476294.916,0.0]
      addKnot sh k #corner #line [313348.685,476193.556,0.0]
      addKnot sh k #corner #line [313087.468,476658.408,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313348.685,476193.556,0.0]
      addKnot sh k #corner #line [313521.142,476294.916,0.0]
      addKnot sh k #corner #line [313619.138,476120.526,0.0]
      addKnot sh k #corner #line [307415.483,472474.401,0.0]
      addKnot sh k #corner #line [307314.143,472646.825,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [303406.979,476682.319,0.0]
      addKnot sh k #corner #line [302960.793,476457.973,0.0]
      addKnot sh k #corner #line [302871.121,476635.322,0.0]
      addKnot sh k #corner #line [302870.925,476635.223,0.0]
      addKnot sh k #corner #line [302870.354,476636.359,0.0]
      addKnot sh k #corner #line [303317.136,476861.003,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287111.796,513283.706,0.0]
      addKnot sh k #corner #line [291373.809,513316.767,0.0]
      addKnot sh k #corner #line [291371.355,513634.053,0.0]
      addKnot sh k #corner #line [291471.352,513634.827,0.0]
      addKnot sh k #corner #line [291474.580,513217.546,0.0]
      addKnot sh k #corner #line [287112.572,513183.709,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [291363.619,514634.023,0.0]
      addKnot sh k #corner #line [291362.052,514836.527,0.0]
      addKnot sh k #corner #line [291462.049,514837.301,0.0]
      addKnot sh k #corner #line [291463.616,514634.797,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298961.098,470003.905,0.0]
      addKnot sh k #corner #line [302716.878,472017.268,0.0]
      addKnot sh k #corner #line [302587.466,472258.688,0.0]
      addKnot sh k #corner #line [302675.602,472305.932,0.0]
      addKnot sh k #corner #line [302852.258,471976.379,0.0]
      addKnot sh k #corner #line [299008.345,469915.770,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302115.018,473140.046,0.0]
      addKnot sh k #corner #line [301998.810,473356.834,0.0]
      addKnot sh k #corner #line [302086.946,473404.079,0.0]
      addKnot sh k #corner #line [302203.154,473187.291,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [314412.334,449545.092,0.0]
      addKnot sh k #corner #line [317480.596,452502.334,0.0]
      addKnot sh k #corner #line [317290.511,452699.562,0.0]
      addKnot sh k #corner #line [317362.514,452768.957,0.0]
      addKnot sh k #corner #line [317621.991,452499.728,0.0]
      addKnot sh k #corner #line [314481.730,449473.090,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317746.357,444512.995,0.0]
      addKnot sh k #corner #line [317376.421,444092.290,0.0]
      addKnot sh k #corner #line [317226.228,444224.358,0.0]
      addKnot sh k #corner #line [317596.163,444645.063,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290193.408,539552.293,0.0]
      addKnot sh k #corner #line [294293.658,538391.491,0.0]
      addKnot sh k #corner #line [294368.279,538655.049,0.0]
      addKnot sh k #corner #line [294464.497,538627.807,0.0]
      addKnot sh k #corner #line [294362.635,538268.034,0.0]
      addKnot sh k #corner #line [290166.168,539456.075,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294707.704,539853.896,0.0]
      addKnot sh k #corner #line [294803.922,539826.654,0.0]
      addKnot sh k #corner #line [294736.915,539589.986,0.0]
      addKnot sh k #corner #line [294640.697,539617.228,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [322112.926,449781.695,0.0]
      addKnot sh k #corner #line [322508.964,450232.085,0.0]
      addKnot sh k #corner #line [322659.158,450100.016,0.0]
      addKnot sh k #corner #line [322263.119,449649.627,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300459.581,474099.729,0.0]
      addKnot sh k #corner #line [302057.007,474929.327,0.0]
      addKnot sh k #corner #line [302149.185,474751.835,0.0]
      addKnot sh k #corner #line [300551.758,473922.237,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290500.302,510303.719,0.0]
      addKnot sh k #corner #line [292297.052,510411.862,0.0]
      addKnot sh k #corner #line [292309.068,510212.223,0.0]
      addKnot sh k #corner #line [290512.318,510104.080,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305689.291,471459.852,0.0]
      addKnot sh k #corner #line [306122.301,471714.348,0.0]
      addKnot sh k #corner #line [306020.961,471886.773,0.0]
      addKnot sh k #corner #line [305587.951,471632.276,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313497.581,454356.861,0.0]
      addKnot sh k #corner #line [313065.348,453961.563,0.0]
      addKnot sh k #corner #line [313200.322,453813.977,0.0]
      addKnot sh k #corner #line [313632.555,454209.274,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305620.293,536972.537,0.0]
      addKnot sh k #corner #line [300809.160,538334.585,0.0]
      addKnot sh k #corner #line [300754.680,538142.148,0.0]
      addKnot sh k #corner #line [305565.798,536780.104,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [304839.526,534008.665,0.0]
      addKnot sh k #corner #line [298034.228,535651.181,0.0]
      addKnot sh k #corner #line [297987.303,535456.764,0.0]
      addKnot sh k #corner #line [304792.643,533814.238,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327896.199,442520.234,0.0]
      addKnot sh k #corner #line [329611.605,444920.147,0.0]
      addKnot sh k #corner #line [329774.333,444803.834,0.0]
      addKnot sh k #corner #line [328058.958,442403.899,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [319610.540,445722.982,0.0]
      addKnot sh k #corner #line [320930.565,447225.504,0.0]
      addKnot sh k #corner #line [321081.380,447094.143,0.0]
      addKnot sh k #corner #line [319760.791,445590.980,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311946.222,478689.330,0.0]
      addKnot sh k #corner #line [312205.671,478227.623,0.0]
      addKnot sh k #corner #line [312380.029,478325.600,0.0]
      addKnot sh k #corner #line [312122.527,478783.841,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294186.372,535447.937,0.0]
      addKnot sh k #corner #line [295644.672,535096.292,0.0]
      addKnot sh k #corner #line [295600.241,534901.273,0.0]
      addKnot sh k #corner #line [294141.900,535252.929,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [323774.003,438472.586,0.0]
      addKnot sh k #corner #line [326972.577,442947.625,0.0]
      addKnot sh k #corner #line [327133.613,442828.985,0.0]
      addKnot sh k #corner #line [323935.136,438354.081,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [278691.770,538107.509,0.0]
      addKnot sh k #corner #line [280455.496,537746.892,0.0]
      addKnot sh k #corner #line [280412.567,537551.531,0.0]
      addKnot sh k #corner #line [278648.890,537912.139,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311953.655,459825.772,0.0]
      addKnot sh k #corner #line [312977.907,460626.641,0.0]
      addKnot sh k #corner #line [313104.261,460471.557,0.0]
      addKnot sh k #corner #line [312078.411,459669.440,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287292.126,536698.910,0.0]
      addKnot sh k #corner #line [288556.040,536394.137,0.0]
      addKnot sh k #corner #line [288512.247,536198.965,0.0]
      addKnot sh k #corner #line [287248.291,536503.748,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [314243.338,453842.695,0.0]
      addKnot sh k #corner #line [315050.384,454590.147,0.0]
      addKnot sh k #corner #line [315118.549,454516.978,0.0]
      addKnot sh k #corner #line [314311.501,453769.524,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [295975.444,470593.633,0.0]
      addKnot sh k #corner #line [295307.021,470257.533,0.0]
      addKnot sh k #corner #line [295351.944,470168.191,0.0]
      addKnot sh k #corner #line [296022.464,470505.345,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284859.277,510910.775,0.0]
      addKnot sh k #corner #line [284110.776,510855.883,0.0]
      addKnot sh k #corner #line [284118.090,510756.150,0.0]
      addKnot sh k #corner #line [284864.251,510810.871,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292786.622,469997.584,0.0]
      addKnot sh k #corner #line [293858.814,470536.709,0.0]
      addKnot sh k #corner #line [293904.970,470447.987,0.0]
      addKnot sh k #corner #line [292832.763,469908.855,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [281815.765,509785.157,0.0]
      addKnot sh k #corner #line [283012.672,509872.934,0.0]
      addKnot sh k #corner #line [283018.609,509773.101,0.0]
      addKnot sh k #corner #line [281821.719,509685.325,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276379.799,510288.918,0.0]
      addKnot sh k #corner #line [278973.481,510479.130,0.0]
      addKnot sh k #corner #line [278978.590,510379.236,0.0]
      addKnot sh k #corner #line [276384.963,510189.028,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [288379.572,466774.241,0.0]
      addKnot sh k #corner #line [290702.981,467942.508,0.0]
      addKnot sh k #corner #line [290749.880,467854.160,0.0]
      addKnot sh k #corner #line [288426.421,466685.868,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [319159.141,446119.666,0.0]
      addKnot sh k #corner #line [320457.288,444992.659,0.0]
      addKnot sh k #corner #line [321776.089,443889.892,0.0]
      addKnot sh k #corner #line [321804.299,443608.308,0.0]
      addKnot sh k #corner #line [320404.115,444775.282,0.0]
      addKnot sh k #corner #line [319027.072,445969.472,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [323480.914,445660.493,0.0]
      addKnot sh k #corner #line [325210.147,444282.696,0.0]
      addKnot sh k #corner #line [326972.577,442947.625,0.0]
      addKnot sh k #corner #line [327727.297,442643.213,0.0]
      addKnot sh k #corner #line [325565.299,444260.637,0.0]
      addKnot sh k #corner #line [323452.707,445942.082,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316184.670,486217.120,0.0]
      addKnot sh k #corner #line [316648.295,485221.582,0.0]
      addKnot sh k #corner #line [316467.660,485135.726,0.0]
      addKnot sh k #corner #line [315919.820,486316.445,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316739.185,486688.794,0.0]
      addKnot sh k #corner #line [317280.515,485522.078,0.0]
      addKnot sh k #corner #line [317099.881,485436.222,0.0]
      addKnot sh k #corner #line [316639.873,486423.980,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316648.295,485221.582,0.0]
      addKnot sh k #corner #line [316866.009,484767.702,0.0]
      addKnot sh k #corner #line [316771.501,484504.462,0.0]
      addKnot sh k #corner #line [316467.660,485135.726,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317280.515,485522.078,0.0]
      addKnot sh k #corner #line [317590.041,484879.248,0.0]
      addKnot sh k #corner #line [317320.725,484975.904,0.0]
      addKnot sh k #corner #line [317099.881,485436.222,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [306353.951,538735.330,0.0]
      addKnot sh k #corner #line [305785.418,536821.851,0.0]
      addKnot sh k #corner #line [305620.293,536972.537,0.0]
      addKnot sh k #corner #line [306162.982,538794.751,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302646.319,514924.030,0.0]
      addKnot sh k #corner #line [302663.183,513860.592,0.0]
      addKnot sh k #corner #line [302863.080,513867.434,0.0]
      addKnot sh k #corner #line [302846.313,514925.581,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305193.445,477804.424,0.0]
      addKnot sh k #corner #line [306210.017,475841.252,0.0]
      addKnot sh k #corner #line [306128.240,475570.489,0.0]
      addKnot sh k #corner #line [305104.604,477535.896,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279182.743,541064.283,0.0]
      addKnot sh k #corner #line [278986.099,540266.607,0.0]
      addKnot sh k #corner #line [279180.742,540220.614,0.0]
      addKnot sh k #corner #line [279352.470,540918.640,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [278904.788,539052.774,0.0]
      addKnot sh k #corner #line [278691.770,538107.509,0.0]
      addKnot sh k #corner #line [278474.591,538051.152,0.0]
      addKnot sh k #corner #line [278710.145,539098.767,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284205.109,542827.384,0.0]
      addKnot sh k #corner #line [283475.037,540091.322,0.0]
      addKnot sh k #corner #line [283281.040,540139.956,0.0]
      addKnot sh k #corner #line [284012.672,542881.864,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [280025.977,544218.384,0.0]
      addKnot sh k #corner #line [279729.358,543153.076,0.0]
      addKnot sh k #corner #line [279922.612,543101.555,0.0]
      addKnot sh k #corner #line [280163.934,543971.467,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279613.495,541942.052,0.0]
      addKnot sh k #corner #line [279401.103,541112.636,0.0]
      addKnot sh k #corner #line [279182.743,541064.283,0.0]
      addKnot sh k #corner #line [279420.241,541993.573,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285696.495,542405.163,0.0]
      addKnot sh k #corner #line [284978.512,539714.409,0.0]
      addKnot sh k #corner #line [284784.515,539763.043,0.0]
      addKnot sh k #corner #line [285504.058,542459.643,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [282858.051,543208.745,0.0]
      addKnot sh k #corner #line [282117.059,540431.760,0.0]
      addKnot sh k #corner #line [281923.062,540480.394,0.0]
      addKnot sh k #corner #line [282665.614,543263.225,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [281292.438,540432.299,0.0]
      addKnot sh k #corner #line [280629.602,537607.567,0.0]
      addKnot sh k #corner #line [280455.496,537746.892,0.0]
      addKnot sh k #corner #line [281098.441,540480.933,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [278648.890,537912.139,0.0]
      addKnot sh k #corner #line [278379.325,536640.360,0.0]
      addKnot sh k #corner #line [278143.315,536484.477,0.0]
      addKnot sh k #corner #line [278474.591,538051.152,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [280629.602,537607.567,0.0]
      addKnot sh k #corner #line [280338.788,536239.721,0.0]
      addKnot sh k #corner #line [280142.841,536279.785,0.0]
      addKnot sh k #corner #line [280412.567,537551.531,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296345.254,470326.138,0.0]
      addKnot sh k #corner #line [297201.954,468766.957,0.0]
      addKnot sh k #corner #line [298087.489,467223.970,0.0]
      addKnot sh k #corner #line [297915.057,467122.643,0.0]
      addKnot sh k #corner #line [297003.097,468712.630,0.0]
      addKnot sh k #corner #line [296121.691,470319.755,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [295188.248,472548.323,0.0]
      addKnot sh k #corner #line [296200.069,470597.337,0.0]
      addKnot sh k #corner #line [295975.444,470593.633,0.0]
      addKnot sh k #corner #line [295009.557,472458.491,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300551.758,473922.237,0.0]
      addKnot sh k #corner #line [301010.053,473053.717,0.0]
      addKnot sh k #corner #line [300833.782,472959.224,0.0]
      addKnot sh k #corner #line [300328.128,473918.780,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302280.538,474932.732,0.0]
      addKnot sh k #corner #line [302772.753,473998.646,0.0]
      addKnot sh k #corner #line [302596.483,473904.153,0.0]
      addKnot sh k #corner #line [302149.185,474751.835,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [303689.265,475044.584,0.0]
      addKnot sh k #corner #line [303965.705,474524.688,0.0]
      addKnot sh k #corner #line [304076.585,473898.961,0.0]
      addKnot sh k #corner #line [303836.732,474342.087,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [301799.526,475872.637,0.0]
      addKnot sh k #corner #line [302280.538,474932.732,0.0]
      addKnot sh k #corner #line [302057.007,474929.327,0.0]
      addKnot sh k #corner #line [301620.843,475782.791,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300012.694,474974.174,0.0]
      addKnot sh k #corner #line [300459.581,474099.729,0.0]
      addKnot sh k #corner #line [300328.128,473918.780,0.0]
      addKnot sh k #corner #line [299834.011,474884.328,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [304980.510,472685.320,0.0]
      addKnot sh k #corner #line [305689.291,471459.853,0.0]
      addKnot sh k #corner #line [305415.526,471530.937,0.0]
      addKnot sh k #corner #line [304805.721,472588.098,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [297600.470,473761.249,0.0]
      addKnot sh k #corner #line [298630.406,471778.062,0.0]
      addKnot sh k #corner #line [298454.136,471683.569,0.0]
      addKnot sh k #corner #line [297421.787,473671.402,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269481.508,529315.084,0.0]
      addKnot sh k #corner #line [269323.503,527964.387,0.0]
      addKnot sh k #corner #line [269084.968,527990.860,0.0]
      addKnot sh k #corner #line [269214.296,529106.487,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296341.199,511561.683,0.0]
      addKnot sh k #corner #line [296469.292,509454.591,0.0]
      addKnot sh k #corner #line [296269.828,509439.959,0.0]
      addKnot sh k #corner #line [296132.018,511752.060,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296469.292,509454.591,0.0]
      addKnot sh k #corner #line [296693.615,506920.564,0.0]
      addKnot sh k #corner #line [296994.207,504394.450,0.0]
      addKnot sh k #corner #line [297370.794,501878.542,0.0]
      addKnot sh k #corner #line [297206.323,501648.435,0.0]
      addKnot sh k #corner #line [296813.861,504235.538,0.0]
      addKnot sh k #corner #line [296501.596,506833.541,0.0]
      addKnot sh k #corner #line [296269.828,509439.959,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290447.720,511284.329,0.0]
      addKnot sh k #corner #line [290500.302,510303.719,0.0]
      addKnot sh k #corner #line [290306.616,510191.880,0.0]
      addKnot sh k #corner #line [290247.941,511274.928,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292445.510,511378.346,0.0]
      addKnot sh k #corner #line [292502.642,510324.055,0.0]
      addKnot sh k #corner #line [292297.052,510411.862,0.0]
      addKnot sh k #corner #line [292245.731,511368.945,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292502.642,510324.055,0.0]
      addKnot sh k #corner #line [292572.376,509270.523,0.0]
      addKnot sh k #corner #line [292372.912,509255.895,0.0]
      addKnot sh k #corner #line [292309.068,510212.223,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290512.318,510104.080,0.0]
      addKnot sh k #corner #line [290577.732,509124.242,0.0]
      addKnot sh k #corner #line [290378.267,509109.614,0.0]
      addKnot sh k #corner #line [290306.616,510191.880,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293446.592,514852.778,0.0]
      addKnot sh k #corner #line [293461.577,513835.846,0.0]
      addKnot sh k #corner #line [293661.492,513842.023,0.0]
      addKnot sh k #corner #line [293646.587,514854.226,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284946.842,514786.853,0.0]
      addKnot sh k #corner #line [284979.034,513008.105,0.0]
      addKnot sh k #corner #line [285044.285,511230.262,0.0]
      addKnot sh k #corner #line [284849.154,511120.969,0.0]
      addKnot sh k #corner #line [284780.491,512952.645,0.0]
      addKnot sh k #corner #line [284746.848,514785.300,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287750.703,511157.406,0.0]
      addKnot sh k #corner #line [287884.961,508926.763,0.0]
      addKnot sh k #corner #line [287685.497,508912.135,0.0]
      addKnot sh k #corner #line [287550.924,511148.005,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [301551.460,506695.490,0.0]
      addKnot sh k #corner #line [301813.357,504577.716,0.0]
      addKnot sh k #corner #line [302128.648,502467.230,0.0]
      addKnot sh k #corner #line [301860.084,502625.305,0.0]
      addKnot sh k #corner #line [301562.159,504643.881,0.0]
      addKnot sh k #corner #line [301312.922,506669.045,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302929.141,511971.825,0.0]
      addKnot sh k #corner #line [303102.819,509277.717,0.0]
      addKnot sh k #corner #line [302903.487,509261.390,0.0]
      addKnot sh k #corner #line [302729.362,511962.424,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [319872.201,456918.319,0.0]
      addKnot sh k #corner #line [321033.830,455737.630,0.0]
      addKnot sh k #corner #line [322219.232,454580.812,0.0]
      addKnot sh k #corner #line [321936.400,454574.882,0.0]
      addKnot sh k #corner #line [320751.039,455737.349,0.0]
      addKnot sh k #corner #line [319589.566,456923.683,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294051.879,524051.726,0.0]
      addKnot sh k #corner #line [293925.542,522632.242,0.0]
      addKnot sh k #corner #line [293742.791,522850.961,0.0]
      addKnot sh k #corner #line [293852.818,524071.088,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276723.779,525636.720,0.0]
      addKnot sh k #corner #line [276622.064,524516.270,0.0]
      addKnot sh k #corner #line [276406.197,524336.323,0.0]
      addKnot sh k #corner #line [276544.095,525855.142,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [278417.244,525471.999,0.0]
      addKnot sh k #corner #line [278314.176,524351.680,0.0]
      addKnot sh k #corner #line [278115.105,524371.043,0.0]
      addKnot sh k #corner #line [278218.184,525491.361,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292351.857,524116.600,0.0]
      addKnot sh k #corner #line [292249.747,522996.188,0.0]
      addKnot sh k #corner #line [292050.671,523015.552,0.0]
      addKnot sh k #corner #line [292152.797,524135.961,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279631.215,525554.861,0.0]
      addKnot sh k #corner #line [279491.595,524036.210,0.0]
      addKnot sh k #corner #line [279309.537,524254.862,0.0]
      addKnot sh k #corner #line [279412.547,525375.187,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [291157.493,524232.769,0.0]
      addKnot sh k #corner #line [291055.293,523112.372,0.0]
      addKnot sh k #corner #line [290839.513,522932.416,0.0]
      addKnot sh k #corner #line [290978.071,524451.164,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269323.503,527964.387,0.0]
      addKnot sh k #corner #line [269167.756,526472.173,0.0]
      addKnot sh k #corner #line [268952.487,526734.244,0.0]
      addKnot sh k #corner #line [269084.968,527990.860,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305565.798,536780.104,0.0]
      addKnot sh k #corner #line [305351.876,536005.722,0.0]
      addKnot sh k #corner #line [305545.531,535955.692,0.0]
      addKnot sh k #corner #line [305785.400,536821.786,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305010.444,533864.563,0.0]
      addKnot sh k #corner #line [304420.092,531213.908,0.0]
      addKnot sh k #corner #line [304224.145,531253.969,0.0]
      addKnot sh k #corner #line [304792.643,533814.238,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [283068.605,510679.185,0.0]
      addKnot sh k #corner #line [283112.423,509880.106,0.0]
      addKnot sh k #corner #line [283012.672,509872.934,0.0]
      addKnot sh k #corner #line [282968.847,510671.869,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [281771.762,510584.078,0.0]
      addKnot sh k #corner #line [281815.765,509785.157,0.0]
      addKnot sh k #corner #line [281616.206,509771.798,0.0]
      addKnot sh k #corner #line [281568.004,510653.245,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276384.963,510189.028,0.0]
      addKnot sh k #corner #line [276515.485,508092.961,0.0]
      addKnot sh k #corner #line [276330.649,507878.868,0.0]
      addKnot sh k #corner #line [276180.174,510276.485,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279173.111,510491.503,0.0]
      addKnot sh k #corner #line [279205.159,509893.443,0.0]
      addKnot sh k #corner #line [279108.523,508283.126,0.0]
      addKnot sh k #corner #line [279066.899,508883.054,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [281821.719,509685.325,0.0]
      addKnot sh k #corner #line [281901.025,508487.919,0.0]
      addKnot sh k #corner #line [281716.188,508273.826,0.0]
      addKnot sh k #corner #line [281616.206,509771.798,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [283112.423,509880.106,0.0]
      addKnot sh k #corner #line [283197.544,508583.001,0.0]
      addKnot sh k #corner #line [283097.811,508575.687,0.0]
      addKnot sh k #corner #line [283018.609,509773.101,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276247.097,514719.376,0.0]
      addKnot sh k #corner #line [276289.933,512503.443,0.0]
      addKnot sh k #corner #line [276379.799,510288.918,0.0]
      addKnot sh k #corner #line [276180.174,510276.485,0.0]
      addKnot sh k #corner #line [276087.105,512596.405,0.0]
      addKnot sh k #corner #line [276045.551,514917.819,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [280146.981,514749.624,0.0]
      addKnot sh k #corner #line [280209.820,511968.527,0.0]
      addKnot sh k #corner #line [280009.960,511961.044,0.0]
      addKnot sh k #corner #line [279946.987,514748.072,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293994.255,470493.043,0.0]
      addKnot sh k #corner #line [294366.877,469784.805,0.0]
      addKnot sh k #corner #line [294277.512,469739.871,0.0]
      addKnot sh k #corner #line [293904.970,470447.987,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292832.763,469908.855,0.0]
      addKnot sh k #corner #line [293205.146,469200.658,0.0]
      addKnot sh k #corner #line [293065.796,469036.699,0.0]
      addKnot sh k #corner #line [292654.650,469817.871,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287415.517,468640.021,0.0]
      addKnot sh k #corner #line [288379.572,466774.241,0.0]
      addKnot sh k #corner #line [288248.727,466594.055,0.0]
      addKnot sh k #corner #line [287146.988,468728.857,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [289738.399,469808.023,0.0]
      addKnot sh k #corner #line [290010.666,469271.816,0.0]
      addKnot sh k #corner #line [290188.279,469363.766,0.0]
      addKnot sh k #corner #line [289827.236,470076.552,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292239.963,471065.871,0.0]
      addKnot sh k #corner #line [292786.622,469997.584,0.0]
      addKnot sh k #corner #line [292654.650,469817.871,0.0]
      addKnot sh k #corner #line [291971.434,471154.708,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293401.404,471649.872,0.0]
      addKnot sh k #corner #line [293994.255,470493.043,0.0]
      addKnot sh k #corner #line [293858.814,470536.709,0.0]
      addKnot sh k #corner #line [293312.062,471604.949,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [288426.421,466685.868,0.0]
      addKnot sh k #corner #line [289486.177,464739.304,0.0]
      addKnot sh k #corner #line [290587.017,462815.675,0.0]
      addKnot sh k #corner #line [290515.933,462541.910,0.0]
      addKnot sh k #corner #line [289359.842,464555.401,0.0]
      addKnot sh k #corner #line [288248.727,466594.055,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [292575.479,467210.713,0.0]
      addKnot sh k #corner #line [293949.292,464791.812,0.0]
      addKnot sh k #corner #line [293776.868,464690.472,0.0]
      addKnot sh k #corner #line [292400.124,467114.533,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285058.917,510923.009,0.0]
      addKnot sh k #corner #line [285192.192,508729.283,0.0]
      addKnot sh k #corner #line [284992.727,508714.654,0.0]
      addKnot sh k #corner #line [284864.251,510810.871,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [291961.578,536910.207,0.0]
      addKnot sh k #corner #line [291625.360,535456.867,0.0]
      addKnot sh k #corner #line [291312.958,533998.222,0.0]
      addKnot sh k #corner #line [291117.013,534038.291,0.0]
      addKnot sh k #corner #line [291430.144,535500.350,0.0]
      addKnot sh k #corner #line [291767.150,536957.090,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294391.921,536324.169,0.0]
      addKnot sh k #corner #line [294186.372,535447.937,0.0]
      addKnot sh k #corner #line [293969.364,535396.125,0.0]
      addKnot sh k #corner #line [294197.493,536371.052,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287586.961,537965.076,0.0]
      addKnot sh k #corner #line [287292.126,536698.910,0.0]
      addKnot sh k #corner #line [287075.403,536646.881,0.0]
      addKnot sh k #corner #line [287415.924,538109.185,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296067.940,536022.890,0.0]
      addKnot sh k #corner #line [295817.142,534953.218,0.0]
      addKnot sh k #corner #line [295644.672,535096.292,0.0]
      addKnot sh k #corner #line [295850.127,535972.546,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287248.291,536503.748,0.0]
      addKnot sh k #corner #line [286904.192,534899.776,0.0]
      addKnot sh k #corner #line [286707.764,534937.498,0.0]
      addKnot sh k #corner #line [287075.403,536646.881,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [288728.934,536251.412,0.0]
      addKnot sh k #corner #line [288373.780,534599.258,0.0]
      addKnot sh k #corner #line [288177.835,534639.328,0.0]
      addKnot sh k #corner #line [288512.247,536198.965,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294141.900,535252.929,0.0]
      addKnot sh k #corner #line [293762.273,533497.359,0.0]
      addKnot sh k #corner #line [293566.328,533537.428,0.0]
      addKnot sh k #corner #line [293969.364,535396.125,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296349.381,537156.592,0.0]
      addKnot sh k #corner #line [296067.940,536022.890,0.0]
      addKnot sh k #corner #line [295897.010,536166.973,0.0]
      addKnot sh k #corner #line [296156.112,537208.086,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [288535.623,541601.250,0.0]
      addKnot sh k #corner #line [287816.321,538899.890,0.0]
      addKnot sh k #corner #line [287646.691,539045.510,0.0]
      addKnot sh k #corner #line [288343.222,541655.857,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [289045.166,537613.453,0.0]
      addKnot sh k #corner #line [288728.934,536251.412,0.0]
      addKnot sh k #corner #line [288556.040,536394.137,0.0]
      addKnot sh k #corner #line [288850.739,537660.336,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [309253.747,459682.270,0.0]
      addKnot sh k #corner #line [310886.880,457658.785,0.0]
      addKnot sh k #corner #line [310795.211,457456.254,0.0]
      addKnot sh k #corner #line [308972.999,459716.631,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [312045.283,462118.867,0.0]
      addKnot sh k #corner #line [313197.134,460674.111,0.0]
      addKnot sh k #corner #line [312977.907,460626.641,0.0]
      addKnot sh k #corner #line [312010.920,461838.118,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310199.063,460421.417,0.0]
      addKnot sh k #corner #line [311165.746,459209.702,0.0]
      addKnot sh k #corner #line [311072.486,459007.364,0.0]
      addKnot sh k #corner #line [310041.508,460298.224,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310986.837,461037.382,0.0]
      addKnot sh k #corner #line [311953.655,459825.772,0.0]
      addKnot sh k #corner #line [311874.864,459764.165,0.0]
      addKnot sh k #corner #line [310908.060,460975.785,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313197.134,460674.111,0.0]
      addKnot sh k #corner #line [313864.953,459864.495,0.0]
      addKnot sh k #corner #line [313645.296,459815.606,0.0]
      addKnot sh k #corner #line [313104.261,460471.557,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311292.019,459054.556,0.0]
      addKnot sh k #corner #line [311832.606,458398.254,0.0]
      addKnot sh k #corner #line [311674.980,458275.005,0.0]
      addKnot sh k #corner #line [311072.486,459007.364,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310795.211,457456.254,0.0]
      addKnot sh k #corner #line [311443.781,456686.229,0.0]
      addKnot sh k #corner #line [311595.179,456816.922,0.0]
      addKnot sh k #corner #line [311014.939,457505.035,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [312379.315,455908.555,0.0]
      addKnot sh k #corner #line [313645.180,454491.822,0.0]
      addKnot sh k #corner #line [313497.581,454356.861,0.0]
      addKnot sh k #corner #line [312227.917,455777.863,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313864.953,459864.495,0.0]
      addKnot sh k #corner #line [315104.405,458412.850,0.0]
      addKnot sh k #corner #line [316375.395,456988.737,0.0]
      addKnot sh k #corner #line [316227.798,456853.773,0.0]
      addKnot sh k #corner #line [314985.663,458244.772,0.0]
      addKnot sh k #corner #line [313773.548,459662.007,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311807.234,449145.180,0.0]
      addKnot sh k #corner #line [313054.994,447877.081,0.0]
      addKnot sh k #corner #line [314326.112,446632.395,0.0]
      addKnot sh k #corner #line [314332.007,446349.614,0.0]
      addKnot sh k #corner #line [312949.151,447700.185,0.0]
      addKnot sh k #corner #line [311593.797,449078.353,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317927.354,455043.842,0.0]
      addKnot sh k #corner #line [318278.137,454682.815,0.0]
      addKnot sh k #corner #line [318419.973,454823.830,0.0]
      addKnot sh k #corner #line [318001.920,455254.595,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [319477.549,453760.095,0.0]
      addKnot sh k #corner #line [320492.715,452772.680,0.0]
      addKnot sh k #corner #line [320209.933,452766.785,0.0]
      addKnot sh k #corner #line [319335.713,453619.080,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310090.476,450969.876,0.0]
      addKnot sh k #corner #line [311668.442,449289.183,0.0]
      addKnot sh k #corner #line [311593.797,449078.353,0.0]
      addKnot sh k #corner #line [309807.914,450982.487,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [314739.455,455221.586,0.0]
      addKnot sh k #corner #line [315196.958,454726.221,0.0]
      addKnot sh k #corner #line [315050.384,454590.147,0.0]
      addKnot sh k #corner #line [314591.897,455086.579,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317548.701,455728.389,0.0]
      addKnot sh k #corner #line [318001.920,455254.595,0.0]
      addKnot sh k #corner #line [317788.562,455187.845,0.0]
      addKnot sh k #corner #line [317402.707,455591.687,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311935.309,452657.062,0.0]
      addKnot sh k #corner #line [313468.477,451024.083,0.0]
      addKnot sh k #corner #line [313324.474,450885.291,0.0]
      addKnot sh k #corner #line [311787.722,452522.087,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [315196.958,454726.221,0.0]
      addKnot sh k #corner #line [316204.531,453661.132,0.0]
      addKnot sh k #corner #line [316060.528,453522.340,0.0]
      addKnot sh k #corner #line [315118.549,454516.978,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313780.155,454344.235,0.0]
      addKnot sh k #corner #line [314243.338,453842.695,0.0]
      addKnot sh k #corner #line [314096.762,453706.623,0.0]
      addKnot sh k #corner #line [313632.555,454209.274,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [314311.501,453769.524,0.0]
      addKnot sh k #corner #line [315268.512,452758.984,0.0]
      addKnot sh k #corner #line [315124.510,452620.192,0.0]
      addKnot sh k #corner #line [314096.762,453706.623,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [320611.899,447771.797,0.0]
      addKnot sh k #corner #line [321137.617,447310.315,0.0]
      addKnot sh k #corner #line [320930.565,447225.504,0.0]
      addKnot sh k #corner #line [320479.830,447621.603,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [321081.380,447094.143,0.0]
      addKnot sh k #corner #line [322041.493,446271.400,0.0]
      addKnot sh k #corner #line [322169.562,446425.023,0.0]
      addKnot sh k #corner #line [321137.617,447310.315,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287816.321,538899.890,0.0]
      addKnot sh k #corner #line [287633.844,538159.503,0.0]
      addKnot sh k #corner #line [287415.924,538109.185,0.0]
      addKnot sh k #corner #line [287598.058,538851.513,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:wallHeight capStart:true capEnd:true)
      append made sh
      -- MASONRY: 14 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_MASONRY_SOLID_")
      sh.wirecolor = (color 45 196 102)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316779.212,457087.025,0.0]
      addKnot sh k #corner #line [316436.628,456773.716,0.0]
      addKnot sh k #corner #line [316301.653,456921.302,0.0]
      addKnot sh k #corner #line [316644.238,457234.612,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317751.137,458246.923,0.0]
      addKnot sh k #corner #line [323090.675,463130.181,0.0]
      addKnot sh k #corner #line [323225.649,462982.594,0.0]
      addKnot sh k #corner #line [317886.112,458099.336,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [304748.591,485925.924,0.0]
      addKnot sh k #corner #line [306610.129,486657.126,0.0]
      addKnot sh k #corner #line [306683.249,486470.972,0.0]
      addKnot sh k #corner #line [304821.712,485739.770,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [306207.089,431809.584,0.0]
      addKnot sh k #corner #line [314963.298,441687.338,0.0]
      addKnot sh k #corner #line [315112.960,441554.669,0.0]
      addKnot sh k #corner #line [306356.752,431676.914,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298296.095,440454.375,0.0]
      addKnot sh k #corner #line [307594.085,448957.815,0.0]
      addKnot sh k #corner #line [307729.060,448810.229,0.0]
      addKnot sh k #corner #line [298431.070,440306.788,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [291008.277,449561.650,0.0]
      addKnot sh k #corner #line [301025.216,456958.764,0.0]
      addKnot sh k #corner #line [301144.025,456797.877,0.0]
      addKnot sh k #corner #line [291127.086,449400.763,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296910.771,462997.265,0.0]
      addKnot sh k #corner #line [298423.984,460663.374,0.0]
      addKnot sh k #corner #line [300002.232,458372.961,0.0]
      addKnot sh k #corner #line [300164.429,458489.983,0.0]
      addKnot sh k #corner #line [298534.352,460858.237,0.0]
      addKnot sh k #corner #line [296973.943,463272.964,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302204.494,455391.226,0.0]
      addKnot sh k #corner #line [303574.127,453648.535,0.0]
      addKnot sh k #corner #line [304982.470,451936.975,0.0]
      addKnot sh k #corner #line [306428.815,450257.407,0.0]
      addKnot sh k #corner #line [306577.892,450390.743,0.0]
      addKnot sh k #corner #line [305135.148,452066.163,0.0]
      addKnot sh k #corner #line [303730.296,453773.480,0.0]
      addKnot sh k #corner #line [302364.040,455511.838,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [308930.769,447522.119,0.0]
      addKnot sh k #corner #line [310475.056,445932.147,0.0]
      addKnot sh k #corner #line [312054.587,444377.182,0.0]
      addKnot sh k #corner #line [313668.567,442858.004,0.0]
      addKnot sh k #corner #line [313802.890,443006.192,0.0]
      addKnot sh k #corner #line [312192.925,444521.621,0.0]
      addKnot sh k #corner #line [310617.309,446072.732,0.0]
      addKnot sh k #corner #line [309076.834,447658.748,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302993.765,482553.758,0.0]
      addKnot sh k #corner #line [304056.701,480161.934,0.0]
      addKnot sh k #corner #line [305193.327,477804.237,0.0]
      addKnot sh k #corner #line [305014.538,477714.600,0.0]
      addKnot sh k #corner #line [303875.218,480077.887,0.0]
      addKnot sh k #corner #line [302809.762,482475.382,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285460.784,472253.035,0.0]
      addKnot sh k #corner #line [285987.420,471115.516,0.0]
      addKnot sh k #corner #line [286167.796,471201.925,0.0]
      addKnot sh k #corner #line [285560.094,472517.870,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [286815.849,469849.140,0.0]
      addKnot sh k #corner #line [287370.551,468729.314,0.0]
      addKnot sh k #corner #line [287191.867,468639.468,0.0]
      addKnot sh k #corner #line [286635.473,469762.731,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [307930.959,472777.024,0.0]
      addKnot sh k #corner #line [309246.310,470615.641,0.0]
      addKnot sh k #corner #line [308970.036,470678.452,0.0]
      addKnot sh k #corner #line [307758.236,472676.194,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [304818.617,465859.330,0.0]
      addKnot sh k #corner #line [306192.716,463825.570,0.0]
      addKnot sh k #corner #line [307621.582,461829.908,0.0]
      addKnot sh k #corner #line [307579.503,461550.212,0.0]
      addKnot sh k #corner #line [306085.271,463629.890,0.0]
      addKnot sh k #corner #line [304650.479,465751.013,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:wallHeight capStart:true capEnd:true)
      append made sh
      -- PREFAB: 13 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_PREFAB_SOLID_")
      sh.wirecolor = (color 155 103 221)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [322405.156,454766.550,0.0]
      addKnot sh k #corner #line [322361.733,454721.278,0.0]
      addKnot sh k #corner #line [322289.564,454790.499,0.0]
      addKnot sh k #corner #line [322332.986,454835.771,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [323025.195,455557.468,0.0]
      addKnot sh k #corner #line [324296.902,456883.348,0.0]
      addKnot sh k #corner #line [326858.073,459553.624,0.0]
      addKnot sh k #corner #line [326930.243,459484.404,0.0]
      addKnot sh k #corner #line [324369.071,456814.127,0.0]
      addKnot sh k #corner #line [323097.365,455488.247,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [332512.512,443155.256,0.0]
      addKnot sh k #corner #line [334530.078,446197.045,0.0]
      addKnot sh k #corner #line [334613.413,446141.771,0.0]
      addKnot sh k #corner #line [332595.847,443099.981,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335635.571,447863.745,0.0]
      addKnot sh k #corner #line [337653.084,450905.454,0.0]
      addKnot sh k #corner #line [337736.419,450850.180,0.0]
      addKnot sh k #corner #line [335718.906,447808.470,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335071.135,441519.671,0.0]
      addKnot sh k #corner #line [336981.314,444630.018,0.0]
      addKnot sh k #corner #line [337066.527,444577.685,0.0]
      addKnot sh k #corner #line [335156.348,441467.339,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338027.966,446334.283,0.0]
      addKnot sh k #corner #line [339938.096,449444.550,0.0]
      addKnot sh k #corner #line [340023.309,449392.217,0.0]
      addKnot sh k #corner #line [338113.179,446281.951,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325200.601,448583.290,0.0]
      addKnot sh k #corner #line [327525.070,451397.525,0.0]
      addKnot sh k #corner #line [327602.170,451333.843,0.0]
      addKnot sh k #corner #line [325277.702,448519.608,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [328798.724,452939.539,0.0]
      addKnot sh k #corner #line [331123.130,455753.698,0.0]
      addKnot sh k #corner #line [331200.230,455690.015,0.0]
      addKnot sh k #corner #line [328875.825,452875.856,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327574.241,446689.215,0.0]
      addKnot sh k #corner #line [329799.078,449582.859,0.0]
      addKnot sh k #corner #line [329878.354,449521.905,0.0]
      addKnot sh k #corner #line [327653.517,446628.262,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [331018.141,451168.383,0.0]
      addKnot sh k #corner #line [333242.918,454061.948,0.0]
      addKnot sh k #corner #line [333322.194,454000.995,0.0]
      addKnot sh k #corner #line [331097.417,451107.430,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [332175.681,447819.587,0.0]
      addKnot sh k #corner #line [330053.348,444851.736,0.0]
      addKnot sh k #corner #line [329972.006,444909.904,0.0]
      addKnot sh k #corner #line [332094.360,447877.785,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335462.175,452415.390,0.0]
      addKnot sh k #corner #line [333339.042,449446.421,0.0]
      addKnot sh k #corner #line [333257.723,449504.620,0.0]
      addKnot sh k #corner #line [335380.833,452473.558,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329142.287,457448.539,0.0]
      addKnot sh k #corner #line [326714.306,454723.391,0.0]
      addKnot sh k #corner #line [326639.478,454789.730,0.0]
      addKnot sh k #corner #line [329067.623,457515.061,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:wallHeight capStart:true capEnd:true)
      append made sh
      -- GLASS: 47 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_GLASS_PARTITIONS_")
      sh.wirecolor = (color 62 199 205)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325195.180,456057.525,0.0]
      addKnot sh k #corner #line [326654.677,454731.688,0.0]
      addKnot sh k #corner #line [326746.886,454650.065,0.0]
      addKnot sh k #corner #line [326724.964,454624.953,0.0]
      addKnot sh k #corner #line [326632.564,454706.746,0.0]
      addKnot sh k #corner #line [325172.319,456033.265,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [326654.677,454731.688,0.0]
      addKnot sh k #corner #line [325195.180,456057.525,0.0]
      addKnot sh k #corner #line [325218.040,456081.785,0.0]
      addKnot sh k #corner #line [326676.790,454756.631,0.0]
      addKnot sh k #corner #line [326768.807,454675.177,0.0]
      addKnot sh k #corner #line [326746.886,454650.065,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325172.319,456033.265,0.0]
      addKnot sh k #corner #line [326632.564,454706.746,0.0]
      addKnot sh k #corner #line [326724.964,454624.953,0.0]
      addKnot sh k #corner #line [326703.043,454599.842,0.0]
      addKnot sh k #corner #line [326610.451,454681.803,0.0]
      addKnot sh k #corner #line [325149.459,456009.005,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327500.222,453992.429,0.0]
      addKnot sh k #corner #line [328816.037,452881.986,0.0]
      addKnot sh k #corner #line [328915.040,452800.343,0.0]
      addKnot sh k #corner #line [328894.011,452774.479,0.0]
      addKnot sh k #corner #line [328794.809,452856.285,0.0]
      addKnot sh k #corner #line [327478.300,453967.317,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [328816.037,452881.986,0.0]
      addKnot sh k #corner #line [327500.222,453992.429,0.0]
      addKnot sh k #corner #line [327522.143,454017.541,0.0]
      addKnot sh k #corner #line [328837.264,452907.686,0.0]
      addKnot sh k #corner #line [328936.069,452826.207,0.0]
      addKnot sh k #corner #line [328915.040,452800.343,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327478.300,453967.317,0.0]
      addKnot sh k #corner #line [328794.809,452856.285,0.0]
      addKnot sh k #corner #line [328894.011,452774.479,0.0]
      addKnot sh k #corner #line [328872.983,452748.615,0.0]
      addKnot sh k #corner #line [328773.582,452830.585,0.0]
      addKnot sh k #corner #line [327456.379,453942.206,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333319.650,449419.310,0.0]
      addKnot sh k #corner #line [333416.335,449350.310,0.0]
      addKnot sh k #corner #line [333397.158,449323.045,0.0]
      addKnot sh k #corner #line [333300.267,449392.191,0.0]
      addKnot sh k #corner #line [331908.387,450409.474,0.0]
      addKnot sh k #corner #line [331928.504,450436.054,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333416.335,449350.310,0.0]
      addKnot sh k #corner #line [333319.650,449419.310,0.0]
      addKnot sh k #corner #line [331928.504,450436.054,0.0]
      addKnot sh k #corner #line [331948.621,450462.633,0.0]
      addKnot sh k #corner #line [333339.033,449446.428,0.0]
      addKnot sh k #corner #line [333435.511,449377.576,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [334234.287,448775.024,0.0]
      addKnot sh k #corner #line [335658.805,447808.316,0.0]
      addKnot sh k #corner #line [335758.489,447742.303,0.0]
      addKnot sh k #corner #line [335740.275,447714.385,0.0]
      addKnot sh k #corner #line [335640.380,447780.538,0.0]
      addKnot sh k #corner #line [334215.110,448747.759,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335658.805,447808.316,0.0]
      addKnot sh k #corner #line [334234.287,448775.024,0.0]
      addKnot sh k #corner #line [334253.464,448802.290,0.0]
      addKnot sh k #corner #line [335677.230,447836.095,0.0]
      addKnot sh k #corner #line [335776.702,447770.221,0.0]
      addKnot sh k #corner #line [335758.489,447742.303,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333300.267,449392.191,0.0]
      addKnot sh k #corner #line [333397.158,449323.045,0.0]
      addKnot sh k #corner #line [333377.982,449295.779,0.0]
      addKnot sh k #corner #line [333280.884,449365.073,0.0]
      addKnot sh k #corner #line [331888.270,450382.895,0.0]
      addKnot sh k #corner #line [331908.387,450409.474,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [334215.110,448747.759,0.0]
      addKnot sh k #corner #line [335640.380,447780.538,0.0]
      addKnot sh k #corner #line [335740.275,447714.385,0.0]
      addKnot sh k #corner #line [335722.062,447686.467,0.0]
      addKnot sh k #corner #line [335621.955,447752.760,0.0]
      addKnot sh k #corner #line [334195.934,448720.493,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [332214.456,447873.817,0.0]
      addKnot sh k #corner #line [332310.264,447805.440,0.0]
      addKnot sh k #corner #line [332291.083,447778.178,0.0]
      addKnot sh k #corner #line [332195.073,447846.699,0.0]
      addKnot sh k #corner #line [330748.249,448904.525,0.0]
      addKnot sh k #corner #line [330768.371,448931.100,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [332310.264,447805.440,0.0]
      addKnot sh k #corner #line [332214.456,447873.817,0.0]
      addKnot sh k #corner #line [330768.371,448931.100,0.0]
      addKnot sh k #corner #line [330788.494,448957.675,0.0]
      addKnot sh k #corner #line [332233.839,447900.935,0.0]
      addKnot sh k #corner #line [332329.446,447832.701,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333128.106,447229.997,0.0]
      addKnot sh k #corner #line [334608.587,446224.952,0.0]
      addKnot sh k #corner #line [334703.182,446162.301,0.0]
      addKnot sh k #corner #line [334684.962,446134.387,0.0]
      addKnot sh k #corner #line [334590.162,446197.174,0.0]
      addKnot sh k #corner #line [333108.924,447202.735,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [334608.587,446224.952,0.0]
      addKnot sh k #corner #line [333128.106,447229.997,0.0]
      addKnot sh k #corner #line [333147.288,447257.258,0.0]
      addKnot sh k #corner #line [334627.012,446252.730,0.0]
      addKnot sh k #corner #line [334721.403,446190.215,0.0]
      addKnot sh k #corner #line [334703.182,446162.301,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [332195.073,447846.699,0.0]
      addKnot sh k #corner #line [332291.083,447778.178,0.0]
      addKnot sh k #corner #line [332271.901,447750.916,0.0]
      addKnot sh k #corner #line [332175.690,447819.580,0.0]
      addKnot sh k #corner #line [330728.127,448877.949,0.0]
      addKnot sh k #corner #line [330748.249,448904.525,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333108.924,447202.735,0.0]
      addKnot sh k #corner #line [334590.162,446197.174,0.0]
      addKnot sh k #corner #line [334684.962,446134.387,0.0]
      addKnot sh k #corner #line [334666.742,446106.474,0.0]
      addKnot sh k #corner #line [334571.737,446169.395,0.0]
      addKnot sh k #corner #line [333089.743,447175.473,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325384.926,453318.223,0.0]
      addKnot sh k #corner #line [326748.323,452135.286,0.0]
      addKnot sh k #corner #line [326726.905,452109.744,0.0]
      addKnot sh k #corner #line [325387.761,453271.165,0.0]
      addKnot sh k #corner #line [322944.959,450514.812,0.0]
      addKnot sh k #corner #line [322920.013,450536.920,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [326748.323,452135.286,0.0]
      addKnot sh k #corner #line [325384.926,453318.223,0.0]
      addKnot sh k #corner #line [322920.013,450536.920,0.0]
      addKnot sh k #corner #line [322895.066,450559.029,0.0]
      addKnot sh k #corner #line [325382.099,453365.291,0.0]
      addKnot sh k #corner #line [326769.741,452160.829,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327514.577,451492.749,0.0]
      addKnot sh k #corner #line [327606.066,451417.073,0.0]
      addKnot sh k #corner #line [327697.661,451341.527,0.0]
      addKnot sh k #corner #line [327676.625,451315.670,0.0]
      addKnot sh k #corner #line [327584.838,451391.373,0.0]
      addKnot sh k #corner #line [327493.159,451467.207,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327606.066,451417.073,0.0]
      addKnot sh k #corner #line [327514.577,451492.749,0.0]
      addKnot sh k #corner #line [327535.996,451518.291,0.0]
      addKnot sh k #corner #line [327627.293,451442.773,0.0]
      addKnot sh k #corner #line [327718.698,451367.385,0.0]
      addKnot sh k #corner #line [327697.661,451341.527,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325387.761,453271.165,0.0]
      addKnot sh k #corner #line [326726.905,452109.744,0.0]
      addKnot sh k #corner #line [326705.486,452084.202,0.0]
      addKnot sh k #corner #line [325390.605,453224.117,0.0]
      addKnot sh k #corner #line [322969.905,450492.703,0.0]
      addKnot sh k #corner #line [322944.959,450514.812,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327493.159,451467.207,0.0]
      addKnot sh k #corner #line [327584.838,451391.373,0.0]
      addKnot sh k #corner #line [327676.625,451315.670,0.0]
      addKnot sh k #corner #line [327655.589,451289.812,0.0]
      addKnot sh k #corner #line [327563.610,451365.672,0.0]
      addKnot sh k #corner #line [327471.741,451441.664,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [328473.378,450710.446,0.0]
      addKnot sh k #corner #line [329879.343,449605.221,0.0]
      addKnot sh k #corner #line [329971.125,449534.754,0.0]
      addKnot sh k #corner #line [329951.003,449508.178,0.0]
      addKnot sh k #corner #line [329859.025,449578.796,0.0]
      addKnot sh k #corner #line [328452.342,450684.588,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329879.343,449605.221,0.0]
      addKnot sh k #corner #line [328473.378,450710.446,0.0]
      addKnot sh k #corner #line [328494.415,450736.304,0.0]
      addKnot sh k #corner #line [329899.660,449631.646,0.0]
      addKnot sh k #corner #line [329991.247,449561.329,0.0]
      addKnot sh k #corner #line [329971.125,449534.754,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [328452.342,450684.588,0.0]
      addKnot sh k #corner #line [329859.025,449578.796,0.0]
      addKnot sh k #corner #line [329951.003,449508.178,0.0]
      addKnot sh k #corner #line [329930.881,449481.603,0.0]
      addKnot sh k #corner #line [329838.707,449552.370,0.0]
      addKnot sh k #corner #line [328431.305,450658.731,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335540.581,445615.708,0.0]
      addKnot sh k #corner #line [337058.801,444660.648,0.0]
      addKnot sh k #corner #line [337160.383,444598.362,0.0]
      addKnot sh k #corner #line [337143.150,444569.829,0.0]
      addKnot sh k #corner #line [337041.356,444632.243,0.0]
      addKnot sh k #corner #line [335522.361,445587.795,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [337058.801,444660.648,0.0]
      addKnot sh k #corner #line [335540.581,445615.708,0.0]
      addKnot sh k #corner #line [335558.801,445643.622,0.0]
      addKnot sh k #corner #line [337076.245,444689.052,0.0]
      addKnot sh k #corner #line [337177.616,444626.896,0.0]
      addKnot sh k #corner #line [337160.383,444598.362,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [335522.361,445587.795,0.0]
      addKnot sh k #corner #line [337041.356,444632.243,0.0]
      addKnot sh k #corner #line [337143.150,444569.829,0.0]
      addKnot sh k #corner #line [337125.917,444541.295,0.0]
      addKnot sh k #corner #line [337023.912,444603.839,0.0]
      addKnot sh k #corner #line [335504.141,445559.881,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338016.382,444081.386,0.0]
      addKnot sh k #corner #line [339649.113,443133.544,0.0]
      addKnot sh k #corner #line [339632.706,443104.528,0.0]
      addKnot sh k #corner #line [337999.149,444052.852,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [339649.113,443133.544,0.0]
      addKnot sh k #corner #line [338016.382,444081.386,0.0]
      addKnot sh k #corner #line [338033.615,444109.920,0.0]
      addKnot sh k #corner #line [339665.521,443162.559,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [337999.149,444052.852,0.0]
      addKnot sh k #corner #line [339632.706,443104.528,0.0]
      addKnot sh k #corner #line [339616.298,443075.513,0.0]
      addKnot sh k #corner #line [337981.917,444024.318,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329690.941,452169.488,0.0]
      addKnot sh k #corner #line [331037.452,451111.469,0.0]
      addKnot sh k #corner #line [331131.135,451039.547,0.0]
      addKnot sh k #corner #line [331111.018,451012.967,0.0]
      addKnot sh k #corner #line [331017.134,451085.043,0.0]
      addKnot sh k #corner #line [329669.912,452143.624,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [331037.452,451111.469,0.0]
      addKnot sh k #corner #line [329690.941,452169.488,0.0]
      addKnot sh k #corner #line [329711.970,452195.352,0.0]
      addKnot sh k #corner #line [331057.770,451137.894,0.0]
      addKnot sh k #corner #line [331151.252,451066.126,0.0]
      addKnot sh k #corner #line [331131.135,451039.547,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329669.912,452143.624,0.0]
      addKnot sh k #corner #line [331017.134,451085.043,0.0]
      addKnot sh k #corner #line [331111.018,451012.967,0.0]
      addKnot sh k #corner #line [331090.902,450986.388,0.0]
      addKnot sh k #corner #line [330996.817,451058.618,0.0]
      addKnot sh k #corner #line [329648.883,452117.760,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338053.120,446279.699,0.0]
      addKnot sh k #corner #line [338154.701,446217.417,0.0]
      addKnot sh k #corner #line [338137.473,446188.881,0.0]
      addKnot sh k #corner #line [338035.676,446251.295,0.0]
      addKnot sh k #corner #line [336577.809,447167.999,0.0]
      addKnot sh k #corner #line [336596.022,447195.917,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338154.701,446217.417,0.0]
      addKnot sh k #corner #line [338053.120,446279.699,0.0]
      addKnot sh k #corner #line [336596.022,447195.917,0.0]
      addKnot sh k #corner #line [336614.235,447223.835,0.0]
      addKnot sh k #corner #line [338070.564,446308.104,0.0]
      addKnot sh k #corner #line [338171.929,446245.954,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [339010.790,445700.589,0.0]
      addKnot sh k #corner #line [340586.323,444786.312,0.0]
      addKnot sh k #corner #line [340569.916,444757.296,0.0]
      addKnot sh k #corner #line [338993.562,445672.053,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [340586.323,444786.312,0.0]
      addKnot sh k #corner #line [339010.790,445700.589,0.0]
      addKnot sh k #corner #line [339028.018,445729.126,0.0]
      addKnot sh k #corner #line [340602.730,444815.328,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338035.676,446251.295,0.0]
      addKnot sh k #corner #line [338137.473,446188.881,0.0]
      addKnot sh k #corner #line [338120.245,446160.344,0.0]
      addKnot sh k #corner #line [338018.232,446222.891,0.0]
      addKnot sh k #corner #line [336559.596,447140.080,0.0]
      addKnot sh k #corner #line [336577.809,447167.999,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [338993.562,445672.053,0.0]
      addKnot sh k #corner #line [340569.916,444757.296,0.0]
      addKnot sh k #corner #line [340553.510,444728.280,0.0]
      addKnot sh k #corner #line [338976.334,445643.516,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269346.305,514827.085,0.0]
      addKnot sh k #corner #line [271196.482,514843.149,0.0]
      addKnot sh k #corner #line [271197.061,514776.484,0.0]
      addKnot sh k #corner #line [269346.884,514760.421,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269346.594,514793.753,0.0]
      addKnot sh k #corner #line [271196.771,514809.817,0.0]
      addKnot sh k #corner #line [271196.193,514876.481,0.0]
      addKnot sh k #corner #line [269346.015,514860.417,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [274196.658,514835.862,0.0]
      addKnot sh k #corner #line [276046.835,514851.926,0.0]
      addKnot sh k #corner #line [276046.257,514918.590,0.0]
      addKnot sh k #corner #line [274196.079,514902.526,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [325384.926,453318.223,0.0]
      addKnot sh k #corner #line [326748.323,452135.286,0.0]
      addKnot sh k #corner #line [326705.486,452084.202,0.0]
      addKnot sh k #corner #line [325390.605,453224.117,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302035.829,484717.169,0.0]
      addKnot sh k #corner #line [302932.431,482527.633,0.0]
      addKnot sh k #corner #line [302871.097,482501.507,0.0]
      addKnot sh k #corner #line [301949.405,484754.849,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:wallHeight capStart:true capEnd:true)
      append made sh
      -- STRUCTURE: 8 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_STRUCT_COMPONENTS_")
      sh.wirecolor = (color 135 142 154)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [283632.336,444488.339,0.0]
      addKnot sh k #corner #line [288459.357,448052.307,0.0]
      addKnot sh k #corner #line [288489.056,448012.083,0.0]
      addKnot sh k #corner #line [283661.971,444448.068,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [283661.971,444448.068,0.0]
      addKnot sh k #corner #line [288489.056,448012.083,0.0]
      addKnot sh k #corner #line [288667.250,447770.738,0.0]
      addKnot sh k #corner #line [283839.781,444206.441,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284111.406,444344.839,0.0]
      addKnot sh k #corner #line [283869.416,444166.169,0.0]
      addKnot sh k #corner #line [283839.781,444206.441,0.0]
      addKnot sh k #corner #line [288667.250,447770.738,0.0]
      addKnot sh k #corner #line [288696.917,447730.557,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329465.809,465411.837,0.0]
      addKnot sh k #corner #line [331248.054,463657.779,0.0]
      addKnot sh k #corner #line [333090.381,461966.935,0.0]
      addKnot sh k #corner #line [334990.548,460341.364,0.0]
      addKnot sh k #corner #line [336946.246,458783.042,0.0]
      addKnot sh k #corner #line [338955.093,457293.865,0.0]
      addKnot sh k #corner #line [341014.648,455875.643,0.0]
      addKnot sh k #corner #line [343122.405,454530.103,0.0]
      addKnot sh k #corner #line [345275.801,453258.880,0.0]
      addKnot sh k #corner #line [345374.455,453432.855,0.0]
      addKnot sh k #corner #line [343205.764,454713.618,0.0]
      addKnot sh k #corner #line [341083.529,456069.969,0.0]
      addKnot sh k #corner #line [339010.381,457500.224,0.0]
      addKnot sh k #corner #line [336988.893,459002.608,0.0]
      addKnot sh k #corner #line [335021.574,460575.258,0.0]
      addKnot sh k #corner #line [333110.865,462216.221,0.0]
      addKnot sh k #corner #line [331259.136,463923.462,0.0]
      addKnot sh k #corner #line [329468.687,465694.863,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327467.252,463450.773,0.0]
      addKnot sh k #corner #line [329319.097,461628.216,0.0]
      addKnot sh k #corner #line [331233.370,459871.343,0.0]
      addKnot sh k #corner #line [333207.742,458182.290,0.0]
      addKnot sh k #corner #line [335239.812,456563.113,0.0]
      addKnot sh k #corner #line [337327.109,455015.781,0.0]
      addKnot sh k #corner #line [339467.092,453542.176,0.0]
      addKnot sh k #corner #line [341657.161,452144.090,0.0]
      addKnot sh k #corner #line [343894.650,450823.224,0.0]
      addKnot sh k #corner #line [343795.996,450649.248,0.0]
      addKnot sh k #corner #line [341531.199,451986.746,0.0]
      addKnot sh k #corner #line [339314.893,453403.148,0.0]
      addKnot sh k #corner #line [337149.826,454896.698,0.0]
      addKnot sh k #corner #line [335038.681,456465.544,0.0]
      addKnot sh k #corner #line [332984.078,458107.741,0.0]
      addKnot sh k #corner #line [330988.562,459821.253,0.0]
      addKnot sh k #corner #line [329054.608,461603.956,0.0]
      addKnot sh k #corner #line [327184.613,463453.639,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269391.617,541849.899,0.0]
      addKnot sh k #corner #line [268721.065,538821.426,0.0]
      addKnot sh k #corner #line [268132.937,535775.872,0.0]
      addKnot sh k #corner #line [267627.668,532715.482,0.0]
      addKnot sh k #corner #line [267205.630,529642.507,0.0]
      addKnot sh k #corner #line [266867.132,526559.212,0.0]
      addKnot sh k #corner #line [266612.424,523467.867,0.0]
      addKnot sh k #corner #line [266441.695,520370.749,0.0]
      addKnot sh k #corner #line [266741.437,520358.303,0.0]
      addKnot sh k #corner #line [266911.782,523448.223,0.0]
      addKnot sh k #corner #line [267165.935,526532.381,0.0]
      addKnot sh k #corner #line [267503.709,529608.504,0.0]
      addKnot sh k #corner #line [267924.855,532674.325,0.0]
      addKnot sh k #corner #line [268429.063,535727.585,0.0]
      addKnot sh k #corner #line [269015.960,538766.034,0.0]
      addKnot sh k #corner #line [269685.114,541787.434,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284820.980,443393.682,0.0]
      addKnot sh k #corner #line [286644.545,441035.846,0.0]
      addKnot sh k #corner #line [288526.130,438724.047,0.0]
      addKnot sh k #corner #line [290464.573,436459.711,0.0]
      addKnot sh k #corner #line [292458.677,434244.237,0.0]
      addKnot sh k #corner #line [294507.212,432078.992,0.0]
      addKnot sh k #corner #line [296608.911,429965.314,0.0]
      addKnot sh k #corner #line [298762.478,427904.506,0.0]
      addKnot sh k #corner #line [300966.583,425897.843,0.0]
      addKnot sh k #corner #line [300983.575,425615.511,0.0]
      addKnot sh k #corner #line [298754.134,427638.883,0.0]
      addKnot sh k #corner #line [296576.086,429717.476,0.0]
      addKnot sh k #corner #line [294450.800,431849.986,0.0]
      addKnot sh k #corner #line [292379.608,434035.073,0.0]
      addKnot sh k #corner #line [290363.812,436271.367,0.0]
      addKnot sh k #corner #line [288404.678,438557.463,0.0]
      addKnot sh k #corner #line [286503.434,440891.925,0.0]
      addKnot sh k #corner #line [284661.275,443273.289,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [289372.557,446824.882,0.0]
      addKnot sh k #corner #line [291361.743,444262.279,0.0]
      addKnot sh k #corner #line [293422.877,441757.179,0.0]
      addKnot sh k #corner #line [295554.299,439311.604,0.0]
      addKnot sh k #corner #line [297754.288,436927.523,0.0]
      addKnot sh k #corner #line [300021.074,434606.859,0.0]
      addKnot sh k #corner #line [302352.827,432351.482,0.0]
      addKnot sh k #corner #line [304747.669,430163.211,0.0]
      addKnot sh k #corner #line [305030.000,430180.203,0.0]
      addKnot sh k #corner #line [302614.696,432379.973,0.0]
      addKnot sh k #corner #line [300263.382,434648.014,0.0]
      addKnot sh k #corner #line [297977.987,436982.464,0.0]
      addKnot sh k #corner #line [295760.388,439381.408,0.0]
      addKnot sh k #corner #line [293612.402,441842.880,0.0]
      addKnot sh k #corner #line [291535.792,444364.858,0.0]
      addKnot sh k #corner #line [289532.262,446945.275,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:wallHeight capStart:true capEnd:true)
      append made sh
      -- COLUMN: 97 closed/reconstructed footprints
      sh = splineShape name:(uniqueName "DQ1F3D_CONCRETE_COLUMNS_")
      sh.wirecolor = (color 231 171 91)
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [307675.978,547440.348,0.0]
      addKnot sh k #corner #line [307476.155,546982.013,0.0]
      addKnot sh k #corner #line [307017.820,547181.836,0.0]
      addKnot sh k #corner #line [307217.643,547640.170,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [314326.290,540628.567,0.0]
      addKnot sh k #corner #line [314298.785,540492.331,0.0]
      addKnot sh k #corner #line [314223.777,540381.079,0.0]
      addKnot sh k #corner #line [314112.525,540306.071,0.0]
      addKnot sh k #corner #line [313976.290,540278.567,0.0]
      addKnot sh k #corner #line [313840.054,540306.071,0.0]
      addKnot sh k #corner #line [313728.802,540381.079,0.0]
      addKnot sh k #corner #line [313653.794,540492.331,0.0]
      addKnot sh k #corner #line [313626.290,540628.567,0.0]
      addKnot sh k #corner #line [313653.794,540764.803,0.0]
      addKnot sh k #corner #line [313728.802,540876.054,0.0]
      addKnot sh k #corner #line [313840.054,540951.062,0.0]
      addKnot sh k #corner #line [313976.290,540978.567,0.0]
      addKnot sh k #corner #line [314112.525,540951.062,0.0]
      addKnot sh k #corner #line [314223.777,540876.054,0.0]
      addKnot sh k #corner #line [314298.785,540764.803,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311236.287,529891.794,0.0]
      addKnot sh k #corner #line [311208.782,529755.558,0.0]
      addKnot sh k #corner #line [311133.774,529644.307,0.0]
      addKnot sh k #corner #line [311022.523,529569.299,0.0]
      addKnot sh k #corner #line [310886.287,529541.794,0.0]
      addKnot sh k #corner #line [310750.051,529569.299,0.0]
      addKnot sh k #corner #line [310638.800,529644.307,0.0]
      addKnot sh k #corner #line [310563.792,529755.558,0.0]
      addKnot sh k #corner #line [310536.287,529891.794,0.0]
      addKnot sh k #corner #line [310563.792,530028.030,0.0]
      addKnot sh k #corner #line [310638.800,530139.281,0.0]
      addKnot sh k #corner #line [310750.051,530214.289,0.0]
      addKnot sh k #corner #line [310886.287,530241.794,0.0]
      addKnot sh k #corner #line [311022.523,530214.289,0.0]
      addKnot sh k #corner #line [311133.774,530139.281,0.0]
      addKnot sh k #corner #line [311208.782,530028.030,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310127.562,522522.087,0.0]
      addKnot sh k #corner #line [310100.057,522385.851,0.0]
      addKnot sh k #corner #line [310025.049,522274.600,0.0]
      addKnot sh k #corner #line [309913.798,522199.592,0.0]
      addKnot sh k #corner #line [309777.562,522172.087,0.0]
      addKnot sh k #corner #line [309641.326,522199.592,0.0]
      addKnot sh k #corner #line [309530.075,522274.600,0.0]
      addKnot sh k #corner #line [309455.067,522385.851,0.0]
      addKnot sh k #corner #line [309427.562,522522.087,0.0]
      addKnot sh k #corner #line [309455.067,522658.323,0.0]
      addKnot sh k #corner #line [309530.075,522769.575,0.0]
      addKnot sh k #corner #line [309641.326,522844.582,0.0]
      addKnot sh k #corner #line [309777.562,522872.087,0.0]
      addKnot sh k #corner #line [309913.798,522844.582,0.0]
      addKnot sh k #corner #line [310025.049,522769.575,0.0]
      addKnot sh k #corner #line [310100.057,522658.323,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [309743.401,515626.864,0.0]
      addKnot sh k #corner #line [309719.825,515510.090,0.0]
      addKnot sh k #corner #line [309655.533,515414.732,0.0]
      addKnot sh k #corner #line [309560.174,515350.439,0.0]
      addKnot sh k #corner #line [309443.401,515326.864,0.0]
      addKnot sh k #corner #line [309326.627,515350.439,0.0]
      addKnot sh k #corner #line [309231.269,515414.732,0.0]
      addKnot sh k #corner #line [309166.976,515510.090,0.0]
      addKnot sh k #corner #line [309143.401,515626.864,0.0]
      addKnot sh k #corner #line [309166.976,515743.638,0.0]
      addKnot sh k #corner #line [309231.269,515838.996,0.0]
      addKnot sh k #corner #line [309326.627,515903.288,0.0]
      addKnot sh k #corner #line [309443.401,515926.864,0.0]
      addKnot sh k #corner #line [309560.174,515903.288,0.0]
      addKnot sh k #corner #line [309655.533,515838.996,0.0]
      addKnot sh k #corner #line [309719.825,515743.638,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [309745.255,514876.859,0.0]
      addKnot sh k #corner #line [309721.679,514760.085,0.0]
      addKnot sh k #corner #line [309657.387,514664.727,0.0]
      addKnot sh k #corner #line [309562.028,514600.435,0.0]
      addKnot sh k #corner #line [309445.255,514576.859,0.0]
      addKnot sh k #corner #line [309328.481,514600.435,0.0]
      addKnot sh k #corner #line [309233.123,514664.727,0.0]
      addKnot sh k #corner #line [309168.830,514760.085,0.0]
      addKnot sh k #corner #line [309145.255,514876.859,0.0]
      addKnot sh k #corner #line [309168.830,514993.633,0.0]
      addKnot sh k #corner #line [309233.123,515088.991,0.0]
      addKnot sh k #corner #line [309328.481,515153.284,0.0]
      addKnot sh k #corner #line [309445.255,515176.859,0.0]
      addKnot sh k #corner #line [309562.028,515153.284,0.0]
      addKnot sh k #corner #line [309657.387,515088.991,0.0]
      addKnot sh k #corner #line [309721.679,514993.633,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [306913.858,507267.294,0.0]
      addKnot sh k #corner #line [306890.283,507150.520,0.0]
      addKnot sh k #corner #line [306825.990,507055.162,0.0]
      addKnot sh k #corner #line [306730.632,506990.869,0.0]
      addKnot sh k #corner #line [306613.858,506967.294,0.0]
      addKnot sh k #corner #line [306497.085,506990.869,0.0]
      addKnot sh k #corner #line [306401.726,507055.162,0.0]
      addKnot sh k #corner #line [306337.434,507150.520,0.0]
      addKnot sh k #corner #line [306313.858,507267.294,0.0]
      addKnot sh k #corner #line [306337.434,507384.067,0.0]
      addKnot sh k #corner #line [306401.726,507479.426,0.0]
      addKnot sh k #corner #line [306497.085,507543.718,0.0]
      addKnot sh k #corner #line [306613.858,507567.294,0.0]
      addKnot sh k #corner #line [306730.632,507543.718,0.0]
      addKnot sh k #corner #line [306825.990,507479.426,0.0]
      addKnot sh k #corner #line [306890.283,507384.067,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [308193.442,499574.936,0.0]
      addKnot sh k #corner #line [308169.867,499458.163,0.0]
      addKnot sh k #corner #line [308105.574,499362.804,0.0]
      addKnot sh k #corner #line [308010.216,499298.512,0.0]
      addKnot sh k #corner #line [307893.442,499274.936,0.0]
      addKnot sh k #corner #line [307776.669,499298.512,0.0]
      addKnot sh k #corner #line [307681.310,499362.804,0.0]
      addKnot sh k #corner #line [307617.018,499458.163,0.0]
      addKnot sh k #corner #line [307593.442,499574.936,0.0]
      addKnot sh k #corner #line [307617.018,499691.710,0.0]
      addKnot sh k #corner #line [307681.310,499787.068,0.0]
      addKnot sh k #corner #line [307776.669,499851.361,0.0]
      addKnot sh k #corner #line [307893.442,499874.936,0.0]
      addKnot sh k #corner #line [308010.216,499851.361,0.0]
      addKnot sh k #corner #line [308105.574,499787.068,0.0]
      addKnot sh k #corner #line [308169.867,499691.710,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310270.087,492058.471,0.0]
      addKnot sh k #corner #line [310246.511,491941.697,0.0]
      addKnot sh k #corner #line [310182.219,491846.339,0.0]
      addKnot sh k #corner #line [310086.860,491782.046,0.0]
      addKnot sh k #corner #line [309970.087,491758.471,0.0]
      addKnot sh k #corner #line [309853.313,491782.046,0.0]
      addKnot sh k #corner #line [309757.955,491846.339,0.0]
      addKnot sh k #corner #line [309693.662,491941.697,0.0]
      addKnot sh k #corner #line [309670.087,492058.471,0.0]
      addKnot sh k #corner #line [309693.662,492175.244,0.0]
      addKnot sh k #corner #line [309757.955,492270.603,0.0]
      addKnot sh k #corner #line [309853.313,492334.895,0.0]
      addKnot sh k #corner #line [309970.087,492358.471,0.0]
      addKnot sh k #corner #line [310086.860,492334.895,0.0]
      addKnot sh k #corner #line [310182.219,492270.603,0.0]
      addKnot sh k #corner #line [310246.511,492175.244,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [313121.040,484800.250,0.0]
      addKnot sh k #corner #line [313097.464,484683.477,0.0]
      addKnot sh k #corner #line [313033.172,484588.118,0.0]
      addKnot sh k #corner #line [312937.813,484523.826,0.0]
      addKnot sh k #corner #line [312821.040,484500.250,0.0]
      addKnot sh k #corner #line [312704.266,484523.826,0.0]
      addKnot sh k #corner #line [312608.908,484588.118,0.0]
      addKnot sh k #corner #line [312544.615,484683.477,0.0]
      addKnot sh k #corner #line [312521.040,484800.250,0.0]
      addKnot sh k #corner #line [312544.615,484917.024,0.0]
      addKnot sh k #corner #line [312608.908,485012.382,0.0]
      addKnot sh k #corner #line [312704.266,485076.675,0.0]
      addKnot sh k #corner #line [312821.040,485100.250,0.0]
      addKnot sh k #corner #line [312937.813,485076.675,0.0]
      addKnot sh k #corner #line [313033.172,485012.382,0.0]
      addKnot sh k #corner #line [313097.464,484917.024,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316613.727,478052.220,0.0]
      addKnot sh k #corner #line [316590.152,477935.447,0.0]
      addKnot sh k #corner #line [316525.859,477840.088,0.0]
      addKnot sh k #corner #line [316430.501,477775.796,0.0]
      addKnot sh k #corner #line [316313.727,477752.220,0.0]
      addKnot sh k #corner #line [316196.954,477775.796,0.0]
      addKnot sh k #corner #line [316101.595,477840.088,0.0]
      addKnot sh k #corner #line [316037.303,477935.447,0.0]
      addKnot sh k #corner #line [316013.727,478052.220,0.0]
      addKnot sh k #corner #line [316037.303,478168.994,0.0]
      addKnot sh k #corner #line [316101.595,478264.352,0.0]
      addKnot sh k #corner #line [316196.954,478328.645,0.0]
      addKnot sh k #corner #line [316313.727,478352.220,0.0]
      addKnot sh k #corner #line [316430.501,478328.645,0.0]
      addKnot sh k #corner #line [316525.859,478264.352,0.0]
      addKnot sh k #corner #line [316590.152,478168.994,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316994.459,477406.046,0.0]
      addKnot sh k #corner #line [316970.883,477289.273,0.0]
      addKnot sh k #corner #line [316906.591,477193.914,0.0]
      addKnot sh k #corner #line [316811.232,477129.622,0.0]
      addKnot sh k #corner #line [316694.459,477106.046,0.0]
      addKnot sh k #corner #line [316577.685,477129.622,0.0]
      addKnot sh k #corner #line [316482.327,477193.914,0.0]
      addKnot sh k #corner #line [316418.034,477289.273,0.0]
      addKnot sh k #corner #line [316394.459,477406.046,0.0]
      addKnot sh k #corner #line [316418.034,477522.820,0.0]
      addKnot sh k #corner #line [316482.327,477618.178,0.0]
      addKnot sh k #corner #line [316577.685,477682.471,0.0]
      addKnot sh k #corner #line [316694.459,477706.046,0.0]
      addKnot sh k #corner #line [316811.232,477682.471,0.0]
      addKnot sh k #corner #line [316906.591,477618.178,0.0]
      addKnot sh k #corner #line [316970.883,477522.820,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [321012.788,471372.931,0.0]
      addKnot sh k #corner #line [320989.212,471256.158,0.0]
      addKnot sh k #corner #line [320924.920,471160.799,0.0]
      addKnot sh k #corner #line [320829.561,471096.507,0.0]
      addKnot sh k #corner #line [320712.788,471072.931,0.0]
      addKnot sh k #corner #line [320596.014,471096.507,0.0]
      addKnot sh k #corner #line [320500.656,471160.799,0.0]
      addKnot sh k #corner #line [320436.363,471256.158,0.0]
      addKnot sh k #corner #line [320412.788,471372.931,0.0]
      addKnot sh k #corner #line [320436.363,471489.705,0.0]
      addKnot sh k #corner #line [320500.656,471585.063,0.0]
      addKnot sh k #corner #line [320596.014,471649.356,0.0]
      addKnot sh k #corner #line [320712.788,471672.931,0.0]
      addKnot sh k #corner #line [320829.561,471649.356,0.0]
      addKnot sh k #corner #line [320924.920,471585.063,0.0]
      addKnot sh k #corner #line [320989.212,471489.705,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [328402.297,467578.031,0.0]
      addKnot sh k #corner #line [328378.721,467461.257,0.0]
      addKnot sh k #corner #line [328314.429,467365.899,0.0]
      addKnot sh k #corner #line [328219.070,467301.606,0.0]
      addKnot sh k #corner #line [328102.297,467278.031,0.0]
      addKnot sh k #corner #line [327985.523,467301.606,0.0]
      addKnot sh k #corner #line [327890.165,467365.899,0.0]
      addKnot sh k #corner #line [327825.872,467461.257,0.0]
      addKnot sh k #corner #line [327802.297,467578.031,0.0]
      addKnot sh k #corner #line [327825.872,467694.804,0.0]
      addKnot sh k #corner #line [327890.165,467790.163,0.0]
      addKnot sh k #corner #line [327985.523,467854.455,0.0]
      addKnot sh k #corner #line [328102.297,467878.031,0.0]
      addKnot sh k #corner #line [328219.070,467854.455,0.0]
      addKnot sh k #corner #line [328314.429,467790.163,0.0]
      addKnot sh k #corner #line [328378.721,467694.804,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [339459.459,457762.361,0.0]
      addKnot sh k #corner #line [339435.883,457645.587,0.0]
      addKnot sh k #corner #line [339371.591,457550.229,0.0]
      addKnot sh k #corner #line [339276.232,457485.936,0.0]
      addKnot sh k #corner #line [339159.459,457462.361,0.0]
      addKnot sh k #corner #line [339042.685,457485.936,0.0]
      addKnot sh k #corner #line [338947.326,457550.229,0.0]
      addKnot sh k #corner #line [338883.034,457645.587,0.0]
      addKnot sh k #corner #line [338859.459,457762.361,0.0]
      addKnot sh k #corner #line [338883.034,457879.134,0.0]
      addKnot sh k #corner #line [338947.326,457974.493,0.0]
      addKnot sh k #corner #line [339042.685,458038.785,0.0]
      addKnot sh k #corner #line [339159.459,458062.361,0.0]
      addKnot sh k #corner #line [339276.232,458038.785,0.0]
      addKnot sh k #corner #line [339371.591,457974.493,0.0]
      addKnot sh k #corner #line [339435.883,457879.134,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [345735.429,453743.138,0.0]
      addKnot sh k #corner #line [345711.853,453626.364,0.0]
      addKnot sh k #corner #line [345647.561,453531.005,0.0]
      addKnot sh k #corner #line [345552.202,453466.713,0.0]
      addKnot sh k #corner #line [345435.429,453443.138,0.0]
      addKnot sh k #corner #line [345318.655,453466.713,0.0]
      addKnot sh k #corner #line [345223.297,453531.005,0.0]
      addKnot sh k #corner #line [345159.004,453626.364,0.0]
      addKnot sh k #corner #line [345135.429,453743.138,0.0]
      addKnot sh k #corner #line [345159.004,453859.911,0.0]
      addKnot sh k #corner #line [345223.297,453955.270,0.0]
      addKnot sh k #corner #line [345318.655,454019.562,0.0]
      addKnot sh k #corner #line [345435.429,454043.138,0.0]
      addKnot sh k #corner #line [345552.202,454019.562,0.0]
      addKnot sh k #corner #line [345647.561,453955.270,0.0]
      addKnot sh k #corner #line [345711.853,453859.911,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [340819.379,446819.120,0.0]
      addKnot sh k #corner #line [341428.290,446473.829,0.0]
      addKnot sh k #corner #line [341082.999,445864.917,0.0]
      addKnot sh k #corner #line [340474.087,446210.209,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [337243.159,440512.464,0.0]
      addKnot sh k #corner #line [337852.071,440167.172,0.0]
      addKnot sh k #corner #line [337506.779,439558.260,0.0]
      addKnot sh k #corner #line [336897.868,439903.552,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311430.558,438003.614,0.0]
      addKnot sh k #corner #line [311879.543,437605.603,0.0]
      addKnot sh k #corner #line [311481.532,437156.619,0.0]
      addKnot sh k #corner #line [311032.547,437554.630,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [324622.407,438283.810,0.0]
      addKnot sh k #corner #line [325110.535,437934.911,0.0]
      addKnot sh k #corner #line [324761.636,437446.782,0.0]
      addKnot sh k #corner #line [324273.507,437795.681,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298234.900,440669.432,0.0]
      addKnot sh k #corner #line [298639.821,440226.669,0.0]
      addKnot sh k #corner #line [298197.059,439821.748,0.0]
      addKnot sh k #corner #line [297792.137,440264.510,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [317069.005,444364.268,0.0]
      addKnot sh k #corner #line [317517.989,443966.257,0.0]
      addKnot sh k #corner #line [317119.978,443517.273,0.0]
      addKnot sh k #corner #line [316670.994,443915.284,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [303695.642,445663.537,0.0]
      addKnot sh k #corner #line [304100.563,445220.775,0.0]
      addKnot sh k #corner #line [303657.801,444815.853,0.0]
      addKnot sh k #corner #line [303252.879,445258.615,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [329565.062,445198.949,0.0]
      addKnot sh k #corner #line [330053.190,444850.050,0.0]
      addKnot sh k #corner #line [329704.291,444361.922,0.0]
      addKnot sh k #corner #line [329216.163,444710.821,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290901.676,449793.705,0.0]
      addKnot sh k #corner #line [291317.502,449230.599,0.0]
      addKnot sh k #corner #line [290754.395,448814.773,0.0]
      addKnot sh k #corner #line [290338.570,449377.879,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [322707.412,450724.878,0.0]
      addKnot sh k #corner #line [323156.397,450326.867,0.0]
      addKnot sh k #corner #line [322824.721,449952.713,0.0]
      addKnot sh k #corner #line [322375.736,450350.724,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333949.498,451161.128,0.0]
      addKnot sh k #corner #line [334356.272,450870.379,0.0]
      addKnot sh k #corner #line [334007.373,450382.251,0.0]
      addKnot sh k #corner #line [333600.599,450673.000,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296803.778,454090.017,0.0]
      addKnot sh k #corner #line [297160.200,453607.354,0.0]
      addKnot sh k #corner #line [296677.538,453250.932,0.0]
      addKnot sh k #corner #line [296321.115,453733.595,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [327616.217,456262.432,0.0]
      addKnot sh k #corner #line [328065.202,455864.421,0.0]
      addKnot sh k #corner #line [327667.191,455415.437,0.0]
      addKnot sh k #corner #line [327218.206,455813.448,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316240.459,457136.364,0.0]
      addKnot sh k #corner #line [316645.380,456693.601,0.0]
      addKnot sh k #corner #line [316202.618,456288.680,0.0]
      addKnot sh k #corner #line [315797.696,456731.442,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284435.631,459664.219,0.0]
      addKnot sh k #corner #line [284739.649,459146.944,0.0]
      addKnot sh k #corner #line [284136.162,458792.257,0.0]
      addKnot sh k #corner #line [283832.144,459309.532,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [284816.126,459017.904,0.0]
      addKnot sh k #corner #line [285525.500,457810.929,0.0]
      addKnot sh k #corner #line [284922.013,457456.242,0.0]
      addKnot sh k #corner #line [284212.639,458663.217,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [303601.243,459109.676,0.0]
      addKnot sh k #corner #line [303957.665,458627.013,0.0]
      addKnot sh k #corner #line [303555.446,458329.995,0.0]
      addKnot sh k #corner #line [303199.024,458812.657,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [321701.200,462130.469,0.0]
      addKnot sh k #corner #line [322106.122,461687.707,0.0]
      addKnot sh k #corner #line [321663.360,461282.785,0.0]
      addKnot sh k #corner #line [321258.438,461725.547,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [290729.138,463363.155,0.0]
      addKnot sh k #corner #line [291033.155,462845.880,0.0]
      addKnot sh k #corner #line [290515.880,462541.862,0.0]
      addKnot sh k #corner #line [290211.863,463059.137,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [291109.666,462716.860,0.0]
      addKnot sh k #corner #line [291413.684,462199.585,0.0]
      addKnot sh k #corner #line [290896.409,461895.567,0.0]
      addKnot sh k #corner #line [290592.392,462412.842,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [310479.120,464188.711,0.0]
      addKnot sh k #corner #line [310835.542,463706.048,0.0]
      addKnot sh k #corner #line [310433.323,463409.030,0.0]
      addKnot sh k #corner #line [310076.901,463891.692,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298057.169,467670.120,0.0]
      addKnot sh k #corner #line [298361.187,467152.845,0.0]
      addKnot sh k #corner #line [297843.912,466848.828,0.0]
      addKnot sh k #corner #line [297539.894,467366.103,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298437.744,467023.853,0.0]
      addKnot sh k #corner #line [298741.761,466506.578,0.0]
      addKnot sh k #corner #line [298224.486,466202.560,0.0]
      addKnot sh k #corner #line [297920.469,466719.835,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [316431.964,468584.648,0.0]
      addKnot sh k #corner #line [316788.386,468101.985,0.0]
      addKnot sh k #corner #line [316305.723,467745.563,0.0]
      addKnot sh k #corner #line [315949.301,468228.226,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279174.837,469890.677,0.0]
      addKnot sh k #corner #line [279464.500,469253.421,0.0]
      addKnot sh k #corner #line [278827.243,468963.758,0.0]
      addKnot sh k #corner #line [278537.581,469601.015,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305765.808,471330.840,0.0]
      addKnot sh k #corner #line [306069.826,470813.565,0.0]
      addKnot sh k #corner #line [305552.551,470509.548,0.0]
      addKnot sh k #corner #line [305248.533,471026.823,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305385.180,471977.074,0.0]
      addKnot sh k #corner #line [305689.198,471459.799,0.0]
      addKnot sh k #corner #line [305171.923,471155.781,0.0]
      addKnot sh k #corner #line [304867.906,471673.056,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285841.180,472865.971,0.0]
      addKnot sh k #corner #line [286089.462,472319.751,0.0]
      addKnot sh k #corner #line [285543.242,472071.469,0.0]
      addKnot sh k #corner #line [285294.960,472617.689,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [311764.899,475726.679,0.0]
      addKnot sh k #corner #line [312068.917,475209.404,0.0]
      addKnot sh k #corner #line [311465.429,474854.717,0.0]
      addKnot sh k #corner #line [311161.412,475371.992,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [312145.585,475080.478,0.0]
      addKnot sh k #corner #line [312500.273,474476.991,0.0]
      addKnot sh k #corner #line [311896.785,474122.303,0.0]
      addKnot sh k #corner #line [311542.098,474725.791,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293624.786,476404.045,0.0]
      addKnot sh k #corner #line [293873.069,475857.825,0.0]
      addKnot sh k #corner #line [293235.812,475568.162,0.0]
      addKnot sh k #corner #line [292987.530,476114.382,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [274949.754,480747.569,0.0]
      addKnot sh k #corner #line [275171.219,480083.526,0.0]
      addKnot sh k #corner #line [274507.175,479862.061,0.0]
      addKnot sh k #corner #line [274285.711,480526.105,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [301317.357,479900.738,0.0]
      addKnot sh k #corner #line [301565.639,479354.518,0.0]
      addKnot sh k #corner #line [301019.419,479106.236,0.0]
      addKnot sh k #corner #line [300771.137,479652.456,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [281890.553,483009.732,0.0]
      addKnot sh k #corner #line [282080.380,482440.552,0.0]
      addKnot sh k #corner #line [281511.200,482250.726,0.0]
      addKnot sh k #corner #line [281321.373,482819.906,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [308033.355,483008.449,0.0]
      addKnot sh k #corner #line [308323.018,482371.192,0.0]
      addKnot sh k #corner #line [307685.761,482081.530,0.0]
      addKnot sh k #corner #line [307396.099,482718.786,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [289953.918,485698.997,0.0]
      addKnot sh k #corner #line [290143.745,485129.817,0.0]
      addKnot sh k #corner #line [289574.565,484939.990,0.0]
      addKnot sh k #corner #line [289384.738,485509.170,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298017.311,488388.270,0.0]
      addKnot sh k #corner #line [298207.138,487819.090,0.0]
      addKnot sh k #corner #line [297637.958,487629.264,0.0]
      addKnot sh k #corner #line [297448.131,488198.444,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [305100.430,490539.776,0.0]
      addKnot sh k #corner #line [305321.894,489875.733,0.0]
      addKnot sh k #corner #line [304657.851,489654.269,0.0]
      addKnot sh k #corner #line [304436.386,490318.312,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [271882.677,491986.626,0.0]
      addKnot sh k #corner #line [272033.517,491303.071,0.0]
      addKnot sh k #corner #line [271349.962,491152.231,0.0]
      addKnot sh k #corner #line [271199.122,491835.786,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [279021.881,493510.878,0.0]
      addKnot sh k #corner #line [279151.172,492924.973,0.0]
      addKnot sh k #corner #line [278565.267,492795.682,0.0]
      addKnot sh k #corner #line [278435.976,493381.587,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [287322.178,495342.559,0.0]
      addKnot sh k #corner #line [287451.470,494756.655,0.0]
      addKnot sh k #corner #line [286865.565,494627.364,0.0]
      addKnot sh k #corner #line [286736.274,495213.268,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [295622.538,497174.254,0.0]
      addKnot sh k #corner #line [295751.829,496588.350,0.0]
      addKnot sh k #corner #line [295165.925,496459.059,0.0]
      addKnot sh k #corner #line [295036.634,497044.963,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302783.972,499061.832,0.0]
      addKnot sh k #corner #line [302934.812,498378.277,0.0]
      addKnot sh k #corner #line [302251.257,498227.438,0.0]
      addKnot sh k #corner #line [302100.417,498910.993,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [270007.208,503484.707,0.0]
      addKnot sh k #corner #line [270085.771,502789.130,0.0]
      addKnot sh k #corner #line [269390.193,502710.567,0.0]
      addKnot sh k #corner #line [269311.631,503406.145,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [277363.154,504290.420,0.0]
      addKnot sh k #corner #line [277436.105,503644.527,0.0]
      addKnot sh k #corner #line [276740.527,503565.964,0.0]
      addKnot sh k #corner #line [276667.576,504211.858,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285806.639,505269.292,0.0]
      addKnot sh k #corner #line [285885.201,504573.715,0.0]
      addKnot sh k #corner #line [285090.255,504483.929,0.0]
      addKnot sh k #corner #line [285011.693,505179.506,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294156.469,506187.268,0.0]
      addKnot sh k #corner #line [294229.419,505541.375,0.0]
      addKnot sh k #corner #line [293533.842,505462.812,0.0]
      addKnot sh k #corner #line [293460.891,506108.706,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [301506.802,507042.665,0.0]
      addKnot sh k #corner #line [301585.365,506347.088,0.0]
      addKnot sh k #corner #line [300889.787,506268.526,0.0]
      addKnot sh k #corner #line [300811.225,506964.103,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269344.461,515710.417,0.0]
      addKnot sh k #corner #line [269344.461,515010.417,0.0]
      addKnot sh k #corner #line [268644.461,515010.417,0.0]
      addKnot sh k #corner #line [268644.461,515710.417,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269346.628,514860.422,0.0]
      addKnot sh k #corner #line [269346.628,514160.422,0.0]
      addKnot sh k #corner #line [268646.628,514160.422,0.0]
      addKnot sh k #corner #line [268646.628,514860.422,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285193.920,515836.065,0.0]
      addKnot sh k #corner #line [285193.920,515136.065,0.0]
      addKnot sh k #corner #line [284493.920,515136.065,0.0]
      addKnot sh k #corner #line [284493.920,515836.065,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285195.995,514986.066,0.0]
      addKnot sh k #corner #line [285195.995,514286.066,0.0]
      addKnot sh k #corner #line [284495.995,514286.066,0.0]
      addKnot sh k #corner #line [284495.995,514986.066,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293643.915,515903.543,0.0]
      addKnot sh k #corner #line [293643.915,515203.543,0.0]
      addKnot sh k #corner #line [292943.915,515203.543,0.0]
      addKnot sh k #corner #line [292943.915,515903.543,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [293645.879,515053.542,0.0]
      addKnot sh k #corner #line [293645.879,514353.542,0.0]
      addKnot sh k #corner #line [292945.879,514353.542,0.0]
      addKnot sh k #corner #line [292945.879,515053.542,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [294081.017,524350.288,0.0]
      addKnot sh k #corner #line [294022.926,523753.107,0.0]
      addKnot sh k #corner #line [293425.745,523811.198,0.0]
      addKnot sh k #corner #line [293483.836,524408.379,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [285620.752,525173.207,0.0]
      addKnot sh k #corner #line [285562.661,524576.026,0.0]
      addKnot sh k #corner #line [284965.480,524634.117,0.0]
      addKnot sh k #corner #line [285023.571,525231.298,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [277160.679,525996.107,0.0]
      addKnot sh k #corner #line [277102.588,525398.926,0.0]
      addKnot sh k #corner #line [276505.407,525457.017,0.0]
      addKnot sh k #corner #line [276563.498,526054.199,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [269900.002,526752.580,0.0]
      addKnot sh k #corner #line [269832.229,526055.869,0.0]
      addKnot sh k #corner #line [269135.518,526123.642,0.0]
      addKnot sh k #corner #line [269203.291,526820.353,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [302726.663,531917.380,0.0]
      addKnot sh k #corner #line [302586.435,531231.569,0.0]
      addKnot sh k #corner #line [301900.625,531371.797,0.0]
      addKnot sh k #corner #line [302040.852,532057.607,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [295506.943,533546.651,0.0]
      addKnot sh k #corner #line [295386.748,532958.813,0.0]
      addKnot sh k #corner #line [294798.910,533079.008,0.0]
      addKnot sh k #corner #line [294919.106,533666.846,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [286983.047,535289.476,0.0]
      addKnot sh k #corner #line [286862.852,534701.638,0.0]
      addKnot sh k #corner #line [286177.042,534841.866,0.0]
      addKnot sh k #corner #line [286297.237,535429.704,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [278900.268,536942.105,0.0]
      addKnot sh k #corner #line [278780.073,536354.268,0.0]
      addKnot sh k #corner #line [278143.249,536484.479,0.0]
      addKnot sh k #corner #line [278263.444,537072.317,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [271669.437,538267.441,0.0]
      addKnot sh k #corner #line [271529.209,537581.631,0.0]
      addKnot sh k #corner #line [270843.399,537721.859,0.0]
      addKnot sh k #corner #line [270983.627,538407.669,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [306251.552,543952.477,0.0]
      addKnot sh k #corner #line [305970.653,543203.413,0.0]
      addKnot sh k #corner #line [305221.590,543484.311,0.0]
      addKnot sh k #corner #line [305502.488,544233.375,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [315682.891,543993.161,0.0]
      addKnot sh k #corner #line [315655.386,543856.926,0.0]
      addKnot sh k #corner #line [315580.378,543745.674,0.0]
      addKnot sh k #corner #line [315469.127,543670.666,0.0]
      addKnot sh k #corner #line [315332.891,543643.161,0.0]
      addKnot sh k #corner #line [315196.655,543670.666,0.0]
      addKnot sh k #corner #line [315085.404,543745.674,0.0]
      addKnot sh k #corner #line [315010.396,543856.926,0.0]
      addKnot sh k #corner #line [314982.891,543993.161,0.0]
      addKnot sh k #corner #line [315010.396,544129.397,0.0]
      addKnot sh k #corner #line [315085.404,544240.649,0.0]
      addKnot sh k #corner #line [315196.655,544315.657,0.0]
      addKnot sh k #corner #line [315332.891,544343.161,0.0]
      addKnot sh k #corner #line [315469.127,544315.657,0.0]
      addKnot sh k #corner #line [315580.378,544240.649,0.0]
      addKnot sh k #corner #line [315655.386,544129.397,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [346603.062,443817.367,0.0]
      addKnot sh k #corner #line [346579.487,443700.594,0.0]
      addKnot sh k #corner #line [346515.194,443605.235,0.0]
      addKnot sh k #corner #line [346419.836,443540.943,0.0]
      addKnot sh k #corner #line [346303.062,443517.367,0.0]
      addKnot sh k #corner #line [346186.289,443540.943,0.0]
      addKnot sh k #corner #line [346090.930,443605.235,0.0]
      addKnot sh k #corner #line [346026.638,443700.594,0.0]
      addKnot sh k #corner #line [346003.062,443817.367,0.0]
      addKnot sh k #corner #line [346026.638,443934.141,0.0]
      addKnot sh k #corner #line [346090.930,444029.499,0.0]
      addKnot sh k #corner #line [346186.289,444093.792,0.0]
      addKnot sh k #corner #line [346303.062,444117.367,0.0]
      addKnot sh k #corner #line [346419.836,444093.792,0.0]
      addKnot sh k #corner #line [346515.194,444029.499,0.0]
      addKnot sh k #corner #line [346579.487,443934.141,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [348530.734,458672.652,0.0]
      addKnot sh k #corner #line [348507.159,458555.879,0.0]
      addKnot sh k #corner #line [348442.866,458460.520,0.0]
      addKnot sh k #corner #line [348347.508,458396.228,0.0]
      addKnot sh k #corner #line [348230.734,458372.652,0.0]
      addKnot sh k #corner #line [348113.961,458396.228,0.0]
      addKnot sh k #corner #line [348018.602,458460.520,0.0]
      addKnot sh k #corner #line [347954.310,458555.879,0.0]
      addKnot sh k #corner #line [347930.734,458672.652,0.0]
      addKnot sh k #corner #line [347954.310,458789.426,0.0]
      addKnot sh k #corner #line [348018.602,458884.784,0.0]
      addKnot sh k #corner #line [348113.961,458949.077,0.0]
      addKnot sh k #corner #line [348230.734,458972.652,0.0]
      addKnot sh k #corner #line [348347.508,458949.077,0.0]
      addKnot sh k #corner #line [348442.866,458884.784,0.0]
      addKnot sh k #corner #line [348507.159,458789.426,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [273647.692,546283.933,0.0]
      addKnot sh k #corner #line [273457.014,545610.403,0.0]
      addKnot sh k #corner #line [272783.485,545801.082,0.0]
      addKnot sh k #corner #line [272974.163,546474.611,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [280603.223,544054.951,0.0]
      addKnot sh k #corner #line [280439.785,543477.640,0.0]
      addKnot sh k #corner #line [279862.474,543641.078,0.0]
      addKnot sh k #corner #line [280025.913,544218.389,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [288843.516,541774.035,0.0]
      addKnot sh k #corner #line [288693.697,541244.833,0.0]
      addKnot sh k #corner #line [288116.386,541408.272,0.0]
      addKnot sh k #corner #line [288266.205,541937.473,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [296974.282,539472.161,0.0]
      addKnot sh k #corner #line [296810.844,538894.850,0.0]
      addKnot sh k #corner #line [296233.533,539058.289,0.0]
      addKnot sh k #corner #line [296396.971,539635.600,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [304148.611,537648.922,0.0]
      addKnot sh k #corner #line [303957.932,536975.393,0.0]
      addKnot sh k #corner #line [303284.403,537166.071,0.0]
      addKnot sh k #corner #line [303475.081,537839.601,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [312485.617,535023.993,0.0]
      addKnot sh k #corner #line [312458.112,534887.757,0.0]
      addKnot sh k #corner #line [312383.104,534776.506,0.0]
      addKnot sh k #corner #line [312271.852,534701.498,0.0]
      addKnot sh k #corner #line [312135.617,534673.993,0.0]
      addKnot sh k #corner #line [311999.381,534701.498,0.0]
      addKnot sh k #corner #line [311888.129,534776.506,0.0]
      addKnot sh k #corner #line [311813.121,534887.757,0.0]
      addKnot sh k #corner #line [311785.617,535023.993,0.0]
      addKnot sh k #corner #line [311813.121,535160.229,0.0]
      addKnot sh k #corner #line [311888.129,535271.481,0.0]
      addKnot sh k #corner #line [311999.381,535346.488,0.0]
      addKnot sh k #corner #line [312135.617,535373.993,0.0]
      addKnot sh k #corner #line [312271.852,535346.488,0.0]
      addKnot sh k #corner #line [312383.104,535271.481,0.0]
      addKnot sh k #corner #line [312458.112,535160.229,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [309955.456,451117.407,0.0]
      addKnot sh k #corner #line [310360.378,450674.645,0.0]
      addKnot sh k #corner #line [309917.615,450269.723,0.0]
      addKnot sh k #corner #line [309512.694,450712.486,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [298433.448,546456.954,0.0]
      addKnot sh k #corner #line [298714.346,547206.017,0.0]
      addKnot sh k #corner #line [299463.409,546925.119,0.0]
      addKnot sh k #corner #line [299182.511,546176.056,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300596.573,523163.937,0.0]
      addKnot sh k #corner #line [300654.664,523761.118,0.0]
      addKnot sh k #corner #line [301450.906,523683.664,0.0]
      addKnot sh k #corner #line [301392.815,523086.482,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300343.562,515261.712,0.0]
      addKnot sh k #corner #line [300343.562,515861.712,0.0]
      addKnot sh k #corner #line [301043.562,515861.712,0.0]
      addKnot sh k #corner #line [301043.562,515261.712,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [300345.508,515111.710,0.0]
      addKnot sh k #corner #line [301045.508,515111.710,0.0]
      addKnot sh k #corner #line [301045.508,514511.710,0.0]
      addKnot sh k #corner #line [300345.508,514511.710,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276044.128,515668.588,0.0]
      addKnot sh k #corner #line [276744.128,515668.588,0.0]
      addKnot sh k #corner #line [276744.128,515068.588,0.0]
      addKnot sh k #corner #line [276044.128,515068.588,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [276046.257,514918.590,0.0]
      addKnot sh k #corner #line [276746.257,514918.590,0.0]
      addKnot sh k #corner #line [276746.257,514318.590,0.0]
      addKnot sh k #corner #line [276046.257,514318.590,0.0]
      close sh k
      addNewSpline sh
      k = numSplines sh
      addKnot sh k #corner #line [333712.822,462349.249,0.0]
      addKnot sh k #corner #line [333689.247,462466.022,0.0]
      addKnot sh k #corner #line [333624.954,462561.381,0.0]
      addKnot sh k #corner #line [333529.596,462625.673,0.0]
      addKnot sh k #corner #line [333412.822,462649.249,0.0]
      addKnot sh k #corner #line [333296.049,462625.673,0.0]
      addKnot sh k #corner #line [333200.690,462561.381,0.0]
      addKnot sh k #corner #line [333136.398,462466.022,0.0]
      addKnot sh k #corner #line [333112.822,462349.249,0.0]
      addKnot sh k #corner #line [333136.398,462232.475,0.0]
      addKnot sh k #corner #line [333200.690,462137.117,0.0]
      addKnot sh k #corner #line [333296.049,462072.824,0.0]
      addKnot sh k #corner #line [333412.822,462049.249,0.0]
      addKnot sh k #corner #line [333529.596,462072.824,0.0]
      addKnot sh k #corner #line [333624.954,462137.117,0.0]
      addKnot sh k #corner #line [333689.247,462232.475,0.0]
      addKnot sh k #corner #line [333712.822,462349.249,0.0]
      close sh k
      updateShape sh
      addModifier sh (Extrude amount:columnHeight capStart:true capEnd:true)
      append made sh
      -- WALL_OPEN_EDGES: source edges for REVIEW ONLY (hidden to avoid misleading walls)
      if makeReviewWalls do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REVIEW_WALL_OPEN_EDGES_")
        sh.wirecolor = (color 238 90 90)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278632.937,469149.727,0.0]
        addKnot sh k #corner #line [278583.275,469258.969,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319159.141,446119.666,0.0]
        addKnot sh k #corner #line [320457.288,444992.659,0.0]
        addKnot sh k #corner #line [321776.089,443889.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319027.072,445969.472,0.0]
        addKnot sh k #corner #line [320404.115,444775.282,0.0]
        addKnot sh k #corner #line [321804.299,443608.308,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315661.093,424714.436,0.0]
        addKnot sh k #corner #line [329936.910,444687.349,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315643.756,425034.123,0.0]
        addKnot sh k #corner #line [327942.659,442241.189,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322839.473,450607.951,0.0]
        addKnot sh k #corner #line [324824.026,448896.497,0.0]
        addKnot sh k #corner #line [326859.225,447245.590,0.0]
        addKnot sh k #corner #line [328943.224,445656.730,0.0]
        addKnot sh k #corner #line [331074.132,444131.358,0.0]
        addKnot sh k #corner #line [333250.015,442670.857,0.0]
        addKnot sh k #corner #line [335468.899,441276.554,0.0]
        addKnot sh k #corner #line [337728.771,439949.712,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322857.032,450325.046,0.0]
        addKnot sh k #corner #line [324533.232,448879.328,0.0]
        addKnot sh k #corner #line [326245.588,447476.622,0.0]
        addKnot sh k #corner #line [327992.997,446117.832,0.0]
        addKnot sh k #corner #line [329774.333,444803.834,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329774.333,444803.834,0.0]
        addKnot sh k #corner #line [331687.122,443468.432,0.0]
        addKnot sh k #corner #line [333634.949,442184.676,0.0]
        addKnot sh k #corner #line [335616.421,440953.484,0.0]
        addKnot sh k #corner #line [337630.117,439775.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323774.003,438472.586,0.0]
        addKnot sh k #corner #line [326972.577,442947.625,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323935.136,438354.081,0.0]
        addKnot sh k #corner #line [327133.613,442828.985,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321776.089,443889.892,0.0]
        addKnot sh k #corner #line [323452.707,445942.082,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321804.299,443608.308,0.0]
        addKnot sh k #corner #line [323480.914,445660.493,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323480.914,445660.493,0.0]
        addKnot sh k #corner #line [325210.147,444282.696,0.0]
        addKnot sh k #corner #line [326972.577,442947.625,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323452.707,445942.082,0.0]
        addKnot sh k #corner #line [325565.299,444260.637,0.0]
        addKnot sh k #corner #line [327727.297,442643.213,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316863.340,443811.669,0.0]
        addKnot sh k #corner #line [318781.859,442152.654,0.0]
        addKnot sh k #corner #line [320743.514,440544.873,0.0]
        addKnot sh k #corner #line [322746.937,438989.450,0.0]
        addKnot sh k #corner #line [324790.731,437487.467,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317145.090,443829.212,0.0]
        addKnot sh k #corner #line [319024.928,442209.605,0.0]
        addKnot sh k #corner #line [320946.060,440639.201,0.0]
        addKnot sh k #corner #line [322907.199,439119.052,0.0]
        addKnot sh k #corner #line [324907.030,437650.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311807.234,449145.180,0.0]
        addKnot sh k #corner #line [317927.354,455043.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314429.907,446740.612,0.0]
        addKnot sh k #corner #line [320002.229,452550.235,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311807.234,449145.180,0.0]
        addKnot sh k #corner #line [317927.354,455043.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316184.670,486217.120,0.0]
        addKnot sh k #corner #line [316648.295,485221.582,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315919.820,486316.445,0.0]
        addKnot sh k #corner #line [316467.660,485135.726,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316739.185,486688.794,0.0]
        addKnot sh k #corner #line [317280.515,485522.078,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316639.873,486423.980,0.0]
        addKnot sh k #corner #line [317099.881,485436.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316648.295,485221.582,0.0]
        addKnot sh k #corner #line [316866.009,484767.702,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316467.660,485135.726,0.0]
        addKnot sh k #corner #line [316771.501,484504.462,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317280.515,485522.078,0.0]
        addKnot sh k #corner #line [317590.041,484879.248,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317099.881,485436.222,0.0]
        addKnot sh k #corner #line [317320.725,484975.904,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317590.041,484879.248,0.0]
        addKnot sh k #corner #line [316771.501,484504.462,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317320.725,484975.904,0.0]
        addKnot sh k #corner #line [316866.009,484767.702,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316639.873,486423.980,0.0]
        addKnot sh k #corner #line [316184.670,486217.120,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316739.185,486688.794,0.0]
        addKnot sh k #corner #line [315919.820,486316.445,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320488.362,452776.472,0.0]
        addKnot sh k #corner #line [320975.027,453283.794,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320975.027,453283.794,0.0]
        addKnot sh k #corner #line [320830.698,453422.247,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320830.698,453422.247,0.0]
        addKnot sh k #corner #line [320344.033,452914.925,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320344.033,452914.925,0.0]
        addKnot sh k #corner #line [320488.362,452776.472,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321936.400,454574.882,0.0]
        addKnot sh k #corner #line [321869.091,454504.716,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321869.091,454504.716,0.0]
        addKnot sh k #corner #line [322013.420,454366.264,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322013.420,454366.264,0.0]
        addKnot sh k #corner #line [322219.232,454580.812,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304839.526,534008.665,0.0]
        addKnot sh k #corner #line [298034.228,535651.181,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298034.228,535651.181,0.0]
        addKnot sh k #corner #line [297987.303,535456.764,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297987.303,535456.764,0.0]
        addKnot sh k #corner #line [304792.643,533814.238,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296044.478,535925.681,0.0]
        addKnot sh k #corner #line [296529.173,535808.696,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296529.173,535808.696,0.0]
        addKnot sh k #corner #line [296576.097,536003.113,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296576.097,536003.113,0.0]
        addKnot sh k #corner #line [296091.402,536120.098,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296091.402,536120.098,0.0]
        addKnot sh k #corner #line [296044.478,535925.681,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306353.951,538735.330,0.0]
        addKnot sh k #corner #line [305785.418,536821.851,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306162.982,538794.751,0.0]
        addKnot sh k #corner #line [305620.293,536972.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306353.951,538735.330,0.0]
        addKnot sh k #corner #line [306162.982,538794.751,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293646.587,514854.226,0.0]
        addKnot sh k #corner #line [294145.499,514858.096,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294145.499,514858.096,0.0]
        addKnot sh k #corner #line [294143.948,515058.090,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294143.948,515058.090,0.0]
        addKnot sh k #corner #line [293545.123,515053.445,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302744.700,515124.799,0.0]
        addKnot sh k #corner #line [295642.234,515069.711,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295642.234,515069.711,0.0]
        addKnot sh k #corner #line [295643.786,514869.717,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295643.786,514869.717,0.0]
        addKnot sh k #corner #line [302646.319,514924.030,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293883.475,509165.488,0.0]
        addKnot sh k #corner #line [294382.531,509201.927,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294382.531,509201.927,0.0]
        addKnot sh k #corner #line [294367.967,509401.396,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294367.967,509401.396,0.0]
        addKnot sh k #corner #line [293868.910,509364.957,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293868.910,509364.957,0.0]
        addKnot sh k #corner #line [293883.475,509165.488,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296262.569,509539.729,0.0]
        addKnot sh k #corner #line [295862.321,509510.505,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295862.321,509510.505,0.0]
        addKnot sh k #corner #line [295876.885,509311.036,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295876.885,509311.036,0.0]
        addKnot sh k #corner #line [296277.200,509340.265,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296906.926,539231.461,0.0]
        addKnot sh k #corner #line [299311.403,538550.745,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299311.403,538550.745,0.0]
        addKnot sh k #corner #line [299365.882,538743.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299365.882,538743.182,0.0]
        addKnot sh k #corner #line [296961.406,539423.898,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296961.406,539423.898,0.0]
        addKnot sh k #corner #line [296906.926,539231.461,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305620.293,536972.537,0.0]
        addKnot sh k #corner #line [300809.160,538334.585,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300809.160,538334.585,0.0]
        addKnot sh k #corner #line [300754.680,538142.148,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300754.680,538142.148,0.0]
        addKnot sh k #corner #line [305565.798,536780.104,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324695.442,461567.025,0.0]
        addKnot sh k #corner #line [319872.201,456918.319,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324556.650,461711.028,0.0]
        addKnot sh k #corner #line [319589.566,456923.683,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324695.442,461567.025,0.0]
        addKnot sh k #corner #line [324556.650,461711.028,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302646.319,514924.030,0.0]
        addKnot sh k #corner #line [302663.183,513860.592,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302663.183,513860.592,0.0]
        addKnot sh k #corner #line [302863.080,513867.434,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302846.313,514925.581,0.0]
        addKnot sh k #corner #line [302863.080,513867.434,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302924.652,512068.487,0.0]
        addKnot sh k #corner #line [302929.141,511971.825,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302924.652,512068.487,0.0]
        addKnot sh k #corner #line [302724.756,512061.645,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302724.756,512061.645,0.0]
        addKnot sh k #corner #line [302729.362,511962.424,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302744.700,515124.799,0.0]
        addKnot sh k #corner #line [302844.697,515125.574,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302844.697,515125.574,0.0]
        addKnot sh k #corner #line [302846.249,514925.580,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313521.142,476294.916,0.0]
        addKnot sh k #corner #line [313261.826,476756.386,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313261.826,476756.386,0.0]
        addKnot sh k #corner #line [313087.468,476658.408,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313087.468,476658.408,0.0]
        addKnot sh k #corner #line [313348.685,476193.556,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311946.222,478689.330,0.0]
        addKnot sh k #corner #line [312205.671,478227.623,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312205.671,478227.623,0.0]
        addKnot sh k #corner #line [312380.029,478325.600,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312380.029,478325.600,0.0]
        addKnot sh k #corner #line [312122.527,478783.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313521.142,476294.916,0.0]
        addKnot sh k #corner #line [307314.143,472646.825,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307314.143,472646.825,0.0]
        addKnot sh k #corner #line [307415.483,472474.401,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307415.483,472474.401,0.0]
        addKnot sh k #corner #line [313619.138,476120.526,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313619.138,476120.526,0.0]
        addKnot sh k #corner #line [313521.142,476294.916,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305689.291,471459.852,0.0]
        addKnot sh k #corner #line [306122.301,471714.348,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306122.301,471714.348,0.0]
        addKnot sh k #corner #line [306020.961,471886.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306020.961,471886.773,0.0]
        addKnot sh k #corner #line [305587.951,471632.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305193.445,477804.424,0.0]
        addKnot sh k #corner #line [306210.017,475841.252,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305104.604,477535.896,0.0]
        addKnot sh k #corner #line [306128.240,475570.489,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302960.198,476457.674,0.0]
        addKnot sh k #corner #line [303406.979,476682.319,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303406.979,476682.319,0.0]
        addKnot sh k #corner #line [303317.136,476861.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303317.136,476861.003,0.0]
        addKnot sh k #corner #line [302870.354,476636.359,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302870.354,476636.359,0.0]
        addKnot sh k #corner #line [302960.198,476457.674,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305193.445,477804.424,0.0]
        addKnot sh k #corner #line [304657.269,477534.831,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304657.269,477534.831,0.0]
        addKnot sh k #corner #line [304747.112,477356.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304747.112,477356.147,0.0]
        addKnot sh k #corner #line [305104.604,477535.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326587.708,439999.524,0.0]
        addKnot sh k #corner #line [326702.063,440163.607,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326587.702,439999.529,0.0]
        addKnot sh k #corner #line [326702.056,440163.611,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316510.505,456841.274,0.0]
        addKnot sh k #corner #line [316779.215,457087.021,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316779.215,457087.021,0.0]
        addKnot sh k #corner #line [316644.240,457234.608,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316644.240,457234.608,0.0]
        addKnot sh k #corner #line [316375.395,456988.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323016.769,463062.585,0.0]
        addKnot sh k #corner #line [317751.139,458246.919,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317751.139,458246.919,0.0]
        addKnot sh k #corner #line [317886.114,458099.333,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317886.114,458099.333,0.0]
        addKnot sh k #corner #line [323299.397,463050.034,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278143.315,536484.477,0.0]
        addKnot sh k #corner #line [278780.077,536354.283,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278780.077,536354.283,0.0]
        addKnot sh k #corner #line [278820.141,536550.229,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278820.141,536550.229,0.0]
        addKnot sh k #corner #line [278379.325,536640.360,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280142.841,536279.785,0.0]
        addKnot sh k #corner #line [279995.818,536309.846,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279995.818,536309.846,0.0]
        addKnot sh k #corner #line [279955.754,536113.900,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279955.754,536113.900,0.0]
        addKnot sh k #corner #line [280200.703,536063.817,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279182.743,541064.283,0.0]
        addKnot sh k #corner #line [278986.099,540266.607,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278986.099,540266.607,0.0]
        addKnot sh k #corner #line [279180.742,540220.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279352.470,540918.640,0.0]
        addKnot sh k #corner #line [279180.742,540220.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278904.788,539052.774,0.0]
        addKnot sh k #corner #line [278691.770,538107.509,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278904.788,539052.774,0.0]
        addKnot sh k #corner #line [278710.145,539098.767,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278710.145,539098.767,0.0]
        addKnot sh k #corner #line [278474.591,538051.152,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280025.977,544218.384,0.0]
        addKnot sh k #corner #line [282816.265,543428.436,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280163.934,543971.467,0.0]
        addKnot sh k #corner #line [282665.614,543263.225,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283329.356,539921.655,0.0]
        addKnot sh k #corner #line [281971.379,540262.092,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283281.040,540139.956,0.0]
        addKnot sh k #corner #line [282117.059,540431.760,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284205.109,542827.384,0.0]
        addKnot sh k #corner #line [283475.037,540091.322,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284012.672,542881.864,0.0]
        addKnot sh k #corner #line [283281.040,540139.956,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280025.977,544218.384,0.0]
        addKnot sh k #corner #line [279729.358,543153.076,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279729.358,543153.076,0.0]
        addKnot sh k #corner #line [279922.612,543101.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280163.934,543971.467,0.0]
        addKnot sh k #corner #line [279922.612,543101.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279613.495,541942.052,0.0]
        addKnot sh k #corner #line [279401.103,541112.636,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279613.495,541942.052,0.0]
        addKnot sh k #corner #line [279420.241,541993.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279420.241,541993.573,0.0]
        addKnot sh k #corner #line [279182.743,541064.283,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284163.322,543047.075,0.0]
        addKnot sh k #corner #line [285654.708,542624.854,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284205.109,542827.384,0.0]
        addKnot sh k #corner #line [285504.058,542459.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287598.058,538851.513,0.0]
        addKnot sh k #corner #line [284832.831,539544.741,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287646.691,539045.510,0.0]
        addKnot sh k #corner #line [284978.512,539714.409,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285696.495,542405.163,0.0]
        addKnot sh k #corner #line [284978.512,539714.409,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285504.058,542459.643,0.0]
        addKnot sh k #corner #line [284784.515,539763.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284832.831,539544.741,0.0]
        addKnot sh k #corner #line [283329.356,539921.655,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284784.515,539763.043,0.0]
        addKnot sh k #corner #line [283475.037,540091.322,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285654.708,542624.854,0.0]
        addKnot sh k #corner #line [288493.072,541821.294,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285696.495,542405.163,0.0]
        addKnot sh k #corner #line [288343.222,541655.857,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282858.051,543208.745,0.0]
        addKnot sh k #corner #line [282117.059,540431.760,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282665.614,543263.225,0.0]
        addKnot sh k #corner #line [281923.062,540480.394,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282816.265,543428.436,0.0]
        addKnot sh k #corner #line [284163.322,543047.075,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282858.051,543208.745,0.0]
        addKnot sh k #corner #line [284012.672,542881.864,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281971.379,540262.092,0.0]
        addKnot sh k #corner #line [281292.438,540432.299,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281923.062,540480.394,0.0]
        addKnot sh k #corner #line [281244.026,540650.625,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281292.438,540432.299,0.0]
        addKnot sh k #corner #line [280629.602,537607.567,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281098.441,540480.933,0.0]
        addKnot sh k #corner #line [280455.496,537746.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281098.441,540480.933,0.0]
        addKnot sh k #corner #line [279352.470,540918.640,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281244.026,540650.625,0.0]
        addKnot sh k #corner #line [279401.103,541112.636,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280200.703,536063.817,0.0]
        addKnot sh k #corner #line [280395.995,536023.887,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280395.995,536023.887,0.0]
        addKnot sh k #corner #line [280436.058,536219.833,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280436.058,536219.833,0.0]
        addKnot sh k #corner #line [280338.788,536239.721,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286707.764,534937.498,0.0]
        addKnot sh k #corner #line [281611.735,535979.450,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281611.735,535979.450,0.0]
        addKnot sh k #corner #line [281571.671,535783.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281571.671,535783.504,0.0]
        addKnot sh k #corner #line [286764.810,534721.697,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278691.770,538107.509,0.0]
        addKnot sh k #corner #line [280455.496,537746.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278648.890,537912.139,0.0]
        addKnot sh k #corner #line [280412.567,537551.531,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278648.890,537912.139,0.0]
        addKnot sh k #corner #line [278379.325,536640.360,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278474.591,538051.152,0.0]
        addKnot sh k #corner #line [278143.315,536484.477,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280629.602,537607.567,0.0]
        addKnot sh k #corner #line [280338.788,536239.721,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280412.567,537551.531,0.0]
        addKnot sh k #corner #line [280142.841,536279.785,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306210.017,475841.252,0.0]
        addKnot sh k #corner #line [312024.530,478958.233,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306128.240,475570.489,0.0]
        addKnot sh k #corner #line [312122.527,478783.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312024.530,478958.233,0.0]
        addKnot sh k #corner #line [312122.527,478783.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296345.254,470326.138,0.0]
        addKnot sh k #corner #line [297201.954,468766.957,0.0]
        addKnot sh k #corner #line [298087.489,467223.970,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296121.691,470319.755,0.0]
        addKnot sh k #corner #line [297003.097,468712.630,0.0]
        addKnot sh k #corner #line [297915.057,467122.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295188.248,472548.323,0.0]
        addKnot sh k #corner #line [296200.069,470597.337,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295009.557,472458.491,0.0]
        addKnot sh k #corner #line [295975.444,470593.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300551.758,473922.237,0.0]
        addKnot sh k #corner #line [301010.053,473053.717,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300328.128,473918.780,0.0]
        addKnot sh k #corner #line [300833.782,472959.224,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302280.538,474932.732,0.0]
        addKnot sh k #corner #line [302772.753,473998.646,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302149.185,474751.835,0.0]
        addKnot sh k #corner #line [302596.483,473904.153,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302782.284,476366.792,0.0]
        addKnot sh k #corner #line [302959.264,476017.774,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302959.264,476017.774,0.0]
        addKnot sh k #corner #line [303136.813,476109.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302871.121,476635.322,0.0]
        addKnot sh k #corner #line [303136.813,476109.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303689.265,475044.584,0.0]
        addKnot sh k #corner #line [303965.705,474524.688,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303689.265,475044.584,0.0]
        addKnot sh k #corner #line [303511.716,474952.506,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303511.716,474952.506,0.0]
        addKnot sh k #corner #line [303742.239,474518.357,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296250.761,470502.408,0.0]
        addKnot sh k #corner #line [298454.136,471683.569,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296345.254,470326.138,0.0]
        addKnot sh k #corner #line [298636.717,471554.520,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301016.362,472830.174,0.0]
        addKnot sh k #corner #line [301278.432,472970.662,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301278.432,472970.662,0.0]
        addKnot sh k #corner #line [301183.939,473146.932,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301183.939,473146.932,0.0]
        addKnot sh k #corner #line [301010.053,473053.717,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302596.483,473904.153,0.0]
        addKnot sh k #corner #line [301800.884,473477.657,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301800.884,473477.657,0.0]
        addKnot sh k #corner #line [301895.376,473301.387,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301895.376,473301.387,0.0]
        addKnot sh k #corner #line [302779.061,473775.103,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299833.457,475107.909,0.0]
        addKnot sh k #corner #line [301620.288,476006.372,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300012.694,474974.174,0.0]
        addKnot sh k #corner #line [301620.843,475782.791,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302772.753,473998.646,0.0]
        addKnot sh k #corner #line [303742.239,474518.357,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302779.061,473775.103,0.0]
        addKnot sh k #corner #line [303836.732,474342.087,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301620.288,476006.372,0.0]
        addKnot sh k #corner #line [302871.121,476635.322,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301799.526,475872.637,0.0]
        addKnot sh k #corner #line [302782.284,476366.792,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301799.526,475872.637,0.0]
        addKnot sh k #corner #line [302280.538,474932.732,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301620.843,475782.791,0.0]
        addKnot sh k #corner #line [302057.007,474929.327,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300459.581,474099.729,0.0]
        addKnot sh k #corner #line [302057.007,474929.327,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300551.758,473922.237,0.0]
        addKnot sh k #corner #line [302149.185,474751.835,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300012.694,474974.174,0.0]
        addKnot sh k #corner #line [300459.581,474099.729,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299834.011,474884.328,0.0]
        addKnot sh k #corner #line [300328.128,473918.780,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298087.489,467223.970,0.0]
        addKnot sh k #corner #line [305415.526,471530.937,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298102.572,467000.849,0.0]
        addKnot sh k #corner #line [305689.291,471459.853,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295188.248,472548.323,0.0]
        addKnot sh k #corner #line [295826.713,472869.360,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295826.713,472869.360,0.0]
        addKnot sh k #corner #line [295736.867,473048.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295736.867,473048.043,0.0]
        addKnot sh k #corner #line [295009.013,472682.060,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297421.235,473894.984,0.0]
        addKnot sh k #corner #line [296719.624,473542.197,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296719.624,473542.197,0.0]
        addKnot sh k #corner #line [296809.470,473363.514,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296809.470,473363.514,0.0]
        addKnot sh k #corner #line [297421.787,473671.402,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303836.732,474342.087,0.0]
        addKnot sh k #corner #line [304076.585,473898.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304076.585,473898.961,0.0]
        addKnot sh k #corner #line [304251.373,473996.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303965.705,474524.688,0.0]
        addKnot sh k #corner #line [304251.373,473996.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304980.510,472685.320,0.0]
        addKnot sh k #corner #line [305689.291,471459.853,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304980.510,472685.320,0.0]
        addKnot sh k #corner #line [304805.721,472588.098,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304805.721,472588.098,0.0]
        addKnot sh k #corner #line [305415.526,471530.937,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297600.470,473761.249,0.0]
        addKnot sh k #corner #line [298630.406,471778.062,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297421.787,473671.402,0.0]
        addKnot sh k #corner #line [298454.136,471683.569,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297600.470,473761.249,0.0]
        addKnot sh k #corner #line [298238.546,474082.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298238.546,474082.089,0.0]
        addKnot sh k #corner #line [298148.700,474260.772,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298148.700,474260.772,0.0]
        addKnot sh k #corner #line [297421.235,473894.984,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299833.457,475107.909,0.0]
        addKnot sh k #corner #line [299131.457,474754.926,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299131.457,474754.926,0.0]
        addKnot sh k #corner #line [299221.303,474576.243,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299221.303,474576.243,0.0]
        addKnot sh k #corner #line [299834.011,474884.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298630.406,471778.062,0.0]
        addKnot sh k #corner #line [300833.782,472959.224,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298636.717,471554.520,0.0]
        addKnot sh k #corner #line [301016.362,472830.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267937.577,526832.964,0.0]
        addKnot sh k #corner #line [268952.487,526734.244,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267675.203,526617.352,0.0]
        addKnot sh k #corner #line [269169.233,526472.029,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267993.028,529500.324,0.0]
        addKnot sh k #corner #line [269481.508,529315.084,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268202.099,529232.454,0.0]
        addKnot sh k #corner #line [269214.296,529106.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267993.028,529500.324,0.0]
        addKnot sh k #corner #line [267943.260,529090.199,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267943.260,529090.199,0.0]
        addKnot sh k #corner #line [268181.815,529063.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268202.099,529232.454,0.0]
        addKnot sh k #corner #line [268181.815,529063.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267962.008,527075.937,0.0]
        addKnot sh k #corner #line [267937.577,526832.964,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267962.008,527075.937,0.0]
        addKnot sh k #corner #line [267723.453,527102.315,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267723.453,527102.315,0.0]
        addKnot sh k #corner #line [267675.203,526617.352,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269481.508,529315.084,0.0]
        addKnot sh k #corner #line [269323.503,527964.387,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269214.296,529106.487,0.0]
        addKnot sh k #corner #line [269084.968,527990.860,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296341.199,511561.683,0.0]
        addKnot sh k #corner #line [296469.292,509454.591,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296132.018,511752.060,0.0]
        addKnot sh k #corner #line [296269.828,509439.959,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297370.794,501878.542,0.0]
        addKnot sh k #corner #line [301860.084,502625.305,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297206.323,501648.435,0.0]
        addKnot sh k #corner #line [302128.648,502467.230,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296469.292,509454.591,0.0]
        addKnot sh k #corner #line [296693.615,506920.564,0.0]
        addKnot sh k #corner #line [296994.207,504394.450,0.0]
        addKnot sh k #corner #line [297370.794,501878.542,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296269.828,509439.959,0.0]
        addKnot sh k #corner #line [296501.596,506833.541,0.0]
        addKnot sh k #corner #line [296813.861,504235.538,0.0]
        addKnot sh k #corner #line [297206.323,501648.435,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296132.018,511752.060,0.0]
        addKnot sh k #corner #line [302724.725,512062.316,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296341.199,511561.683,0.0]
        addKnot sh k #corner #line [302734.127,511862.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285053.686,511030.483,0.0]
        addKnot sh k #corner #line [285058.917,510923.009,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284849.154,511120.969,0.0]
        addKnot sh k #corner #line [284859.277,510910.775,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290447.720,511284.329,0.0]
        addKnot sh k #corner #line [290500.302,510303.719,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290247.941,511274.928,0.0]
        addKnot sh k #corner #line [290306.616,510191.880,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292445.510,511378.346,0.0]
        addKnot sh k #corner #line [292502.642,510324.055,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292245.731,511368.945,0.0]
        addKnot sh k #corner #line [292297.052,510411.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293544.295,511430.056,0.0]
        addKnot sh k #corner #line [293568.824,510948.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293568.824,510948.883,0.0]
        addKnot sh k #corner #line [293768.462,510960.992,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293739.315,511539.344,0.0]
        addKnot sh k #corner #line [293768.462,510960.992,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293841.112,509763.193,0.0]
        addKnot sh k #corner #line [293883.523,509166.141,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293841.112,509763.193,0.0]
        addKnot sh k #corner #line [293641.474,509751.084,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293641.474,509751.084,0.0]
        addKnot sh k #corner #line [293669.431,509350.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285044.285,511230.262,0.0]
        addKnot sh k #corner #line [287641.358,511352.482,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285053.686,511030.483,0.0]
        addKnot sh k #corner #line [287550.924,511148.005,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285107.035,508522.501,0.0]
        addKnot sh k #corner #line [285919.993,508582.121,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285919.993,508582.121,0.0]
        addKnot sh k #corner #line [285905.365,508781.585,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285905.365,508781.585,0.0]
        addKnot sh k #corner #line [285192.192,508729.283,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287685.497,508912.135,0.0]
        addKnot sh k #corner #line [287002.419,508862.040,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287002.419,508862.040,0.0]
        addKnot sh k #corner #line [287017.047,508662.575,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287017.047,508662.575,0.0]
        addKnot sh k #corner #line [287799.804,508719.980,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290447.720,511284.329,0.0]
        addKnot sh k #corner #line [291347.370,511326.667,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291347.370,511326.667,0.0]
        addKnot sh k #corner #line [291337.968,511526.446,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291337.968,511526.446,0.0]
        addKnot sh k #corner #line [290338.373,511479.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292336.162,511573.422,0.0]
        addKnot sh k #corner #line [292037.194,511559.352,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292037.194,511559.352,0.0]
        addKnot sh k #corner #line [292046.596,511359.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292046.596,511359.573,0.0]
        addKnot sh k #corner #line [292245.731,511368.945,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290577.732,509124.242,0.0]
        addKnot sh k #corner #line [292372.912,509255.895,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290492.572,508917.459,0.0]
        addKnot sh k #corner #line [292487.216,509063.740,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292336.162,511573.422,0.0]
        addKnot sh k #corner #line [293534.893,511629.835,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292445.510,511378.346,0.0]
        addKnot sh k #corner #line [293544.295,511430.056,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292572.376,509270.523,0.0]
        addKnot sh k #corner #line [293669.431,509350.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292487.216,509063.740,0.0]
        addKnot sh k #corner #line [293883.523,509166.141,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292502.642,510324.055,0.0]
        addKnot sh k #corner #line [292572.376,509270.523,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292309.068,510212.223,0.0]
        addKnot sh k #corner #line [292372.912,509255.895,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290500.302,510303.719,0.0]
        addKnot sh k #corner #line [292297.052,510411.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290512.318,510104.080,0.0]
        addKnot sh k #corner #line [292309.068,510212.223,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290512.318,510104.080,0.0]
        addKnot sh k #corner #line [290577.732,509124.242,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290306.616,510191.880,0.0]
        addKnot sh k #corner #line [290378.267,509109.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284845.242,514986.071,0.0]
        addKnot sh k #corner #line [293544.980,515053.547,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284946.842,514786.853,0.0]
        addKnot sh k #corner #line [293446.592,514852.778,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293446.592,514852.778,0.0]
        addKnot sh k #corner #line [293461.577,513835.846,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293461.577,513835.846,0.0]
        addKnot sh k #corner #line [293661.492,513842.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293646.587,514854.226,0.0]
        addKnot sh k #corner #line [293661.492,513842.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293717.080,512042.881,0.0]
        addKnot sh k #corner #line [293739.315,511539.344,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293717.080,512042.881,0.0]
        addKnot sh k #corner #line [293517.165,512036.704,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293517.165,512036.704,0.0]
        addKnot sh k #corner #line [293534.893,511629.835,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284946.842,514786.853,0.0]
        addKnot sh k #corner #line [284979.034,513008.105,0.0]
        addKnot sh k #corner #line [285044.285,511230.262,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284746.848,514785.300,0.0]
        addKnot sh k #corner #line [284780.491,512952.645,0.0]
        addKnot sh k #corner #line [284849.154,511120.969,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287750.703,511157.406,0.0]
        addKnot sh k #corner #line [287884.961,508926.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287550.924,511148.005,0.0]
        addKnot sh k #corner #line [287685.497,508912.135,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287641.358,511352.482,0.0]
        addKnot sh k #corner #line [290338.373,511479.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287750.703,511157.406,0.0]
        addKnot sh k #corner #line [290247.941,511274.928,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287799.804,508719.980,0.0]
        addKnot sh k #corner #line [288612.302,508779.566,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288612.302,508779.566,0.0]
        addKnot sh k #corner #line [288597.674,508979.031,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288597.674,508979.031,0.0]
        addKnot sh k #corner #line [287884.961,508926.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290378.267,509109.614,0.0]
        addKnot sh k #corner #line [289694.727,509059.485,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289694.727,509059.485,0.0]
        addKnot sh k #corner #line [289709.356,508860.021,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289709.356,508860.021,0.0]
        addKnot sh k #corner #line [290492.572,508917.459,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287111.796,513283.706,0.0]
        addKnot sh k #corner #line [291373.809,513316.767,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287112.572,513183.709,0.0]
        addKnot sh k #corner #line [291474.580,513217.546,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287111.796,513283.706,0.0]
        addKnot sh k #corner #line [287112.572,513183.709,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301551.460,506695.490,0.0]
        addKnot sh k #corner #line [301813.357,504577.716,0.0]
        addKnot sh k #corner #line [302128.648,502467.230,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301312.922,506669.045,0.0]
        addKnot sh k #corner #line [301562.159,504643.881,0.0]
        addKnot sh k #corner #line [301860.084,502625.305,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301551.460,506695.490,0.0]
        addKnot sh k #corner #line [301312.922,506669.045,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302929.141,511971.825,0.0]
        addKnot sh k #corner #line [303102.819,509277.717,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302729.362,511962.424,0.0]
        addKnot sh k #corner #line [302903.487,509261.390,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303102.819,509277.717,0.0]
        addKnot sh k #corner #line [302903.487,509261.390,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291474.580,513217.546,0.0]
        addKnot sh k #corner #line [291471.352,513634.827,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291471.352,513634.827,0.0]
        addKnot sh k #corner #line [291371.355,513634.053,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291371.355,513634.053,0.0]
        addKnot sh k #corner #line [291373.809,513316.767,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291362.052,514836.527,0.0]
        addKnot sh k #corner #line [291363.619,514634.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291363.619,514634.023,0.0]
        addKnot sh k #corner #line [291463.616,514634.797,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291463.616,514634.797,0.0]
        addKnot sh k #corner #line [291462.049,514837.301,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291462.049,514837.301,0.0]
        addKnot sh k #corner #line [291362.052,514836.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298961.098,470003.905,0.0]
        addKnot sh k #corner #line [302716.878,472017.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299008.345,469915.770,0.0]
        addKnot sh k #corner #line [302852.258,471976.379,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298961.098,470003.905,0.0]
        addKnot sh k #corner #line [299008.345,469915.770,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302852.258,471976.379,0.0]
        addKnot sh k #corner #line [302675.602,472305.932,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302675.602,472305.932,0.0]
        addKnot sh k #corner #line [302587.466,472258.688,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302587.466,472258.688,0.0]
        addKnot sh k #corner #line [302716.878,472017.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301998.810,473356.834,0.0]
        addKnot sh k #corner #line [302115.018,473140.046,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302115.018,473140.046,0.0]
        addKnot sh k #corner #line [302203.154,473187.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302203.154,473187.291,0.0]
        addKnot sh k #corner #line [302086.946,473404.079,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302086.946,473404.079,0.0]
        addKnot sh k #corner #line [301998.810,473356.834,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314412.334,449545.092,0.0]
        addKnot sh k #corner #line [317480.596,452502.334,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314481.730,449473.090,0.0]
        addKnot sh k #corner #line [317621.991,452499.728,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314412.334,449545.092,0.0]
        addKnot sh k #corner #line [314481.730,449473.090,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317621.991,452499.728,0.0]
        addKnot sh k #corner #line [317362.514,452768.957,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317362.514,452768.957,0.0]
        addKnot sh k #corner #line [317290.511,452699.562,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317290.511,452699.562,0.0]
        addKnot sh k #corner #line [317480.596,452502.334,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316425.875,453596.694,0.0]
        addKnot sh k #corner #line [316596.565,453419.589,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316596.565,453419.589,0.0]
        addKnot sh k #corner #line [316668.568,453488.983,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316668.568,453488.983,0.0]
        addKnot sh k #corner #line [316497.877,453666.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316497.877,453666.089,0.0]
        addKnot sh k #corner #line [316425.875,453596.694,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319872.201,456918.319,0.0]
        addKnot sh k #corner #line [321033.830,455737.630,0.0]
        addKnot sh k #corner #line [322219.232,454580.812,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319589.566,456923.683,0.0]
        addKnot sh k #corner #line [320751.039,455737.349,0.0]
        addKnot sh k #corner #line [321936.400,454574.882,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276544.095,525855.142,0.0]
        addKnot sh k #corner #line [278337.149,525680.733,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276723.779,525636.720,0.0]
        addKnot sh k #corner #line [278218.184,525491.361,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276622.064,524516.270,0.0]
        addKnot sh k #corner #line [278115.105,524371.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276406.197,524336.323,0.0]
        addKnot sh k #corner #line [278193.953,524162.430,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294051.879,524051.726,0.0]
        addKnot sh k #corner #line [293925.542,522632.242,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293852.818,524071.088,0.0]
        addKnot sh k #corner #line [293742.791,522850.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294051.879,524051.726,0.0]
        addKnot sh k #corner #line [293852.818,524071.088,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292249.747,522996.188,0.0]
        addKnot sh k #corner #line [293742.791,522850.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292132.139,522806.684,0.0]
        addKnot sh k #corner #line [293925.542,522632.242,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290978.071,524451.164,0.0]
        addKnot sh k #corner #line [292271.773,524325.333,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291157.493,524232.769,0.0]
        addKnot sh k #corner #line [292152.797,524135.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276723.779,525636.720,0.0]
        addKnot sh k #corner #line [276622.064,524516.270,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276544.095,525855.142,0.0]
        addKnot sh k #corner #line [276406.197,524336.323,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278417.244,525471.999,0.0]
        addKnot sh k #corner #line [278314.176,524351.680,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278218.184,525491.361,0.0]
        addKnot sh k #corner #line [278115.105,524371.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292351.857,524116.600,0.0]
        addKnot sh k #corner #line [292249.747,522996.188,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292152.797,524135.961,0.0]
        addKnot sh k #corner #line [292050.671,523015.552,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291055.293,523112.372,0.0]
        addKnot sh k #corner #line [292050.671,523015.552,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290839.513,522932.416,0.0]
        addKnot sh k #corner #line [292132.139,522806.684,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279631.215,525554.861,0.0]
        addKnot sh k #corner #line [279491.595,524036.210,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279412.547,525375.187,0.0]
        addKnot sh k #corner #line [279309.537,524254.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291157.493,524232.769,0.0]
        addKnot sh k #corner #line [291055.293,523112.372,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290978.071,524451.164,0.0]
        addKnot sh k #corner #line [290839.513,522932.416,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278314.176,524351.680,0.0]
        addKnot sh k #corner #line [279309.537,524254.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278196.191,524162.212,0.0]
        addKnot sh k #corner #line [279491.595,524036.210,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278337.149,525680.733,0.0]
        addKnot sh k #corner #line [279631.215,525554.861,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278417.244,525471.999,0.0]
        addKnot sh k #corner #line [279412.547,525375.187,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292271.773,524325.333,0.0]
        addKnot sh k #corner #line [293462.011,524209.565,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292351.857,524116.600,0.0]
        addKnot sh k #corner #line [293442.649,524010.505,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293462.011,524209.565,0.0]
        addKnot sh k #corner #line [293442.649,524010.505,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269323.503,527964.387,0.0]
        addKnot sh k #corner #line [269167.756,526472.173,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269084.968,527990.860,0.0]
        addKnot sh k #corner #line [268952.487,526734.244,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301042.429,515461.605,0.0]
        addKnot sh k #corner #line [302643.286,515474.022,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301043.980,515261.611,0.0]
        addKnot sh k #corner #line [302843.935,515275.572,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301042.429,515461.605,0.0]
        addKnot sh k #corner #line [301043.980,515261.611,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305565.798,536780.104,0.0]
        addKnot sh k #corner #line [305351.876,536005.722,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305351.876,536005.722,0.0]
        addKnot sh k #corner #line [305545.531,535955.692,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305785.400,536821.786,0.0]
        addKnot sh k #corner #line [305545.531,535955.692,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305095.294,534212.911,0.0]
        addKnot sh k #corner #line [305010.444,533864.563,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305095.294,534212.911,0.0]
        addKnot sh k #corner #line [304901.639,534262.941,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304901.639,534262.941,0.0]
        addKnot sh k #corner #line [304839.526,534008.665,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336346.389,437917.349,0.0]
        addKnot sh k #corner #line [337505.458,439961.384,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336520.365,437818.696,0.0]
        addKnot sh k #corner #line [337679.434,439862.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336346.389,437917.349,0.0]
        addKnot sh k #corner #line [336520.365,437818.696,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337505.458,439961.384,0.0]
        addKnot sh k #corner #line [337679.434,439862.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305010.444,533864.563,0.0]
        addKnot sh k #corner #line [304420.092,531213.908,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304792.643,533814.238,0.0]
        addKnot sh k #corner #line [304224.145,531253.969,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304420.092,531213.908,0.0]
        addKnot sh k #corner #line [304224.145,531253.969,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317376.421,444092.290,0.0]
        addKnot sh k #corner #line [317746.357,444512.995,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317746.357,444512.995,0.0]
        addKnot sh k #corner #line [317596.163,444645.063,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317596.163,444645.063,0.0]
        addKnot sh k #corner #line [317226.228,444224.358,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317226.228,444224.358,0.0]
        addKnot sh k #corner #line [317376.421,444092.290,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320395.906,447829.035,0.0]
        addKnot sh k #corner #line [318388.573,445546.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318388.573,445546.222,0.0]
        addKnot sh k #corner #line [318538.767,445414.153,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318538.767,445414.153,0.0]
        addKnot sh k #corner #line [320479.830,447621.603,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278910.730,511919.884,0.0]
        addKnot sh k #corner #line [280009.960,511961.044,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279118.073,511727.508,0.0]
        addKnot sh k #corner #line [280117.324,511764.924,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276515.485,508092.961,0.0]
        addKnot sh k #corner #line [279108.523,508283.126,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276330.649,507878.868,0.0]
        addKnot sh k #corner #line [279322.615,508098.289,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280209.820,511968.527,0.0]
        addKnot sh k #corner #line [281708.770,512024.654,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280117.324,511764.924,0.0]
        addKnot sh k #corner #line [281516.394,511817.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283068.605,510679.185,0.0]
        addKnot sh k #corner #line [283112.423,509880.106,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282968.847,510671.869,0.0]
        addKnot sh k #corner #line [283012.672,509872.934,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283197.544,508583.001,0.0]
        addKnot sh k #corner #line [284992.727,508714.654,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283212.121,508383.533,0.0]
        addKnot sh k #corner #line [285107.032,508522.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276379.799,510288.918,0.0]
        addKnot sh k #corner #line [278973.481,510479.130,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276384.963,510189.028,0.0]
        addKnot sh k #corner #line [278978.590,510379.236,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283068.605,510679.185,0.0]
        addKnot sh k #corner #line [283120.768,510683.010,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283120.768,510683.010,0.0]
        addKnot sh k #corner #line [283113.454,510782.742,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283113.454,510782.742,0.0]
        addKnot sh k #corner #line [283063.588,510779.085,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284859.277,510910.775,0.0]
        addKnot sh k #corner #line [284110.776,510855.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284110.776,510855.883,0.0]
        addKnot sh k #corner #line [284118.090,510756.150,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284118.090,510756.150,0.0]
        addKnot sh k #corner #line [284864.251,510810.871,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281771.762,510584.078,0.0]
        addKnot sh k #corner #line [281815.765,509785.157,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281568.004,510653.245,0.0]
        addKnot sh k #corner #line [281616.206,509771.798,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276384.963,510189.028,0.0]
        addKnot sh k #corner #line [276515.485,508092.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276180.174,510276.485,0.0]
        addKnot sh k #corner #line [276330.649,507878.868,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278978.590,510379.236,0.0]
        addKnot sh k #corner #line [279005.534,509881.170,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279005.534,509881.170,0.0]
        addKnot sh k #corner #line [279205.159,509893.443,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279173.111,510491.503,0.0]
        addKnot sh k #corner #line [279205.159,509893.443,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279266.525,508895.328,0.0]
        addKnot sh k #corner #line [279322.615,508098.289,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279266.525,508895.328,0.0]
        addKnot sh k #corner #line [279066.899,508883.054,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279066.899,508883.054,0.0]
        addKnot sh k #corner #line [279108.523,508283.126,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281766.715,510683.977,0.0]
        addKnot sh k #corner #line [283063.588,510779.085,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281771.762,510584.078,0.0]
        addKnot sh k #corner #line [282968.847,510671.869,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281901.025,508487.919,0.0]
        addKnot sh k #corner #line [283097.811,508575.687,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281716.188,508273.826,0.0]
        addKnot sh k #corner #line [283212.121,508383.533,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281815.765,509785.157,0.0]
        addKnot sh k #corner #line [283012.672,509872.934,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281821.719,509685.325,0.0]
        addKnot sh k #corner #line [283018.609,509773.101,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281821.719,509685.325,0.0]
        addKnot sh k #corner #line [281901.025,508487.919,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281616.206,509771.798,0.0]
        addKnot sh k #corner #line [281716.188,508273.826,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283112.423,509880.106,0.0]
        addKnot sh k #corner #line [283197.544,508583.001,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283018.609,509773.101,0.0]
        addKnot sh k #corner #line [283097.811,508575.687,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276045.551,514917.819,0.0]
        addKnot sh k #corner #line [280045.383,514948.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276247.097,514719.376,0.0]
        addKnot sh k #corner #line [279946.987,514748.072,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276247.097,514719.376,0.0]
        addKnot sh k #corner #line [276289.933,512503.443,0.0]
        addKnot sh k #corner #line [276379.799,510288.918,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276045.551,514917.819,0.0]
        addKnot sh k #corner #line [276087.105,512596.405,0.0]
        addKnot sh k #corner #line [276180.174,510276.485,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280146.981,514749.624,0.0]
        addKnot sh k #corner #line [280209.820,511968.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279946.987,514748.072,0.0]
        addKnot sh k #corner #line [280009.960,511961.044,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280045.383,514948.842,0.0]
        addKnot sh k #corner #line [284845.239,514986.069,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280146.981,514749.624,0.0]
        addKnot sh k #corner #line [284746.848,514785.300,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281516.394,511817.310,0.0]
        addKnot sh k #corner #line [281519.085,511747.947,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281519.085,511747.947,0.0]
        addKnot sh k #corner #line [281718.893,511756.779,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281708.770,512024.654,0.0]
        addKnot sh k #corner #line [281718.893,511756.779,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281763.053,510757.755,0.0]
        addKnot sh k #corner #line [281766.715,510683.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281763.053,510757.755,0.0]
        addKnot sh k #corner #line [281563.245,510748.923,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281563.245,510748.923,0.0]
        addKnot sh k #corner #line [281568.004,510653.245,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278910.730,511919.884,0.0]
        addKnot sh k #corner #line [278923.656,511580.854,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278923.656,511580.854,0.0]
        addKnot sh k #corner #line [279123.459,511589.789,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279118.073,511727.508,0.0]
        addKnot sh k #corner #line [279123.459,511589.789,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279168.133,510590.787,0.0]
        addKnot sh k #corner #line [279173.111,510491.503,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279168.133,510590.787,0.0]
        addKnot sh k #corner #line [278968.330,510581.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278968.330,510581.852,0.0]
        addKnot sh k #corner #line [278973.481,510479.130,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291514.847,466857.075,0.0]
        addKnot sh k #corner #line [292391.577,467337.954,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291435.672,466585.539,0.0]
        addKnot sh k #corner #line [292400.124,467114.533,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287146.988,468728.857,0.0]
        addKnot sh k #corner #line [289827.236,470076.552,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287415.517,468640.021,0.0]
        addKnot sh k #corner #line [289738.399,469808.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292391.577,467337.954,0.0]
        addKnot sh k #corner #line [293619.105,468011.242,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292575.479,467210.713,0.0]
        addKnot sh k #corner #line [293890.641,467932.068,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293994.255,470493.043,0.0]
        addKnot sh k #corner #line [294366.877,469784.805,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293904.970,470447.987,0.0]
        addKnot sh k #corner #line [294277.512,469739.871,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293311.512,471828.532,0.0]
        addKnot sh k #corner #line [295009.001,472682.072,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293401.404,471649.872,0.0]
        addKnot sh k #corner #line [295009.557,472458.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288379.572,466774.241,0.0]
        addKnot sh k #corner #line [290702.981,467942.508,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288426.421,466685.868,0.0]
        addKnot sh k #corner #line [290749.880,467854.160,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294413.858,469696.499,0.0]
        addKnot sh k #corner #line [294458.528,469718.960,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294458.528,469718.960,0.0]
        addKnot sh k #corner #line [294413.605,469808.302,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294413.605,469808.302,0.0]
        addKnot sh k #corner #line [294366.877,469784.805,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295975.444,470593.633,0.0]
        addKnot sh k #corner #line [295307.021,470257.533,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295307.021,470257.533,0.0]
        addKnot sh k #corner #line [295351.944,470168.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295351.944,470168.191,0.0]
        addKnot sh k #corner #line [296022.464,470505.345,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292832.763,469908.855,0.0]
        addKnot sh k #corner #line [293205.146,469200.658,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292654.650,469817.871,0.0]
        addKnot sh k #corner #line [293065.796,469036.699,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287415.517,468640.021,0.0]
        addKnot sh k #corner #line [288379.572,466774.241,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287146.988,468728.857,0.0]
        addKnot sh k #corner #line [288248.727,466594.055,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289738.399,469808.023,0.0]
        addKnot sh k #corner #line [290010.666,469271.816,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290010.666,469271.816,0.0]
        addKnot sh k #corner #line [290188.279,469363.766,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289827.236,470076.552,0.0]
        addKnot sh k #corner #line [290188.279,469363.766,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290648.022,468475.714,0.0]
        addKnot sh k #corner #line [290927.547,467946.027,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290648.022,468475.714,0.0]
        addKnot sh k #corner #line [290470.409,468383.764,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290470.409,468383.764,0.0]
        addKnot sh k #corner #line [290702.981,467942.508,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293205.146,469200.658,0.0]
        addKnot sh k #corner #line [294277.512,469739.871,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293252.100,469112.338,0.0]
        addKnot sh k #corner #line [294413.858,469696.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291971.434,471154.708,0.0]
        addKnot sh k #corner #line [293311.512,471828.532,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292239.963,471065.871,0.0]
        addKnot sh k #corner #line [293312.062,471604.949,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292786.622,469997.584,0.0]
        addKnot sh k #corner #line [293858.814,470536.709,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292832.763,469908.855,0.0]
        addKnot sh k #corner #line [293904.970,470447.987,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292239.963,471065.871,0.0]
        addKnot sh k #corner #line [292786.622,469997.584,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291971.434,471154.708,0.0]
        addKnot sh k #corner #line [292654.650,469817.871,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293401.404,471649.872,0.0]
        addKnot sh k #corner #line [293994.255,470493.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293312.062,471604.949,0.0]
        addKnot sh k #corner #line [293858.814,470536.709,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290587.017,462815.675,0.0]
        addKnot sh k #corner #line [293776.868,464690.472,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290515.933,462541.910,0.0]
        addKnot sh k #corner #line [293964.377,464568.692,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288426.421,466685.868,0.0]
        addKnot sh k #corner #line [289486.177,464739.304,0.0]
        addKnot sh k #corner #line [290587.017,462815.675,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288248.727,466594.055,0.0]
        addKnot sh k #corner #line [289359.842,464555.401,0.0]
        addKnot sh k #corner #line [290515.933,462541.910,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292575.479,467210.713,0.0]
        addKnot sh k #corner #line [293949.292,464791.812,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292400.124,467114.533,0.0]
        addKnot sh k #corner #line [293776.868,464690.472,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293949.292,464791.812,0.0]
        addKnot sh k #corner #line [297915.057,467122.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293964.377,464568.692,0.0]
        addKnot sh k #corner #line [298102.560,467000.860,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293065.796,469036.699,0.0]
        addKnot sh k #corner #line [293110.831,468952.148,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293110.831,468952.148,0.0]
        addKnot sh k #corner #line [293286.833,469047.144,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293252.100,469112.338,0.0]
        addKnot sh k #corner #line [293286.833,469047.144,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293761.808,468167.145,0.0]
        addKnot sh k #corner #line [293890.641,467932.068,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293761.808,468167.145,0.0]
        addKnot sh k #corner #line [293585.806,468072.149,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293585.806,468072.149,0.0]
        addKnot sh k #corner #line [293619.105,468011.242,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290749.880,467854.160,0.0]
        addKnot sh k #corner #line [290798.194,467763.363,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290798.194,467763.363,0.0]
        addKnot sh k #corner #line [290974.245,467858.269,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290927.547,467946.027,0.0]
        addKnot sh k #corner #line [290974.245,467858.269,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291448.767,466978.026,0.0]
        addKnot sh k #corner #line [291514.847,466857.075,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291448.767,466978.026,0.0]
        addKnot sh k #corner #line [291272.717,466883.120,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291272.717,466883.120,0.0]
        addKnot sh k #corner #line [291435.672,466585.539,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285058.917,510923.009,0.0]
        addKnot sh k #corner #line [285192.192,508729.283,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284864.251,510810.871,0.0]
        addKnot sh k #corner #line [284992.727,508714.654,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296200.069,470597.337,0.0]
        addKnot sh k #corner #line [296250.761,470502.408,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296022.464,470505.345,0.0]
        addKnot sh k #corner #line [296121.691,470319.755,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291961.578,536910.207,0.0]
        addKnot sh k #corner #line [291625.360,535456.867,0.0]
        addKnot sh k #corner #line [291312.958,533998.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291767.150,536957.090,0.0]
        addKnot sh k #corner #line [291430.144,535500.350,0.0]
        addKnot sh k #corner #line [291117.013,534038.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294391.921,536324.169,0.0]
        addKnot sh k #corner #line [294186.372,535447.937,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294197.493,536371.052,0.0]
        addKnot sh k #corner #line [293969.364,535396.125,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287586.961,537965.076,0.0]
        addKnot sh k #corner #line [287292.126,536698.910,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287415.924,538109.185,0.0]
        addKnot sh k #corner #line [287075.403,536646.881,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288235.687,534423.359,0.0]
        addKnot sh k #corner #line [288947.948,534277.707,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288947.948,534277.707,0.0]
        addKnot sh k #corner #line [288988.017,534473.652,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288988.017,534473.652,0.0]
        addKnot sh k #corner #line [288373.780,534599.258,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291117.013,534038.291,0.0]
        addKnot sh k #corner #line [290555.578,534153.100,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290555.578,534153.100,0.0]
        addKnot sh k #corner #line [290515.509,533957.155,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290515.509,533957.155,0.0]
        addKnot sh k #corner #line [291174.863,533822.323,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296067.940,536022.890,0.0]
        addKnot sh k #corner #line [295817.142,534953.218,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295850.127,535972.546,0.0]
        addKnot sh k #corner #line [295644.672,535096.292,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288994.784,537831.334,0.0]
        addKnot sh k #corner #line [291911.194,537128.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289045.166,537613.453,0.0]
        addKnot sh k #corner #line [291767.150,536957.090,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287292.126,536698.910,0.0]
        addKnot sh k #corner #line [288556.040,536394.137,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287248.291,536503.748,0.0]
        addKnot sh k #corner #line [288512.247,536198.965,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294186.372,535447.937,0.0]
        addKnot sh k #corner #line [295644.672,535096.292,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294141.900,535252.929,0.0]
        addKnot sh k #corner #line [295600.241,534901.273,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287248.291,536503.748,0.0]
        addKnot sh k #corner #line [286904.192,534899.776,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287075.403,536646.881,0.0]
        addKnot sh k #corner #line [286707.764,534937.498,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288728.934,536251.412,0.0]
        addKnot sh k #corner #line [288373.780,534599.258,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288512.247,536198.965,0.0]
        addKnot sh k #corner #line [288177.835,534639.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291911.194,537128.089,0.0]
        addKnot sh k #corner #line [294341.535,536542.051,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291961.578,536910.207,0.0]
        addKnot sh k #corner #line [294197.493,536371.052,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291174.863,533822.323,0.0]
        addKnot sh k #corner #line [291886.230,533676.854,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291886.230,533676.854,0.0]
        addKnot sh k #corner #line [291926.299,533872.799,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291926.299,533872.799,0.0]
        addKnot sh k #corner #line [291312.958,533998.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293566.328,533537.428,0.0]
        addKnot sh k #corner #line [293003.997,533652.419,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293003.997,533652.419,0.0]
        addKnot sh k #corner #line [292963.928,533456.474,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292963.928,533456.474,0.0]
        addKnot sh k #corner #line [293624.176,533321.459,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294341.535,536542.051,0.0]
        addKnot sh k #corner #line [295897.010,536166.973,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294391.921,536324.169,0.0]
        addKnot sh k #corner #line [295850.127,535972.546,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293762.273,533497.359,0.0]
        addKnot sh k #corner #line [295231.862,533196.840,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293624.176,533321.459,0.0]
        addKnot sh k #corner #line [295387.738,532960.826,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295600.241,534901.273,0.0]
        addKnot sh k #corner #line [295568.373,534760.105,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295568.373,534760.105,0.0]
        addKnot sh k #corner #line [295763.802,534717.568,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295817.142,534953.218,0.0]
        addKnot sh k #corner #line [295763.802,534717.568,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295508.589,533545.022,0.0]
        addKnot sh k #corner #line [295387.738,532960.826,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295508.589,533545.022,0.0]
        addKnot sh k #corner #line [295313.160,533587.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295313.160,533587.558,0.0]
        addKnot sh k #corner #line [295231.862,533196.840,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294141.900,535252.929,0.0]
        addKnot sh k #corner #line [293762.273,533497.359,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293969.364,535396.125,0.0]
        addKnot sh k #corner #line [293566.328,533537.428,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296714.192,539285.846,0.0]
        addKnot sh k #corner #line [296619.533,538947.408,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296619.533,538947.408,0.0]
        addKnot sh k #corner #line [296812.802,538895.914,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296961.109,539423.803,0.0]
        addKnot sh k #corner #line [296812.802,538895.914,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296349.381,537156.592,0.0]
        addKnot sh k #corner #line [296067.940,536022.890,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296349.381,537156.592,0.0]
        addKnot sh k #corner #line [296156.112,537208.086,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296156.112,537208.086,0.0]
        addKnot sh k #corner #line [295897.010,536166.973,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290193.408,539552.293,0.0]
        addKnot sh k #corner #line [294293.658,538391.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290166.168,539456.075,0.0]
        addKnot sh k #corner #line [294362.635,538268.034,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290193.408,539552.293,0.0]
        addKnot sh k #corner #line [290166.168,539456.075,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288535.623,541601.250,0.0]
        addKnot sh k #corner #line [287816.321,538899.890,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288343.222,541655.857,0.0]
        addKnot sh k #corner #line [287646.691,539045.510,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288493.835,541820.942,0.0]
        addKnot sh k #corner #line [296961.109,539423.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288535.623,541601.250,0.0]
        addKnot sh k #corner #line [296714.192,539285.846,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287586.961,537965.076,0.0]
        addKnot sh k #corner #line [287878.551,537894.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287878.551,537894.763,0.0]
        addKnot sh k #corner #line [287925.434,538089.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287925.434,538089.191,0.0]
        addKnot sh k #corner #line [287633.844,538159.503,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288994.784,537831.334,0.0]
        addKnot sh k #corner #line [288605.929,537925.100,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288605.929,537925.100,0.0]
        addKnot sh k #corner #line [288559.046,537730.673,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288559.046,537730.673,0.0]
        addKnot sh k #corner #line [288850.739,537660.336,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289045.166,537613.453,0.0]
        addKnot sh k #corner #line [288728.934,536251.412,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288850.739,537660.336,0.0]
        addKnot sh k #corner #line [288556.040,536394.137,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286904.192,534899.776,0.0]
        addKnot sh k #corner #line [288177.835,534639.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286766.099,534723.876,0.0]
        addKnot sh k #corner #line [288235.687,534423.359,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294362.635,538268.034,0.0]
        addKnot sh k #corner #line [294464.497,538627.807,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294464.497,538627.807,0.0]
        addKnot sh k #corner #line [294368.279,538655.049,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294368.279,538655.049,0.0]
        addKnot sh k #corner #line [294293.658,538391.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294707.704,539853.896,0.0]
        addKnot sh k #corner #line [294640.697,539617.228,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294640.697,539617.228,0.0]
        addKnot sh k #corner #line [294736.915,539589.986,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294736.915,539589.986,0.0]
        addKnot sh k #corner #line [294803.922,539826.654,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294803.922,539826.654,0.0]
        addKnot sh k #corner #line [294707.704,539853.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309253.747,459682.270,0.0]
        addKnot sh k #corner #line [310886.880,457658.785,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308972.999,459716.631,0.0]
        addKnot sh k #corner #line [310795.211,457456.254,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308972.999,459716.631,0.0]
        addKnot sh k #corner #line [309997.048,460517.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309253.747,459682.270,0.0]
        addKnot sh k #corner #line [310041.508,460298.224,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313780.155,454344.235,0.0]
        addKnot sh k #corner #line [314004.504,454549.404,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314004.504,454549.404,0.0]
        addKnot sh k #corner #line [313869.533,454696.994,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313869.533,454696.994,0.0]
        addKnot sh k #corner #line [313645.180,454491.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314530.677,455301.616,0.0]
        addKnot sh k #corner #line [314312.301,455101.909,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314312.301,455101.909,0.0]
        addKnot sh k #corner #line [314447.273,454954.319,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314447.273,454954.319,0.0]
        addKnot sh k #corner #line [314591.897,455086.579,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312045.283,462118.867,0.0]
        addKnot sh k #corner #line [313197.134,460674.111,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312010.920,461838.118,0.0]
        addKnot sh k #corner #line [312977.907,460626.641,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310199.063,460421.417,0.0]
        addKnot sh k #corner #line [311165.746,459209.702,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310041.508,460298.224,0.0]
        addKnot sh k #corner #line [311072.486,459007.364,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310986.837,461037.382,0.0]
        addKnot sh k #corner #line [311953.655,459825.772,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310908.060,460975.785,0.0]
        addKnot sh k #corner #line [311874.864,459764.165,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310199.063,460421.417,0.0]
        addKnot sh k #corner #line [310282.054,460486.308,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310282.054,460486.308,0.0]
        addKnot sh k #corner #line [310158.861,460643.863,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310158.861,460643.863,0.0]
        addKnot sh k #corner #line [309997.048,460517.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310863.599,461194.901,0.0]
        addKnot sh k #corner #line [310631.525,461013.442,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310631.525,461013.442,0.0]
        addKnot sh k #corner #line [310754.718,460855.887,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310754.718,460855.887,0.0]
        addKnot sh k #corner #line [310908.060,460975.785,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310863.599,461194.901,0.0]
        addKnot sh k #corner #line [312045.283,462118.867,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310986.837,461037.382,0.0]
        addKnot sh k #corner #line [312010.920,461838.118,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311165.746,459209.702,0.0]
        addKnot sh k #corner #line [311874.864,459764.165,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311292.019,459054.556,0.0]
        addKnot sh k #corner #line [312078.411,459669.440,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313197.134,460674.111,0.0]
        addKnot sh k #corner #line [313864.953,459864.495,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313104.261,460471.557,0.0]
        addKnot sh k #corner #line [313645.296,459815.606,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311953.655,459825.772,0.0]
        addKnot sh k #corner #line [312977.907,460626.641,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312078.411,459669.440,0.0]
        addKnot sh k #corner #line [313104.261,460471.557,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311292.019,459054.556,0.0]
        addKnot sh k #corner #line [311832.606,458398.254,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311072.486,459007.364,0.0]
        addKnot sh k #corner #line [311674.980,458275.005,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310886.880,457658.785,0.0]
        addKnot sh k #corner #line [311674.980,458275.005,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311014.939,457505.035,0.0]
        addKnot sh k #corner #line [311879.403,458180.965,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310795.211,457456.254,0.0]
        addKnot sh k #corner #line [311443.781,456686.229,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311443.781,456686.229,0.0]
        addKnot sh k #corner #line [311595.179,456816.922,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311014.939,457505.035,0.0]
        addKnot sh k #corner #line [311595.179,456816.922,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312379.315,455908.555,0.0]
        addKnot sh k #corner #line [313645.180,454491.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312379.315,455908.555,0.0]
        addKnot sh k #corner #line [312227.917,455777.863,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312227.917,455777.863,0.0]
        addKnot sh k #corner #line [313497.581,454356.861,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313864.953,459864.495,0.0]
        addKnot sh k #corner #line [315104.405,458412.850,0.0]
        addKnot sh k #corner #line [316375.395,456988.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313773.548,459662.007,0.0]
        addKnot sh k #corner #line [314985.663,458244.772,0.0]
        addKnot sh k #corner #line [316227.798,456853.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311832.606,458398.254,0.0]
        addKnot sh k #corner #line [313645.296,459815.606,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311879.403,458180.965,0.0]
        addKnot sh k #corner #line [313773.548,459662.007,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311807.234,449145.180,0.0]
        addKnot sh k #corner #line [313054.994,447877.081,0.0]
        addKnot sh k #corner #line [314326.112,446632.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311593.797,449078.353,0.0]
        addKnot sh k #corner #line [312949.151,447700.185,0.0]
        addKnot sh k #corner #line [314332.007,446349.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317927.354,455043.842,0.0]
        addKnot sh k #corner #line [318278.137,454682.815,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318278.137,454682.815,0.0]
        addKnot sh k #corner #line [318419.973,454823.830,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318001.920,455254.595,0.0]
        addKnot sh k #corner #line [318419.973,454823.830,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319477.549,453760.095,0.0]
        addKnot sh k #corner #line [320492.715,452772.680,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319477.549,453760.095,0.0]
        addKnot sh k #corner #line [319335.713,453619.080,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319335.713,453619.080,0.0]
        addKnot sh k #corner #line [320209.933,452766.785,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310090.476,450969.876,0.0]
        addKnot sh k #corner #line [311668.442,449289.183,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309807.914,450982.487,0.0]
        addKnot sh k #corner #line [311593.797,449078.353,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311668.442,449289.183,0.0]
        addKnot sh k #corner #line [313324.474,450885.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311807.234,449145.180,0.0]
        addKnot sh k #corner #line [313535.229,450810.647,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315335.263,452545.547,0.0]
        addKnot sh k #corner #line [315551.267,452753.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315551.267,452753.735,0.0]
        addKnot sh k #corner #line [315412.475,452897.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315412.475,452897.737,0.0]
        addKnot sh k #corner #line [315268.512,452758.984,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316060.528,453522.340,0.0]
        addKnot sh k #corner #line [315916.485,453383.509,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315916.485,453383.509,0.0]
        addKnot sh k #corner #line [316055.277,453239.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316055.277,453239.507,0.0]
        addKnot sh k #corner #line [316271.281,453447.695,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314326.112,446632.395,0.0]
        addKnot sh k #corner #line [320209.933,452766.785,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314332.007,446349.614,0.0]
        addKnot sh k #corner #line [320492.715,452772.680,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310090.476,450969.876,0.0]
        addKnot sh k #corner #line [310617.828,451452.164,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310617.828,451452.164,0.0]
        addKnot sh k #corner #line [310482.853,451599.751,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310482.853,451599.751,0.0]
        addKnot sh k #corner #line [309807.914,450982.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311726.501,452737.125,0.0]
        addKnot sh k #corner #line [311294.579,452342.112,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311294.579,452342.112,0.0]
        addKnot sh k #corner #line [311429.554,452194.526,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311429.554,452194.526,0.0]
        addKnot sh k #corner #line [311787.722,452522.087,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314739.455,455221.586,0.0]
        addKnot sh k #corner #line [315196.958,454726.221,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314591.897,455086.579,0.0]
        addKnot sh k #corner #line [315050.384,454590.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314243.338,453842.695,0.0]
        addKnot sh k #corner #line [315050.384,454590.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314311.501,453769.524,0.0]
        addKnot sh k #corner #line [315118.549,454516.978,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314530.646,455301.647,0.0]
        addKnot sh k #corner #line [316227.798,456853.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314739.455,455221.586,0.0]
        addKnot sh k #corner #line [316362.908,456706.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316204.531,453661.132,0.0]
        addKnot sh k #corner #line [317788.562,455187.845,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316271.281,453447.695,0.0]
        addKnot sh k #corner #line [317927.354,455043.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316362.908,456706.310,0.0]
        addKnot sh k #corner #line [316582.512,456467.632,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316582.512,456467.632,0.0]
        addKnot sh k #corner #line [316728.506,456604.335,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316510.505,456841.274,0.0]
        addKnot sh k #corner #line [316728.506,456604.335,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317548.701,455728.389,0.0]
        addKnot sh k #corner #line [318001.920,455254.595,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317548.701,455728.389,0.0]
        addKnot sh k #corner #line [317402.707,455591.687,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317402.707,455591.687,0.0]
        addKnot sh k #corner #line [317788.562,455187.845,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311935.309,452657.062,0.0]
        addKnot sh k #corner #line [313468.477,451024.083,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311787.722,452522.087,0.0]
        addKnot sh k #corner #line [313324.474,450885.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311935.309,452657.062,0.0]
        addKnot sh k #corner #line [312388.596,453071.615,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312388.596,453071.615,0.0]
        addKnot sh k #corner #line [312253.622,453219.202,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312253.622,453219.202,0.0]
        addKnot sh k #corner #line [311726.501,452737.125,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313497.581,454356.861,0.0]
        addKnot sh k #corner #line [313065.348,453961.563,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313065.348,453961.563,0.0]
        addKnot sh k #corner #line [313200.322,453813.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313200.322,453813.977,0.0]
        addKnot sh k #corner #line [313632.555,454209.274,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313468.477,451024.083,0.0]
        addKnot sh k #corner #line [315124.510,452620.192,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313535.229,450810.647,0.0]
        addKnot sh k #corner #line [315335.263,452545.547,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315196.958,454726.221,0.0]
        addKnot sh k #corner #line [316204.531,453661.132,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315118.549,454516.978,0.0]
        addKnot sh k #corner #line [316060.528,453522.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313780.155,454344.235,0.0]
        addKnot sh k #corner #line [314243.338,453842.695,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313632.555,454209.274,0.0]
        addKnot sh k #corner #line [314096.762,453706.623,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314311.501,453769.524,0.0]
        addKnot sh k #corner #line [315268.512,452758.984,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314096.762,453706.623,0.0]
        addKnot sh k #corner #line [315124.510,452620.192,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319610.540,445722.982,0.0]
        addKnot sh k #corner #line [320930.565,447225.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319760.791,445590.980,0.0]
        addKnot sh k #corner #line [321081.380,447094.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319610.540,445722.982,0.0]
        addKnot sh k #corner #line [319760.791,445590.980,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320611.899,447771.797,0.0]
        addKnot sh k #corner #line [321137.617,447310.315,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320479.830,447621.603,0.0]
        addKnot sh k #corner #line [320930.565,447225.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321081.380,447094.143,0.0]
        addKnot sh k #corner #line [322041.493,446271.400,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322041.493,446271.400,0.0]
        addKnot sh k #corner #line [322169.562,446425.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321137.617,447310.315,0.0]
        addKnot sh k #corner #line [322169.562,446425.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323091.281,445656.626,0.0]
        addKnot sh k #corner #line [323168.168,445593.458,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323091.281,445656.626,0.0]
        addKnot sh k #corner #line [322963.212,445503.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322963.212,445503.003,0.0]
        addKnot sh k #corner #line [323041.292,445438.854,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323041.292,445438.854,0.0]
        addKnot sh k #corner #line [323168.168,445593.458,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320611.899,447771.797,0.0]
        addKnot sh k #corner #line [321470.709,448748.468,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321470.709,448748.468,0.0]
        addKnot sh k #corner #line [321320.516,448880.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321320.516,448880.537,0.0]
        addKnot sh k #corner #line [320395.906,447829.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322508.964,450232.085,0.0]
        addKnot sh k #corner #line [322112.926,449781.695,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322112.926,449781.695,0.0]
        addKnot sh k #corner #line [322263.119,449649.627,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322263.119,449649.627,0.0]
        addKnot sh k #corner #line [322659.158,450100.016,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322659.158,450100.016,0.0]
        addKnot sh k #corner #line [322508.964,450232.085,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287816.321,538899.890,0.0]
        addKnot sh k #corner #line [287633.844,538159.503,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287598.058,538851.513,0.0]
        addKnot sh k #corner #line [287415.924,538109.185,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327896.199,442520.234,0.0]
        addKnot sh k #corner #line [329611.605,444920.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327726.231,442641.722,0.0]
        addKnot sh k #corner #line [329441.637,445041.635,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329672.995,444631.408,0.0]
        addKnot sh k #corner #line [331585.784,443296.006,0.0]
        addKnot sh k #corner #line [333533.612,442012.250,0.0]
        addKnot sh k #corner #line [335515.083,440781.058,0.0]
        addKnot sh k #corner #line [337528.779,439603.311,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315480.864,425150.553,0.0]
        addKnot sh k #corner #line [324785.110,438167.514,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315172.873,425063.401,0.0]
        addKnot sh k #corner #line [324622.407,438283.810,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328058.958,442403.899,0.0]
        addKnot sh k #corner #line [329774.333,444803.834,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327896.586,442520.775,0.0]
        addKnot sh k #corner #line [328058.958,442403.899,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327133.613,442828.985,0.0]
        addKnot sh k #corner #line [327942.659,442241.189,0.0]
        updateShape sh
        addModifier sh (Extrude amount:wallHeight capStart:false capEnd:false)
        sh.isHidden = true
        append made sh
      )
      -- MASONRY_EDGES: source edges for REVIEW ONLY (hidden to avoid misleading walls)
      if makeReviewWalls do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REVIEW_MASONRY_EDGES_")
        sh.wirecolor = (color 245 156 70)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290847.916,461982.227,0.0]
        addKnot sh k #corner #line [291029.124,461680.073,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291029.124,461680.073,0.0]
        addKnot sh k #corner #line [291199.731,461784.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291019.608,462084.802,0.0]
        addKnot sh k #corner #line [291199.731,461784.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291019.608,462084.802,0.0]
        addKnot sh k #corner #line [290847.916,461982.227,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291982.570,460504.937,0.0]
        addKnot sh k #corner #line [292145.049,460244.464,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291982.570,460504.937,0.0]
        addKnot sh k #corner #line [291811.963,460400.556,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291811.963,460400.556,0.0]
        addKnot sh k #corner #line [291975.614,460138.200,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310517.501,463968.428,0.0]
        addKnot sh k #corner #line [317998.776,469493.049,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310716.799,463866.980,0.0]
        addKnot sh k #corner #line [318117.584,469332.162,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317998.776,469493.049,0.0]
        addKnot sh k #corner #line [318117.584,469332.162,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296910.771,462997.265,0.0]
        addKnot sh k #corner #line [298423.984,460663.374,0.0]
        addKnot sh k #corner #line [300002.232,458372.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300002.232,458372.961,0.0]
        addKnot sh k #corner #line [300164.429,458489.983,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296973.943,463272.964,0.0]
        addKnot sh k #corner #line [298534.352,460858.237,0.0]
        addKnot sh k #corner #line [300164.429,458489.983,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301042.071,457273.536,0.0]
        addKnot sh k #corner #line [301245.467,456997.099,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301042.071,457273.536,0.0]
        addKnot sh k #corner #line [300879.874,457156.513,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300879.874,457156.513,0.0]
        addKnot sh k #corner #line [301025.216,456958.764,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301144.025,456797.877,0.0]
        addKnot sh k #corner #line [301299.926,456587.786,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301299.926,456587.786,0.0]
        addKnot sh k #corner #line [301459.473,456708.399,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301245.467,456997.099,0.0]
        addKnot sh k #corner #line [301459.473,456708.399,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307577.879,449272.697,0.0]
        addKnot sh k #corner #line [307809.122,449018.963,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307577.879,449272.697,0.0]
        addKnot sh k #corner #line [307428.802,449139.362,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307428.802,449139.362,0.0]
        addKnot sh k #corner #line [307594.085,448957.815,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302204.494,455391.226,0.0]
        addKnot sh k #corner #line [303574.127,453648.535,0.0]
        addKnot sh k #corner #line [304982.470,451936.975,0.0]
        addKnot sh k #corner #line [306428.815,450257.407,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306428.815,450257.407,0.0]
        addKnot sh k #corner #line [306577.892,450390.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302364.040,455511.838,0.0]
        addKnot sh k #corner #line [303730.296,453773.480,0.0]
        addKnot sh k #corner #line [305135.148,452066.163,0.0]
        addKnot sh k #corner #line [306577.892,450390.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302364.040,455511.838,0.0]
        addKnot sh k #corner #line [302204.494,455391.226,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307729.060,448810.229,0.0]
        addKnot sh k #corner #line [307906.081,448617.571,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307906.081,448617.571,0.0]
        addKnot sh k #corner #line [308052.146,448754.200,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307809.122,449018.963,0.0]
        addKnot sh k #corner #line [308052.146,448754.200,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314914.268,441998.800,0.0]
        addKnot sh k #corner #line [315170.765,441770.628,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314914.268,441998.800,0.0]
        addKnot sh k #corner #line [314779.945,441850.612,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314779.945,441850.612,0.0]
        addKnot sh k #corner #line [314963.298,441687.338,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308930.769,447522.119,0.0]
        addKnot sh k #corner #line [310475.056,445932.147,0.0]
        addKnot sh k #corner #line [312054.587,444377.182,0.0]
        addKnot sh k #corner #line [313668.567,442858.004,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313668.567,442858.004,0.0]
        addKnot sh k #corner #line [313802.890,443006.192,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309076.834,447658.748,0.0]
        addKnot sh k #corner #line [310617.309,446072.732,0.0]
        addKnot sh k #corner #line [312192.925,444521.621,0.0]
        addKnot sh k #corner #line [313802.890,443006.192,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309076.834,447658.748,0.0]
        addKnot sh k #corner #line [308930.769,447522.119,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315112.960,441554.669,0.0]
        addKnot sh k #corner #line [315309.174,441381.549,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315309.174,441381.549,0.0]
        addKnot sh k #corner #line [315440.157,441532.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315170.765,441770.628,0.0]
        addKnot sh k #corner #line [315440.157,441532.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316442.755,440399.209,0.0]
        addKnot sh k #corner #line [318849.893,438409.967,0.0]
        addKnot sh k #corner #line [321316.114,436494.464,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321316.645,436495.190,0.0]
        addKnot sh k #corner #line [321434.748,436656.602,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316573.738,440550.357,0.0]
        addKnot sh k #corner #line [318974.509,438566.360,0.0]
        addKnot sh k #corner #line [321434.748,436656.602,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316573.738,440550.357,0.0]
        addKnot sh k #corner #line [316442.755,440399.209,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292145.049,460244.464,0.0]
        addKnot sh k #corner #line [296973.943,463272.964,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292166.554,460021.872,0.0]
        addKnot sh k #corner #line [296910.771,462997.265,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310555.912,463748.171,0.0]
        addKnot sh k #corner #line [310778.292,463449.090,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310778.292,463449.090,0.0]
        addKnot sh k #corner #line [310937.504,463570.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310716.799,463866.980,0.0]
        addKnot sh k #corner #line [310937.504,463570.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311845.396,462376.107,0.0]
        addKnot sh k #corner #line [312045.354,462118.777,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311845.396,462376.107,0.0]
        addKnot sh k #corner #line [311686.185,462255.050,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311686.185,462255.050,0.0]
        addKnot sh k #corner #line [311887.658,461995.765,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311887.658,461995.765,0.0]
        addKnot sh k #corner #line [312045.354,462118.777,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316436.628,456773.716,0.0]
        addKnot sh k #corner #line [316779.212,457087.025,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316779.212,457087.025,0.0]
        addKnot sh k #corner #line [316644.238,457234.612,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316644.238,457234.612,0.0]
        addKnot sh k #corner #line [316301.653,456921.302,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316301.653,456921.302,0.0]
        addKnot sh k #corner #line [316436.628,456773.716,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323090.675,463130.181,0.0]
        addKnot sh k #corner #line [317751.137,458246.923,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317751.137,458246.923,0.0]
        addKnot sh k #corner #line [317886.112,458099.336,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317886.112,458099.336,0.0]
        addKnot sh k #corner #line [323225.649,462982.594,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323225.649,462982.594,0.0]
        addKnot sh k #corner #line [323090.675,463130.181,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306207.089,431809.584,0.0]
        addKnot sh k #corner #line [314963.298,441687.338,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306356.752,431676.914,0.0]
        addKnot sh k #corner #line [315112.960,441554.669,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298296.095,440454.375,0.0]
        addKnot sh k #corner #line [307594.085,448957.815,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298431.070,440306.788,0.0]
        addKnot sh k #corner #line [307729.060,448810.229,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298296.095,440454.375,0.0]
        addKnot sh k #corner #line [298431.070,440306.788,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291008.277,449561.650,0.0]
        addKnot sh k #corner #line [301025.216,456958.764,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291127.086,449400.763,0.0]
        addKnot sh k #corner #line [301144.025,456797.877,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291008.277,449561.650,0.0]
        addKnot sh k #corner #line [291127.086,449400.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307621.582,461829.908,0.0]
        addKnot sh k #corner #line [310517.501,463968.428,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307579.503,461550.212,0.0]
        addKnot sh k #corner #line [310555.912,463748.171,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279096.495,469579.764,0.0]
        addKnot sh k #corner #line [285560.094,472517.870,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279179.258,469397.691,0.0]
        addKnot sh k #corner #line [285460.784,472253.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279096.495,469579.764,0.0]
        addKnot sh k #corner #line [279179.258,469397.691,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304748.591,485925.924,0.0]
        addKnot sh k #corner #line [306610.129,486657.126,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304821.712,485739.770,0.0]
        addKnot sh k #corner #line [306683.249,486470.972,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304748.591,485925.924,0.0]
        addKnot sh k #corner #line [304821.712,485739.770,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306610.129,486657.126,0.0]
        addKnot sh k #corner #line [306683.249,486470.972,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302993.765,482553.758,0.0]
        addKnot sh k #corner #line [304056.701,480161.934,0.0]
        addKnot sh k #corner #line [305193.327,477804.237,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302809.762,482475.382,0.0]
        addKnot sh k #corner #line [303875.218,480077.887,0.0]
        addKnot sh k #corner #line [305014.538,477714.600,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302993.765,482553.758,0.0]
        addKnot sh k #corner #line [302809.762,482475.382,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305193.327,477804.237,0.0]
        addKnot sh k #corner #line [305014.538,477714.600,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285621.773,456153.311,0.0]
        addKnot sh k #corner #line [291975.614,460138.200,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285728.036,455983.876,0.0]
        addKnot sh k #corner #line [292166.554,460021.872,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285621.773,456153.311,0.0]
        addKnot sh k #corner #line [285728.036,455983.876,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285460.784,472253.035,0.0]
        addKnot sh k #corner #line [285987.420,471115.516,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285987.420,471115.516,0.0]
        addKnot sh k #corner #line [286167.796,471201.925,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285560.094,472517.870,0.0]
        addKnot sh k #corner #line [286167.796,471201.925,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286815.849,469849.140,0.0]
        addKnot sh k #corner #line [287370.551,468729.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286815.849,469849.140,0.0]
        addKnot sh k #corner #line [286635.473,469762.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286635.473,469762.731,0.0]
        addKnot sh k #corner #line [287191.867,468639.468,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287191.867,468639.468,0.0]
        addKnot sh k #corner #line [287370.551,468729.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307930.959,472777.024,0.0]
        addKnot sh k #corner #line [309246.310,470615.641,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307758.236,472676.194,0.0]
        addKnot sh k #corner #line [308970.036,470678.452,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307930.959,472777.024,0.0]
        addKnot sh k #corner #line [307758.236,472676.194,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303635.956,467333.118,0.0]
        addKnot sh k #corner #line [308970.036,470678.452,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303911.784,467270.028,0.0]
        addKnot sh k #corner #line [309246.310,470615.641,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303635.956,467333.118,0.0]
        addKnot sh k #corner #line [303838.135,467012.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303838.135,467012.003,0.0]
        addKnot sh k #corner #line [304006.272,467120.320,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303911.784,467270.028,0.0]
        addKnot sh k #corner #line [304006.272,467120.320,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304818.617,465859.330,0.0]
        addKnot sh k #corner #line [306192.716,463825.570,0.0]
        addKnot sh k #corner #line [307621.582,461829.908,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304818.617,465859.330,0.0]
        addKnot sh k #corner #line [304650.479,465751.013,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304650.479,465751.013,0.0]
        addKnot sh k #corner #line [306085.271,463629.890,0.0]
        addKnot sh k #corner #line [307579.503,461550.212,0.0]
        updateShape sh
        addModifier sh (Extrude amount:wallHeight capStart:false capEnd:false)
        sh.isHidden = true
        append made sh
      )
      -- PREFAB_EDGES: source edges for REVIEW ONLY (hidden to avoid misleading walls)
      if makeReviewWalls do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REVIEW_PREFAB_EDGES_")
        sh.wirecolor = (color 245 156 70)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322361.733,454721.278,0.0]
        addKnot sh k #corner #line [322405.156,454766.550,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322405.156,454766.550,0.0]
        addKnot sh k #corner #line [322332.986,454835.771,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322332.986,454835.771,0.0]
        addKnot sh k #corner #line [322289.564,454790.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322289.564,454790.499,0.0]
        addKnot sh k #corner #line [322361.733,454721.278,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324296.902,456883.348,0.0]
        addKnot sh k #corner #line [323025.195,455557.468,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323025.195,455557.468,0.0]
        addKnot sh k #corner #line [323097.365,455488.247,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323097.365,455488.247,0.0]
        addKnot sh k #corner #line [324369.071,456814.127,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332175.681,447819.587,0.0]
        addKnot sh k #corner #line [330053.348,444851.736,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332094.360,447877.785,0.0]
        addKnot sh k #corner #line [329972.006,444909.904,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330053.348,444851.736,0.0]
        addKnot sh k #corner #line [329972.006,444909.904,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328798.724,452939.539,0.0]
        addKnot sh k #corner #line [331123.130,455753.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328875.825,452875.856,0.0]
        addKnot sh k #corner #line [331200.230,455690.015,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331123.130,455753.698,0.0]
        addKnot sh k #corner #line [331200.230,455690.015,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331018.141,451168.383,0.0]
        addKnot sh k #corner #line [333242.918,454061.948,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331097.417,451107.430,0.0]
        addKnot sh k #corner #line [333322.194,454000.995,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333242.918,454061.948,0.0]
        addKnot sh k #corner #line [333322.194,454000.995,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325200.601,448583.290,0.0]
        addKnot sh k #corner #line [327525.070,451397.525,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325277.702,448519.608,0.0]
        addKnot sh k #corner #line [327602.170,451333.843,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325200.601,448583.290,0.0]
        addKnot sh k #corner #line [325277.702,448519.608,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327574.241,446689.215,0.0]
        addKnot sh k #corner #line [329799.078,449582.859,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327653.517,446628.262,0.0]
        addKnot sh k #corner #line [329878.354,449521.905,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327574.241,446689.215,0.0]
        addKnot sh k #corner #line [327653.517,446628.262,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332512.512,443155.256,0.0]
        addKnot sh k #corner #line [334530.078,446197.045,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332595.847,443099.981,0.0]
        addKnot sh k #corner #line [334613.413,446141.771,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332512.512,443155.256,0.0]
        addKnot sh k #corner #line [332595.847,443099.981,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335071.135,441519.671,0.0]
        addKnot sh k #corner #line [336981.314,444630.018,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335156.348,441467.339,0.0]
        addKnot sh k #corner #line [337066.527,444577.685,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335071.135,441519.671,0.0]
        addKnot sh k #corner #line [335156.348,441467.339,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338027.966,446334.283,0.0]
        addKnot sh k #corner #line [339938.096,449444.550,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338113.179,446281.951,0.0]
        addKnot sh k #corner #line [340023.309,449392.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339938.096,449444.550,0.0]
        addKnot sh k #corner #line [340023.309,449392.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335635.571,447863.745,0.0]
        addKnot sh k #corner #line [337653.084,450905.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335718.906,447808.470,0.0]
        addKnot sh k #corner #line [337736.419,450850.180,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337653.084,450905.454,0.0]
        addKnot sh k #corner #line [337736.419,450850.180,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324296.902,456883.348,0.0]
        addKnot sh k #corner #line [326858.073,459553.624,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324369.071,456814.127,0.0]
        addKnot sh k #corner #line [326930.243,459484.404,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326858.073,459553.624,0.0]
        addKnot sh k #corner #line [326930.243,459484.404,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329142.287,457448.539,0.0]
        addKnot sh k #corner #line [326714.306,454723.391,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329067.623,457515.061,0.0]
        addKnot sh k #corner #line [326639.478,454789.730,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329142.287,457448.539,0.0]
        addKnot sh k #corner #line [329067.623,457515.061,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335462.175,452415.390,0.0]
        addKnot sh k #corner #line [333339.042,449446.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335380.833,452473.558,0.0]
        addKnot sh k #corner #line [333257.723,449504.620,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335462.175,452415.390,0.0]
        addKnot sh k #corner #line [335380.833,452473.558,0.0]
        updateShape sh
        addModifier sh (Extrude amount:wallHeight capStart:false capEnd:false)
        sh.isHidden = true
        append made sh
      )
      -- GLASS_EDGES: source edges for REVIEW ONLY (hidden to avoid misleading walls)
      if makeReviewWalls do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REVIEW_GLASS_EDGES_")
        sh.wirecolor = (color 38 181 191)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269346.305,514827.085,0.0]
        addKnot sh k #corner #line [271196.482,514843.149,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.369,514869.194,0.0]
        addKnot sh k #corner #line [276046.546,514885.258,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269346.594,514793.753,0.0]
        addKnot sh k #corner #line [271196.771,514809.817,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.658,514835.862,0.0]
        addKnot sh k #corner #line [276046.835,514851.926,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [269346.884,514760.421,0.0]
        addKnot sh k #corner #line [271197.061,514776.484,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271197.061,514776.484,0.0]
        addKnot sh k #corner #line [271196.193,514876.481,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271196.193,514876.481,0.0]
        addKnot sh k #corner #line [269346.015,514860.417,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [276046.257,514918.590,0.0]
        addKnot sh k #corner #line [274196.079,514902.526,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.079,514902.526,0.0]
        addKnot sh k #corner #line [274196.948,514802.530,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.948,514802.530,0.0]
        addKnot sh k #corner #line [276047.125,514818.594,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324380.650,456826.199,0.0]
        addKnot sh k #corner #line [324467.392,456743.327,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325195.180,456057.525,0.0]
        addKnot sh k #corner #line [326654.677,454731.688,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324357.576,456802.143,0.0]
        addKnot sh k #corner #line [324444.532,456719.067,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325172.319,456033.265,0.0]
        addKnot sh k #corner #line [326632.564,454706.746,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324334.503,456778.086,0.0]
        addKnot sh k #corner #line [324421.671,456694.807,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324421.671,456694.807,0.0]
        addKnot sh k #corner #line [324490.253,456767.587,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324403.724,456850.256,0.0]
        addKnot sh k #corner #line [324490.253,456767.587,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325218.040,456081.785,0.0]
        addKnot sh k #corner #line [326676.790,454756.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325218.040,456081.785,0.0]
        addKnot sh k #corner #line [325149.459,456009.005,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325149.459,456009.005,0.0]
        addKnot sh k #corner #line [326610.451,454681.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326654.677,454731.688,0.0]
        addKnot sh k #corner #line [326746.886,454650.065,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327500.222,453992.429,0.0]
        addKnot sh k #corner #line [328816.037,452881.986,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326632.564,454706.746,0.0]
        addKnot sh k #corner #line [326724.964,454624.953,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327478.300,453967.317,0.0]
        addKnot sh k #corner #line [328794.809,452856.285,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326610.451,454681.803,0.0]
        addKnot sh k #corner #line [326703.043,454599.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326703.043,454599.842,0.0]
        addKnot sh k #corner #line [326768.807,454675.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326676.790,454756.631,0.0]
        addKnot sh k #corner #line [326768.807,454675.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327522.143,454017.541,0.0]
        addKnot sh k #corner #line [328837.264,452907.686,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327522.143,454017.541,0.0]
        addKnot sh k #corner #line [327456.379,453942.206,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327456.379,453942.206,0.0]
        addKnot sh k #corner #line [328773.582,452830.585,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333319.650,449419.310,0.0]
        addKnot sh k #corner #line [333416.335,449350.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334234.287,448775.024,0.0]
        addKnot sh k #corner #line [335658.805,447808.316,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333300.267,449392.191,0.0]
        addKnot sh k #corner #line [333397.158,449323.045,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334215.110,448747.759,0.0]
        addKnot sh k #corner #line [335640.380,447780.538,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333280.884,449365.073,0.0]
        addKnot sh k #corner #line [333377.982,449295.779,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333377.982,449295.779,0.0]
        addKnot sh k #corner #line [333435.511,449377.576,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333339.033,449446.428,0.0]
        addKnot sh k #corner #line [333435.511,449377.576,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334253.464,448802.290,0.0]
        addKnot sh k #corner #line [335677.230,447836.095,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334253.464,448802.290,0.0]
        addKnot sh k #corner #line [334195.934,448720.493,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334195.934,448720.493,0.0]
        addKnot sh k #corner #line [335621.955,447752.760,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332214.456,447873.817,0.0]
        addKnot sh k #corner #line [332310.264,447805.440,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333128.106,447229.997,0.0]
        addKnot sh k #corner #line [334608.587,446224.952,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332195.073,447846.699,0.0]
        addKnot sh k #corner #line [332291.083,447778.178,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333108.924,447202.735,0.0]
        addKnot sh k #corner #line [334590.162,446197.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332175.690,447819.580,0.0]
        addKnot sh k #corner #line [332271.901,447750.916,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332271.901,447750.916,0.0]
        addKnot sh k #corner #line [332329.446,447832.701,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332233.839,447900.935,0.0]
        addKnot sh k #corner #line [332329.446,447832.701,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333147.288,447257.258,0.0]
        addKnot sh k #corner #line [334627.012,446252.730,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333147.288,447257.258,0.0]
        addKnot sh k #corner #line [333089.743,447175.473,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333089.743,447175.473,0.0]
        addKnot sh k #corner #line [334571.737,446169.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325384.926,453318.223,0.0]
        addKnot sh k #corner #line [326748.323,452135.286,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327514.577,451492.749,0.0]
        addKnot sh k #corner #line [327606.066,451417.073,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325387.761,453271.165,0.0]
        addKnot sh k #corner #line [326726.905,452109.744,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327493.159,451467.207,0.0]
        addKnot sh k #corner #line [327584.838,451391.373,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325390.605,453224.117,0.0]
        addKnot sh k #corner #line [326705.486,452084.202,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326705.486,452084.202,0.0]
        addKnot sh k #corner #line [326769.741,452160.829,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325382.099,453365.291,0.0]
        addKnot sh k #corner #line [326769.741,452160.829,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327535.996,451518.291,0.0]
        addKnot sh k #corner #line [327627.293,451442.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327535.996,451518.291,0.0]
        addKnot sh k #corner #line [327471.741,451441.664,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327471.741,451441.664,0.0]
        addKnot sh k #corner #line [327563.610,451365.672,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327606.066,451417.073,0.0]
        addKnot sh k #corner #line [327697.661,451341.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328473.378,450710.446,0.0]
        addKnot sh k #corner #line [329879.343,449605.221,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327584.838,451391.373,0.0]
        addKnot sh k #corner #line [327676.625,451315.670,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328452.342,450684.588,0.0]
        addKnot sh k #corner #line [329859.025,449578.796,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327563.610,451365.672,0.0]
        addKnot sh k #corner #line [327655.589,451289.812,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327655.589,451289.812,0.0]
        addKnot sh k #corner #line [327718.698,451367.385,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327627.293,451442.773,0.0]
        addKnot sh k #corner #line [327718.698,451367.385,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328494.415,450736.304,0.0]
        addKnot sh k #corner #line [329899.660,449631.646,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328494.415,450736.304,0.0]
        addKnot sh k #corner #line [328431.305,450658.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328431.305,450658.731,0.0]
        addKnot sh k #corner #line [329838.707,449552.370,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329879.343,449605.221,0.0]
        addKnot sh k #corner #line [329971.125,449534.754,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330768.371,448931.100,0.0]
        addKnot sh k #corner #line [332214.456,447873.817,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329859.025,449578.796,0.0]
        addKnot sh k #corner #line [329951.003,449508.178,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330748.249,448904.525,0.0]
        addKnot sh k #corner #line [332195.073,447846.699,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329838.707,449552.370,0.0]
        addKnot sh k #corner #line [329930.881,449481.603,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329930.881,449481.603,0.0]
        addKnot sh k #corner #line [329991.247,449561.329,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329899.660,449631.646,0.0]
        addKnot sh k #corner #line [329991.247,449561.329,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330788.494,448957.675,0.0]
        addKnot sh k #corner #line [332233.839,447900.935,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330788.494,448957.675,0.0]
        addKnot sh k #corner #line [330728.127,448877.949,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330728.127,448877.949,0.0]
        addKnot sh k #corner #line [332175.690,447819.580,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334608.587,446224.952,0.0]
        addKnot sh k #corner #line [334703.182,446162.301,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335540.581,445615.708,0.0]
        addKnot sh k #corner #line [337058.801,444660.648,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334590.162,446197.174,0.0]
        addKnot sh k #corner #line [334684.962,446134.387,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335522.361,445587.795,0.0]
        addKnot sh k #corner #line [337041.356,444632.243,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334571.737,446169.395,0.0]
        addKnot sh k #corner #line [334666.742,446106.474,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334666.742,446106.474,0.0]
        addKnot sh k #corner #line [334721.403,446190.215,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334627.012,446252.730,0.0]
        addKnot sh k #corner #line [334721.403,446190.215,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335558.801,445643.622,0.0]
        addKnot sh k #corner #line [337076.245,444689.052,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335558.801,445643.622,0.0]
        addKnot sh k #corner #line [335504.141,445559.881,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335504.141,445559.881,0.0]
        addKnot sh k #corner #line [337023.912,444603.839,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337058.801,444660.648,0.0]
        addKnot sh k #corner #line [337160.383,444598.362,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338016.382,444081.386,0.0]
        addKnot sh k #corner #line [339649.113,443133.544,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337041.356,444632.243,0.0]
        addKnot sh k #corner #line [337143.150,444569.829,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337999.149,444052.852,0.0]
        addKnot sh k #corner #line [339632.706,443104.528,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337023.912,444603.839,0.0]
        addKnot sh k #corner #line [337125.917,444541.295,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337125.917,444541.295,0.0]
        addKnot sh k #corner #line [337177.616,444626.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337076.245,444689.052,0.0]
        addKnot sh k #corner #line [337177.616,444626.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338033.615,444109.920,0.0]
        addKnot sh k #corner #line [339665.521,443162.559,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338033.615,444109.920,0.0]
        addKnot sh k #corner #line [337981.917,444024.318,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337981.917,444024.318,0.0]
        addKnot sh k #corner #line [339616.298,443075.513,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339616.298,443075.513,0.0]
        addKnot sh k #corner #line [339665.521,443162.559,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328816.037,452881.986,0.0]
        addKnot sh k #corner #line [328915.040,452800.343,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329690.941,452169.488,0.0]
        addKnot sh k #corner #line [331037.452,451111.469,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328794.809,452856.285,0.0]
        addKnot sh k #corner #line [328894.011,452774.479,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329669.912,452143.624,0.0]
        addKnot sh k #corner #line [331017.134,451085.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328773.582,452830.585,0.0]
        addKnot sh k #corner #line [328872.983,452748.615,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328872.983,452748.615,0.0]
        addKnot sh k #corner #line [328936.069,452826.207,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328837.264,452907.686,0.0]
        addKnot sh k #corner #line [328936.069,452826.207,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329711.970,452195.352,0.0]
        addKnot sh k #corner #line [331057.770,451137.894,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329711.970,452195.352,0.0]
        addKnot sh k #corner #line [329648.883,452117.760,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329648.883,452117.760,0.0]
        addKnot sh k #corner #line [330996.817,451058.618,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331037.452,451111.469,0.0]
        addKnot sh k #corner #line [331131.135,451039.547,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331928.504,450436.054,0.0]
        addKnot sh k #corner #line [333319.650,449419.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331017.134,451085.043,0.0]
        addKnot sh k #corner #line [331111.018,451012.967,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331908.387,450409.474,0.0]
        addKnot sh k #corner #line [333300.267,449392.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330996.817,451058.618,0.0]
        addKnot sh k #corner #line [331090.902,450986.388,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331090.902,450986.388,0.0]
        addKnot sh k #corner #line [331151.252,451066.126,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331057.770,451137.894,0.0]
        addKnot sh k #corner #line [331151.252,451066.126,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331948.621,450462.633,0.0]
        addKnot sh k #corner #line [333339.033,449446.428,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331948.621,450462.633,0.0]
        addKnot sh k #corner #line [331888.270,450382.895,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331888.270,450382.895,0.0]
        addKnot sh k #corner #line [333280.884,449365.073,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338053.120,446279.699,0.0]
        addKnot sh k #corner #line [338154.701,446217.417,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339010.790,445700.589,0.0]
        addKnot sh k #corner #line [340586.323,444786.312,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338035.676,446251.295,0.0]
        addKnot sh k #corner #line [338137.473,446188.881,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338993.562,445672.053,0.0]
        addKnot sh k #corner #line [340569.916,444757.296,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338018.232,446222.891,0.0]
        addKnot sh k #corner #line [338120.245,446160.344,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338120.245,446160.344,0.0]
        addKnot sh k #corner #line [338171.929,446245.954,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338070.564,446308.104,0.0]
        addKnot sh k #corner #line [338171.929,446245.954,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339028.018,445729.126,0.0]
        addKnot sh k #corner #line [340602.730,444815.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339028.018,445729.126,0.0]
        addKnot sh k #corner #line [338976.334,445643.516,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338976.334,445643.516,0.0]
        addKnot sh k #corner #line [340553.510,444728.280,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [340553.510,444728.280,0.0]
        addKnot sh k #corner #line [340602.730,444815.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335658.805,447808.316,0.0]
        addKnot sh k #corner #line [335758.489,447742.303,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336596.022,447195.917,0.0]
        addKnot sh k #corner #line [338053.120,446279.699,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335640.380,447780.538,0.0]
        addKnot sh k #corner #line [335740.275,447714.385,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336577.809,447167.999,0.0]
        addKnot sh k #corner #line [338035.676,446251.295,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335621.955,447752.760,0.0]
        addKnot sh k #corner #line [335722.062,447686.467,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335722.062,447686.467,0.0]
        addKnot sh k #corner #line [335776.702,447770.221,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335677.230,447836.095,0.0]
        addKnot sh k #corner #line [335776.702,447770.221,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336614.235,447223.835,0.0]
        addKnot sh k #corner #line [338070.564,446308.104,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336614.235,447223.835,0.0]
        addKnot sh k #corner #line [336559.596,447140.080,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336559.596,447140.080,0.0]
        addKnot sh k #corner #line [338018.232,446222.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322920.013,450536.920,0.0]
        addKnot sh k #corner #line [325384.926,453318.223,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322944.959,450514.812,0.0]
        addKnot sh k #corner #line [325387.761,453271.165,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322895.066,450559.029,0.0]
        addKnot sh k #corner #line [325382.099,453365.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322969.905,450492.703,0.0]
        addKnot sh k #corner #line [325390.605,453224.117,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322895.066,450559.029,0.0]
        addKnot sh k #corner #line [322969.905,450492.703,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302035.829,484717.169,0.0]
        addKnot sh k #corner #line [302932.431,482527.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301949.405,484754.849,0.0]
        addKnot sh k #corner #line [302871.097,482501.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302122.302,484679.509,0.0]
        addKnot sh k #corner #line [302993.765,482553.758,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301863.030,484792.548,0.0]
        addKnot sh k #corner #line [302809.762,482475.382,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301949.405,484754.849,0.0]
        addKnot sh k #corner #line [304772.965,485863.873,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302035.829,484717.169,0.0]
        addKnot sh k #corner #line [304797.338,485801.821,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301863.030,484792.548,0.0]
        addKnot sh k #corner #line [304748.593,485925.925,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302122.302,484679.509,0.0]
        addKnot sh k #corner #line [304821.710,485739.769,0.0]
        updateShape sh
        addModifier sh (Extrude amount:wallHeight capStart:false capEnd:false)
        sh.isHidden = true
        append made sh
      )
      -- MOVABLE_PARTITIONS: source edges for REVIEW ONLY (hidden to avoid misleading walls)
      if makeReviewWalls do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REVIEW_MOVABLE_PARTITIONS_")
        sh.wirecolor = (color 229 182 56)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283322.536,477563.719,0.0]
        addKnot sh k #corner #line [288763.954,479701.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283432.214,477284.487,0.0]
        addKnot sh k #corner #line [288601.618,479314.959,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283322.536,477563.719,0.0]
        addKnot sh k #corner #line [283432.214,477284.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285812.246,472688.058,0.0]
        addKnot sh k #corner #line [290504.356,474820.266,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285936.360,472414.936,0.0]
        addKnot sh k #corner #line [290894.563,474668.063,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285812.246,472688.058,0.0]
        addKnot sh k #corner #line [285936.360,472414.936,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288763.954,479701.035,0.0]
        addKnot sh k #corner #line [290894.563,474668.063,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288601.618,479314.959,0.0]
        addKnot sh k #corner #line [290504.356,474820.266,0.0]
        updateShape sh
        addModifier sh (Extrude amount:wallHeight capStart:false capEnd:false)
        sh.isHidden = true
        append made sh
      )
      -- DOORS reference only, 1094 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_DOORS_")
        sh.wirecolor = (color 248 101 60)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271302.740,514122.845,0.0]
        addKnot sh k #corner #line [271506.345,514170.540,0.0]
        addKnot sh k #corner #line [271686.777,514276.249,0.0]
        addKnot sh k #corner #line [271827.932,514430.539,0.0]
        addKnot sh k #corner #line [271917.214,514619.639,0.0]
        addKnot sh k #corner #line [271946.653,514826.674,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271946.653,514826.674,0.0]
        addKnot sh k #corner #line [271979.683,514620.182,0.0]
        addKnot sh k #corner #line [272072.234,514432.660,0.0]
        addKnot sh k #corner #line [272216.047,514280.844,0.0]
        addKnot sh k #corner #line [272398.287,514178.284,0.0]
        addKnot sh k #corner #line [272602.691,514134.132,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272576.735,514244.135,0.0]
        addKnot sh k #corner #line [272574.629,514486.588,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272676.731,514245.003,0.0]
        addKnot sh k #corner #line [272674.626,514487.456,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272602.706,514132.344,0.0]
        addKnot sh k #corner #line [272596.629,514832.317,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272696.625,514833.185,0.0]
        addKnot sh k #corner #line [272596.629,514832.317,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272696.625,514833.185,0.0]
        addKnot sh k #corner #line [272695.757,514933.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272652.704,514132.778,0.0]
        addKnot sh k #corner #line [272645.759,514932.748,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272695.757,514933.182,0.0]
        addKnot sh k #corner #line [272645.759,514932.748,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271226.785,514232.414,0.0]
        addKnot sh k #corner #line [271224.680,514474.868,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271326.782,514233.282,0.0]
        addKnot sh k #corner #line [271324.677,514475.736,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271252.757,514120.623,0.0]
        addKnot sh k #corner #line [271245.811,514920.593,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271196.682,514820.163,0.0]
        addKnot sh k #corner #line [271195.813,514920.159,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271196.682,514820.163,0.0]
        addKnot sh k #corner #line [271296.678,514821.031,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271195.813,514920.159,0.0]
        addKnot sh k #corner #line [271245.811,514920.593,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271302.755,514121.057,0.0]
        addKnot sh k #corner #line [271296.678,514821.031,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271252.757,514120.623,0.0]
        addKnot sh k #corner #line [271302.755,514121.057,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272652.704,514132.778,0.0]
        addKnot sh k #corner #line [272602.706,514132.344,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272676.731,514245.003,0.0]
        addKnot sh k #corner #line [272651.732,514244.786,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272576.735,514244.135,0.0]
        addKnot sh k #corner #line [272601.734,514244.352,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272674.626,514487.456,0.0]
        addKnot sh k #corner #line [272649.627,514487.239,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272574.629,514486.588,0.0]
        addKnot sh k #corner #line [272599.629,514486.805,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271326.782,514233.282,0.0]
        addKnot sh k #corner #line [271301.783,514233.065,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271226.785,514232.414,0.0]
        addKnot sh k #corner #line [271251.784,514232.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271324.677,514475.736,0.0]
        addKnot sh k #corner #line [271299.678,514475.519,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [271224.680,514474.868,0.0]
        addKnot sh k #corner #line [271249.679,514475.085,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272802.683,514135.868,0.0]
        addKnot sh k #corner #line [273006.289,514183.563,0.0]
        addKnot sh k #corner #line [273186.721,514289.272,0.0]
        addKnot sh k #corner #line [273327.876,514443.562,0.0]
        addKnot sh k #corner #line [273417.157,514632.662,0.0]
        addKnot sh k #corner #line [273446.597,514839.697,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [273446.597,514839.697,0.0]
        addKnot sh k #corner #line [273479.626,514633.204,0.0]
        addKnot sh k #corner #line [273572.178,514445.683,0.0]
        addKnot sh k #corner #line [273715.991,514293.867,0.0]
        addKnot sh k #corner #line [273898.231,514191.307,0.0]
        addKnot sh k #corner #line [274102.634,514147.154,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274076.678,514257.158,0.0]
        addKnot sh k #corner #line [274074.573,514499.611,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274176.674,514258.026,0.0]
        addKnot sh k #corner #line [274174.569,514500.479,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274102.650,514145.366,0.0]
        addKnot sh k #corner #line [274096.572,514845.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.568,514846.208,0.0]
        addKnot sh k #corner #line [274096.572,514845.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274196.568,514846.208,0.0]
        addKnot sh k #corner #line [274195.700,514946.204,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274152.648,514145.801,0.0]
        addKnot sh k #corner #line [274145.702,514945.770,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274195.700,514946.204,0.0]
        addKnot sh k #corner #line [274145.702,514945.770,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272726.729,514245.437,0.0]
        addKnot sh k #corner #line [272724.624,514487.890,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272826.725,514246.305,0.0]
        addKnot sh k #corner #line [272824.620,514488.759,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272752.700,514133.646,0.0]
        addKnot sh k #corner #line [272745.755,514933.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272696.625,514833.185,0.0]
        addKnot sh k #corner #line [272695.757,514933.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272696.625,514833.185,0.0]
        addKnot sh k #corner #line [272796.621,514834.054,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272695.757,514933.182,0.0]
        addKnot sh k #corner #line [272745.755,514933.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272802.699,514134.080,0.0]
        addKnot sh k #corner #line [272796.621,514834.054,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272752.700,514133.646,0.0]
        addKnot sh k #corner #line [272802.699,514134.080,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274152.648,514145.801,0.0]
        addKnot sh k #corner #line [274102.650,514145.366,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274176.674,514258.026,0.0]
        addKnot sh k #corner #line [274151.675,514257.809,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274076.678,514257.158,0.0]
        addKnot sh k #corner #line [274101.677,514257.375,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274174.569,514500.479,0.0]
        addKnot sh k #corner #line [274149.570,514500.262,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [274074.573,514499.611,0.0]
        addKnot sh k #corner #line [274099.572,514499.828,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272826.725,514246.305,0.0]
        addKnot sh k #corner #line [272801.726,514246.088,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272726.729,514245.437,0.0]
        addKnot sh k #corner #line [272751.728,514245.654,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272824.620,514488.759,0.0]
        addKnot sh k #corner #line [272799.621,514488.542,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [272724.624,514487.890,0.0]
        addKnot sh k #corner #line [272749.623,514488.107,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317260.991,456708.405,0.0]
        addKnot sh k #corner #line [317380.544,456879.977,0.0]
        addKnot sh k #corner #line [317444.083,457079.208,0.0]
        addKnot sh k #corner #line [317445.935,457288.317,0.0]
        addKnot sh k #corner #line [317385.937,457488.643,0.0]
        addKnot sh k #corner #line [317269.442,457662.306,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317269.442,457662.306,0.0]
        addKnot sh k #corner #line [317432.037,457530.803,0.0]
        addKnot sh k #corner #line [317626.220,457453.196,0.0]
        addKnot sh k #corner #line [317834.663,457436.412,0.0]
        addKnot sh k #corner #line [318038.763,457481.948,0.0]
        addKnot sh k #corner #line [318220.304,457585.741,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318127.468,457650.207,0.0]
        addKnot sh k #corner #line [317963.836,457829.128,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318201.261,457717.695,0.0]
        addKnot sh k #corner #line [318037.629,457896.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318221.510,457584.421,0.0]
        addKnot sh k #corner #line [317749.098,458100.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317822.892,458168.462,0.0]
        addKnot sh k #corner #line [317749.098,458100.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317822.892,458168.462,0.0]
        addKnot sh k #corner #line [317755.404,458242.255,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318258.407,457618.165,0.0]
        addKnot sh k #corner #line [317718.508,458208.511,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317755.404,458242.255,0.0]
        addKnot sh k #corner #line [317718.508,458208.511,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317131.258,456739.127,0.0]
        addKnot sh k #corner #line [316967.627,456918.048,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317205.052,456806.615,0.0]
        addKnot sh k #corner #line [317041.420,456985.536,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317225.301,456673.341,0.0]
        addKnot sh k #corner #line [316685.402,457263.688,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316715.993,457156.151,0.0]
        addKnot sh k #corner #line [316648.505,457229.944,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316715.993,457156.151,0.0]
        addKnot sh k #corner #line [316789.786,457223.638,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316648.505,457229.944,0.0]
        addKnot sh k #corner #line [316685.402,457263.688,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317262.198,456707.085,0.0]
        addKnot sh k #corner #line [316789.786,457223.638,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317225.301,456673.341,0.0]
        addKnot sh k #corner #line [317262.198,456707.085,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318258.407,457618.165,0.0]
        addKnot sh k #corner #line [318221.510,457584.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318201.261,457717.695,0.0]
        addKnot sh k #corner #line [318182.813,457700.823,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318127.468,457650.207,0.0]
        addKnot sh k #corner #line [318145.916,457667.079,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318037.629,457896.616,0.0]
        addKnot sh k #corner #line [318019.181,457879.744,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317963.836,457829.128,0.0]
        addKnot sh k #corner #line [317982.284,457846.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317205.052,456806.615,0.0]
        addKnot sh k #corner #line [317186.603,456789.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317131.258,456739.127,0.0]
        addKnot sh k #corner #line [317149.707,456755.999,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317041.420,456985.536,0.0]
        addKnot sh k #corner #line [317022.972,456968.664,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316967.627,456918.048,0.0]
        addKnot sh k #corner #line [316986.075,456934.920,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320463.665,453912.906,0.0]
        addKnot sh k #corner #line [320638.037,454028.338,0.0]
        addKnot sh k #corner #line [320838.725,454087.112,0.0]
        addKnot sh k #corner #line [321047.819,454083.983,0.0]
        addKnot sh k #corner #line [321246.659,454019.229,0.0]
        addKnot sh k #corner #line [321417.498,453898.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321417.498,453898.631,0.0]
        addKnot sh k #corner #line [321289.905,454064.312,0.0]
        addKnot sh k #corner #line [321216.947,454260.289,0.0]
        addKnot sh k #corner #line [321205.133,454469.073,0.0]
        addKnot sh k #corner #line [321255.518,454672.029,0.0]
        addKnot sh k #corner #line [321363.606,454851.046,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321425.842,454756.701,0.0]
        addKnot sh k #corner #line [321600.815,454588.853,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321495.069,454828.866,0.0]
        addKnot sh k #corner #line [321670.041,454661.018,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321362.316,454852.284,0.0]
        addKnot sh k #corner #line [321867.468,454367.701,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321936.694,454439.865,0.0]
        addKnot sh k #corner #line [321867.468,454367.701,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321936.694,454439.865,0.0]
        addKnot sh k #corner #line [322008.859,454370.639,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321396.929,454888.366,0.0]
        addKnot sh k #corner #line [321974.246,454334.557,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322008.859,454370.639,0.0]
        addKnot sh k #corner #line [321974.246,454334.557,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320491.289,453782.478,0.0]
        addKnot sh k #corner #line [320666.261,453614.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320560.515,453854.643,0.0]
        addKnot sh k #corner #line [320735.487,453686.795,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320427.762,453878.061,0.0]
        addKnot sh k #corner #line [321005.079,453324.252,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320898.301,453357.396,0.0]
        addKnot sh k #corner #line [320970.466,453288.170,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320898.301,453357.396,0.0]
        addKnot sh k #corner #line [320967.528,453429.560,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320970.466,453288.170,0.0]
        addKnot sh k #corner #line [321005.079,453324.252,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320462.375,453914.144,0.0]
        addKnot sh k #corner #line [320967.528,453429.560,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320427.762,453878.061,0.0]
        addKnot sh k #corner #line [320462.375,453914.144,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321396.929,454888.366,0.0]
        addKnot sh k #corner #line [321362.316,454852.284,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321495.069,454828.866,0.0]
        addKnot sh k #corner #line [321477.762,454810.824,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321425.842,454756.701,0.0]
        addKnot sh k #corner #line [321443.149,454774.742,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321670.041,454661.018,0.0]
        addKnot sh k #corner #line [321652.734,454642.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321600.815,454588.853,0.0]
        addKnot sh k #corner #line [321618.121,454606.894,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320560.515,453854.643,0.0]
        addKnot sh k #corner #line [320543.209,453836.602,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320491.289,453782.478,0.0]
        addKnot sh k #corner #line [320508.595,453800.520,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320735.487,453686.795,0.0]
        addKnot sh k #corner #line [320718.181,453668.754,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320666.261,453614.631,0.0]
        addKnot sh k #corner #line [320683.568,453632.672,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295643.010,514969.714,0.0]
        addKnot sh k #corner #line [295648.675,514239.299,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295605.553,514969.423,0.0]
        addKnot sh k #corner #line [295611.218,514239.009,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295643.010,514969.714,0.0]
        addKnot sh k #corner #line [295605.553,514969.423,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295611.218,514239.009,0.0]
        addKnot sh k #corner #line [295648.675,514239.299,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294893.867,514963.903,0.0]
        addKnot sh k #corner #line [294930.190,514742.027,0.0]
        addKnot sh k #corner #line [295032.274,514541.708,0.0]
        addKnot sh k #corner #line [295190.445,514381.926,0.0]
        addKnot sh k #corner #line [295389.719,514277.818,0.0]
        addKnot sh k #corner #line [295611.216,514239.249,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294187.844,514228.209,0.0]
        addKnot sh k #corner #line [294408.716,514270.210,0.0]
        addKnot sh k #corner #line [294606.351,514377.396,0.0]
        addKnot sh k #corner #line [294762.025,514539.612,0.0]
        addKnot sh k #corner #line [294860.989,514741.490,0.0]
        addKnot sh k #corner #line [294893.867,514963.903,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294182.181,514958.383,0.0]
        addKnot sh k #corner #line [294187.846,514227.969,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294144.723,514958.093,0.0]
        addKnot sh k #corner #line [294150.389,514227.678,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294187.846,514227.969,0.0]
        addKnot sh k #corner #line [294150.389,514227.678,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294144.723,514958.093,0.0]
        addKnot sh k #corner #line [294182.181,514958.383,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299242.948,537941.834,0.0]
        addKnot sh k #corner #line [299451.755,537930.450,0.0]
        addKnot sh k #corner #line [299654.608,537981.253,0.0]
        addKnot sh k #corner #line [299833.402,538089.710,0.0]
        addKnot sh k #corner #line [299972.181,538246.140,0.0]
        addKnot sh k #corner #line [300058.560,538436.584,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300058.560,538436.584,0.0]
        addKnot sh k #corner #line [300032.290,538229.123,0.0]
        addKnot sh k #corner #line [300068.474,538023.160,0.0]
        addKnot sh k #corner #line [300163.883,537837.076,0.0]
        addKnot sh k #corner #line [300310.001,537687.478,0.0]
        addKnot sh k #corner #line [300493.788,537587.717,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300499.759,537700.583,0.0]
        addKnot sh k #corner #line [300565.805,537933.876,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300595.977,537673.343,0.0]
        addKnot sh k #corner #line [300662.023,537906.637,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300493.301,537585.996,0.0]
        addKnot sh k #corner #line [300683.980,538259.525,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300780.198,538232.286,0.0]
        addKnot sh k #corner #line [300683.980,538259.525,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300780.198,538232.286,0.0]
        addKnot sh k #corner #line [300807.438,538328.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300541.410,537572.376,0.0]
        addKnot sh k #corner #line [300759.329,538342.124,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300807.438,538328.504,0.0]
        addKnot sh k #corner #line [300759.329,538342.124,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299200.809,538068.320,0.0]
        addKnot sh k #corner #line [299266.855,538301.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299297.028,538041.080,0.0]
        addKnot sh k #corner #line [299363.074,538274.374,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299194.352,537953.733,0.0]
        addKnot sh k #corner #line [299412.270,538723.481,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299336.921,538640.882,0.0]
        addKnot sh k #corner #line [299364.161,538737.101,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299336.921,538640.882,0.0]
        addKnot sh k #corner #line [299433.140,538613.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299364.161,538737.101,0.0]
        addKnot sh k #corner #line [299412.270,538723.481,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299242.461,537940.113,0.0]
        addKnot sh k #corner #line [299433.140,538613.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299194.352,537953.733,0.0]
        addKnot sh k #corner #line [299242.461,537940.113,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300541.410,537572.376,0.0]
        addKnot sh k #corner #line [300493.301,537585.996,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300595.977,537673.343,0.0]
        addKnot sh k #corner #line [300571.922,537680.153,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300499.759,537700.583,0.0]
        addKnot sh k #corner #line [300523.813,537693.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300662.023,537906.637,0.0]
        addKnot sh k #corner #line [300637.969,537913.447,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300565.805,537933.876,0.0]
        addKnot sh k #corner #line [300589.859,537927.067,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299297.028,538041.080,0.0]
        addKnot sh k #corner #line [299272.973,538047.890,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299200.809,538068.320,0.0]
        addKnot sh k #corner #line [299224.864,538061.510,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299363.074,538274.374,0.0]
        addKnot sh k #corner #line [299339.019,538281.184,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299266.855,538301.614,0.0]
        addKnot sh k #corner #line [299290.910,538294.804,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303362.057,476771.661,0.0]
        addKnot sh k #corner #line [303690.548,476118.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303395.561,476788.507,0.0]
        addKnot sh k #corner #line [303724.052,476135.192,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303362.057,476771.661,0.0]
        addKnot sh k #corner #line [303395.561,476788.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303724.052,476135.192,0.0]
        addKnot sh k #corner #line [303690.548,476118.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304032.124,477108.575,0.0]
        addKnot sh k #corner #line [304101.081,476894.318,0.0]
        addKnot sh k #corner #line [304101.609,476669.238,0.0]
        addKnot sh k #corner #line [304033.657,476454.660,0.0]
        addKnot sh k #corner #line [303903.663,476270.913,0.0]
        addKnot sh k #corner #line [303723.944,476135.407,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304997.070,476775.543,0.0]
        addKnot sh k #corner #line [304781.115,476712.102,0.0]
        addKnot sh k #corner #line [304556.096,476717.346,0.0]
        addKnot sh k #corner #line [304343.331,476790.777,0.0]
        addKnot sh k #corner #line [304162.978,476925.440,0.0]
        addKnot sh k #corner #line [304032.124,477108.575,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304668.687,477428.643,0.0]
        addKnot sh k #corner #line [304997.178,476775.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304702.190,477445.489,0.0]
        addKnot sh k #corner #line [305030.681,476792.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304997.178,476775.328,0.0]
        addKnot sh k #corner #line [305030.681,476792.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304702.190,477445.489,0.0]
        addKnot sh k #corner #line [304668.687,477428.643,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278800.109,536452.256,0.0]
        addKnot sh k #corner #line [279130.785,535951.603,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279387.947,536332.064,0.0]
        addKnot sh k #corner #line [279297.205,536116.257,0.0]
        addKnot sh k #corner #line [279130.785,535951.603,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279475.133,535881.197,0.0]
        addKnot sh k #corner #line [279386.698,536097.959,0.0]
        addKnot sh k #corner #line [279387.947,536332.064,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279975.786,536211.873,0.0]
        addKnot sh k #corner #line [279475.133,535881.197,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279825.985,543127.315,0.0]
        addKnot sh k #corner #line [279306.749,542826.659,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279671.427,542547.564,0.0]
        addKnot sh k #corner #line [279461.330,542650.842,0.0]
        addKnot sh k #corner #line [279306.749,542826.659,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279216.211,542487.048,0.0]
        addKnot sh k #corner #line [279437.800,542562.580,0.0]
        addKnot sh k #corner #line [279671.427,542547.564,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279516.868,541967.813,0.0]
        addKnot sh k #corner #line [279216.211,542487.048,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279083.421,540243.610,0.0]
        addKnot sh k #corner #line [278572.962,539928.281,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278945.444,539659.690,0.0]
        addKnot sh k #corner #line [278732.490,539756.940,0.0]
        addKnot sh k #corner #line [278572.962,539928.281,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278492.137,539586.229,0.0]
        addKnot sh k #corner #line [278711.484,539668.044,0.0]
        addKnot sh k #corner #line [278945.444,539659.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278807.467,539075.771,0.0]
        addKnot sh k #corner #line [278492.137,539586.229,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280416.027,536121.860,0.0]
        addKnot sh k #corner #line [280746.703,535621.207,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281003.865,536001.668,0.0]
        addKnot sh k #corner #line [280913.123,535785.861,0.0]
        addKnot sh k #corner #line [280746.703,535621.207,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281091.051,535550.801,0.0]
        addKnot sh k #corner #line [281002.616,535767.563,0.0]
        addKnot sh k #corner #line [281003.865,536001.668,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281591.703,535881.477,0.0]
        addKnot sh k #corner #line [281091.051,535550.801,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307364.813,472560.613,0.0]
        addKnot sh k #corner #line [306994.287,473191.039,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307332.483,472541.612,0.0]
        addKnot sh k #corner #line [306961.958,473172.038,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307364.813,472560.613,0.0]
        addKnot sh k #corner #line [307332.483,472541.612,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306961.958,473172.038,0.0]
        addKnot sh k #corner #line [306994.287,473191.039,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306718.222,472180.587,0.0]
        addKnot sh k #corner #line [306635.396,472389.874,0.0]
        addKnot sh k #corner #line [306620.145,472614.437,0.0]
        addKnot sh k #corner #line [306673.914,472833.001,0.0]
        addKnot sh k #corner #line [306791.609,473024.858,0.0]
        addKnot sh k #corner #line [306962.080,473171.831,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305733.557,472449.781,0.0]
        addKnot sh k #corner #line [305944.899,472527.213,0.0]
        addKnot sh k #corner #line [306169.779,472536.701,0.0]
        addKnot sh k #corner #line [306386.892,472477.345,0.0]
        addKnot sh k #corner #line [306575.668,472354.769,0.0]
        addKnot sh k #corner #line [306718.222,472180.587,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306103.960,471819.562,0.0]
        addKnot sh k #corner #line [305733.435,472449.988,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306071.631,471800.561,0.0]
        addKnot sh k #corner #line [305701.105,472430.987,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305733.435,472449.988,0.0]
        addKnot sh k #corner #line [305701.105,472430.987,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306071.631,471800.561,0.0]
        addKnot sh k #corner #line [306103.960,471819.562,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304893.116,472636.709,0.0]
        addKnot sh k #corner #line [305532.161,472992.163,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304874.887,472669.481,0.0]
        addKnot sh k #corner #line [305513.933,473024.934,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304893.116,472636.709,0.0]
        addKnot sh k #corner #line [304874.887,472669.481,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305513.933,473024.934,0.0]
        addKnot sh k #corner #line [305532.161,472992.163,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304528.547,473292.140,0.0]
        addKnot sh k #corner #line [304739.742,473369.974,0.0]
        addKnot sh k #corner #line [304964.604,473379.889,0.0]
        addKnot sh k #corner #line [305181.829,473320.946,0.0]
        addKnot sh k #corner #line [305370.838,473198.729,0.0]
        addKnot sh k #corner #line [305513.722,473024.818,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304821.043,474270.137,0.0]
        addKnot sh k #corner #line [304893.436,474057.016,0.0]
        addKnot sh k #corner #line [304897.582,473831.974,0.0]
        addKnot sh k #corner #line [304833.088,473616.331,0.0]
        addKnot sh k #corner #line [304706.065,473430.519,0.0]
        addKnot sh k #corner #line [304528.547,473292.140,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304182.208,473914.800,0.0]
        addKnot sh k #corner #line [304821.253,474270.254,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304163.979,473947.571,0.0]
        addKnot sh k #corner #line [304803.025,474303.025,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304821.253,474270.254,0.0]
        addKnot sh k #corner #line [304803.025,474303.025,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304163.979,473947.571,0.0]
        addKnot sh k #corner #line [304182.208,473914.800,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296868.724,473327.292,0.0]
        addKnot sh k #corner #line [296377.345,473080.215,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296859.336,473345.964,0.0]
        addKnot sh k #corner #line [296367.957,473098.886,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295820.450,472800.194,0.0]
        addKnot sh k #corner #line [295811.061,472818.865,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296868.724,473327.292,0.0]
        addKnot sh k #corner #line [296859.336,473345.964,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296311.828,473047.272,0.0]
        addKnot sh k #corner #line [296302.440,473065.943,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296302.440,473065.943,0.0]
        addKnot sh k #corner #line [295811.061,472818.865,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296311.828,473047.272,0.0]
        addKnot sh k #corner #line [295820.450,472800.194,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296377.345,473080.215,0.0]
        addKnot sh k #corner #line [296367.957,473098.886,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296809.470,473363.514,0.0]
        addKnot sh k #corner #line [295826.713,472869.360,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299280.557,474540.022,0.0]
        addKnot sh k #corner #line [298789.179,474292.944,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299271.169,474558.693,0.0]
        addKnot sh k #corner #line [298779.790,474311.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298232.283,474012.924,0.0]
        addKnot sh k #corner #line [298222.895,474031.595,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299280.557,474540.022,0.0]
        addKnot sh k #corner #line [299271.169,474558.693,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298723.661,474260.001,0.0]
        addKnot sh k #corner #line [298714.273,474278.672,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298714.273,474278.672,0.0]
        addKnot sh k #corner #line [298222.895,474031.595,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298723.661,474260.001,0.0]
        addKnot sh k #corner #line [298232.283,474012.924,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298789.179,474292.944,0.0]
        addKnot sh k #corner #line [298779.790,474311.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299221.303,474576.243,0.0]
        addKnot sh k #corner #line [298238.546,474082.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303600.491,474998.545,0.0]
        addKnot sh k #corner #line [303781.798,475570.496,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303324.264,475531.179,0.0]
        addKnot sh k #corner #line [303549.121,475596.342,0.0]
        addKnot sh k #corner #line [303781.798,475570.496,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303619.989,475882.505,0.0]
        addKnot sh k #corner #line [303507.068,475677.431,0.0]
        addKnot sh k #corner #line [303324.264,475531.179,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303048.038,476063.813,0.0]
        addKnot sh k #corner #line [303619.989,475882.505,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296815.142,536567.309,0.0]
        addKnot sh k #corner #line [297002.685,536474.800,0.0]
        addKnot sh k #corner #line [297154.532,536331.021,0.0]
        addKnot sh k #corner #line [297257.134,536148.804,0.0]
        addKnot sh k #corner #line [297301.332,535944.411,0.0]
        addKnot sh k #corner #line [297283.183,535736.082,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297283.183,535736.082,0.0]
        addKnot sh k #corner #line [297362.060,535929.753,0.0]
        addKnot sh k #corner #line [297494.625,536091.483,0.0]
        addKnot sh k #corner #line [297669.048,536206.838,0.0]
        addKnot sh k #corner #line [297869.762,536265.523,0.0]
        addKnot sh k #corner #line [298078.855,536262.301,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298028.692,536161.019,0.0]
        addKnot sh k #corner #line [297971.805,535925.324,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298125.901,536137.557,0.0]
        addKnot sh k #corner #line [298069.014,535901.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298079.275,536264.039,0.0]
        addKnot sh k #corner #line [297915.040,535583.578,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298012.248,535560.116,0.0]
        addKnot sh k #corner #line [297915.040,535583.578,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298012.248,535560.116,0.0]
        addKnot sh k #corner #line [297988.786,535462.908,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298127.879,536252.308,0.0]
        addKnot sh k #corner #line [297940.182,535474.639,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297988.786,535462.908,0.0]
        addKnot sh k #corner #line [297940.182,535474.639,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296716.375,536477.758,0.0]
        addKnot sh k #corner #line [296659.488,536242.063,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296813.583,536454.295,0.0]
        addKnot sh k #corner #line [296756.696,536218.601,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296766.957,536580.778,0.0]
        addKnot sh k #corner #line [296579.260,535803.108,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296554.118,535912.048,0.0]
        addKnot sh k #corner #line [296530.656,535814.839,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296554.118,535912.048,0.0]
        addKnot sh k #corner #line [296651.327,535888.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296530.656,535814.839,0.0]
        addKnot sh k #corner #line [296579.260,535803.108,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296815.562,536569.047,0.0]
        addKnot sh k #corner #line [296651.327,535888.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296766.957,536580.778,0.0]
        addKnot sh k #corner #line [296815.562,536569.047,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298127.879,536252.308,0.0]
        addKnot sh k #corner #line [298079.275,536264.039,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298125.901,536137.557,0.0]
        addKnot sh k #corner #line [298101.598,536143.422,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298028.692,536161.019,0.0]
        addKnot sh k #corner #line [298052.994,536155.153,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298069.014,535901.862,0.0]
        addKnot sh k #corner #line [298044.711,535907.728,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297971.805,535925.324,0.0]
        addKnot sh k #corner #line [297996.107,535919.459,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296813.583,536454.295,0.0]
        addKnot sh k #corner #line [296789.281,536460.161,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296716.375,536477.758,0.0]
        addKnot sh k #corner #line [296740.677,536471.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296756.696,536218.601,0.0]
        addKnot sh k #corner #line [296732.394,536224.466,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296659.488,536242.063,0.0]
        addKnot sh k #corner #line [296683.790,536236.197,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287034.673,508923.543,0.0]
        addKnot sh k #corner #line [286486.147,508883.316,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287036.202,508902.701,0.0]
        addKnot sh k #corner #line [286487.675,508862.474,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285864.483,508837.725,0.0]
        addKnot sh k #corner #line [285866.011,508816.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287034.673,508923.543,0.0]
        addKnot sh k #corner #line [287036.202,508902.701,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286413.010,508877.952,0.0]
        addKnot sh k #corner #line [286414.538,508857.110,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286414.538,508857.110,0.0]
        addKnot sh k #corner #line [285866.011,508816.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286413.010,508877.952,0.0]
        addKnot sh k #corner #line [285864.483,508837.725,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286486.147,508883.316,0.0]
        addKnot sh k #corner #line [286487.675,508862.474,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287002.419,508862.040,0.0]
        addKnot sh k #corner #line [285905.365,508781.585,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289726.982,509120.989,0.0]
        addKnot sh k #corner #line [289178.455,509080.761,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289728.511,509100.146,0.0]
        addKnot sh k #corner #line [289179.984,509059.919,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288556.791,509035.171,0.0]
        addKnot sh k #corner #line [288558.320,509014.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289726.982,509120.989,0.0]
        addKnot sh k #corner #line [289728.511,509100.146,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289105.318,509075.398,0.0]
        addKnot sh k #corner #line [289106.847,509054.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289106.847,509054.555,0.0]
        addKnot sh k #corner #line [288558.320,509014.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289105.318,509075.398,0.0]
        addKnot sh k #corner #line [288556.791,509035.171,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289178.455,509080.761,0.0]
        addKnot sh k #corner #line [289179.984,509059.919,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289694.727,509059.485,0.0]
        addKnot sh k #corner #line [288597.674,508979.031,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293741.293,509757.139,0.0]
        addKnot sh k #corner #line [294139.093,510206.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293704.968,510356.038,0.0]
        addKnot sh k #corner #line [293936.922,510324.351,0.0]
        addKnot sh k #corner #line [294139.093,510206.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294117.815,510557.137,0.0]
        addKnot sh k #corner #line [293931.392,510415.528,0.0]
        addKnot sh k #corner #line [293704.968,510356.038,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293668.643,510954.937,0.0]
        addKnot sh k #corner #line [294117.815,510557.137,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292388.975,514591.954,0.0]
        addKnot sh k #corner #line [292388.588,514641.953,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291413.617,514634.410,0.0]
        addKnot sh k #corner #line [291414.004,514584.412,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292388.654,514591.952,0.0]
        addKnot sh k #corner #line [292337.165,514296.295,0.0]
        addKnot sh k #corner #line [292198.195,514030.303,0.0]
        addKnot sh k #corner #line [291984.911,513819.177,0.0]
        addKnot sh k #corner #line [291717.519,513682.919,0.0]
        addKnot sh k #corner #line [291421.353,513634.440,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291413.617,514634.410,0.0]
        addKnot sh k #corner #line [292388.588,514641.953,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291414.004,514584.412,0.0]
        addKnot sh k #corner #line [292388.975,514591.954,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293561.534,513838.934,0.0]
        addKnot sh k #corner #line [294438.616,513866.034,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293562.924,513793.956,0.0]
        addKnot sh k #corner #line [294440.005,513821.055,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293561.534,513838.934,0.0]
        addKnot sh k #corner #line [293562.924,513793.956,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294440.005,513821.055,0.0]
        addKnot sh k #corner #line [294438.616,513866.034,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293589.328,512939.364,0.0]
        addKnot sh k #corner #line [293854.796,512989.154,0.0]
        addKnot sh k #corner #line [294092.545,513117.323,0.0]
        addKnot sh k #corner #line [294280.051,513311.729,0.0]
        addKnot sh k #corner #line [294399.549,513553.953,0.0]
        addKnot sh k #corner #line [294439.717,513821.046,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294492.526,512111.862,0.0]
        addKnot sh k #corner #line [294435.945,512375.965,0.0]
        addKnot sh k #corner #line [294301.722,512610.350,0.0]
        addKnot sh k #corner #line [294102.572,512792.809,0.0]
        addKnot sh k #corner #line [293857.364,512906.057,0.0]
        addKnot sh k #corner #line [293589.328,512939.364,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293615.733,512084.771,0.0]
        addKnot sh k #corner #line [294492.814,512111.871,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293617.123,512039.793,0.0]
        addKnot sh k #corner #line [294494.204,512066.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294492.814,512111.871,0.0]
        addKnot sh k #corner #line [294494.204,512066.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293617.123,512039.793,0.0]
        addKnot sh k #corner #line [293615.733,512084.771,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294375.249,509301.661,0.0]
        addKnot sh k #corner #line [294322.058,510030.159,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294412.608,509304.389,0.0]
        addKnot sh k #corner #line [294359.417,510032.886,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294375.249,509301.661,0.0]
        addKnot sh k #corner #line [294412.608,509304.389,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294359.417,510032.886,0.0]
        addKnot sh k #corner #line [294322.058,510030.159,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295122.426,509356.216,0.0]
        addKnot sh k #corner #line [295071.739,509575.258,0.0]
        addKnot sh k #corner #line [294956.835,509768.508,0.0]
        addKnot sh k #corner #line [294788.599,509917.657,0.0]
        addKnot sh k #corner #line [294582.972,510008.575,0.0]
        addKnot sh k #corner #line [294359.434,510032.647,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295779.070,510136.301,0.0]
        addKnot sh k #corner #line [295561.400,510080.014,0.0]
        addKnot sh k #corner #line [295371.160,509960.193,0.0]
        addKnot sh k #corner #line [295226.373,509788.188,0.0]
        addKnot sh k #corner #line [295140.758,509580.297,0.0]
        addKnot sh k #corner #line [295122.426,509356.216,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295832.244,509408.043,0.0]
        addKnot sh k #corner #line [295779.053,510136.540,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295869.603,509410.771,0.0]
        addKnot sh k #corner #line [295816.412,510139.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295779.053,510136.540,0.0]
        addKnot sh k #corner #line [295816.412,510139.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295869.603,509410.771,0.0]
        addKnot sh k #corner #line [295832.244,509408.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303042.033,473580.237,0.0]
        addKnot sh k #corner #line [303018.411,473624.305,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302159.086,473163.669,0.0]
        addKnot sh k #corner #line [302182.709,473119.601,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303041.751,473580.086,0.0]
        addKnot sh k #corner #line [303133.846,473294.459,0.0]
        addKnot sh k #corner #line [303134.709,472994.353,0.0]
        addKnot sh k #corner #line [303044.259,472708.201,0.0]
        addKnot sh k #corner #line [302871.064,472463.113,0.0]
        addKnot sh k #corner #line [302631.534,472282.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302159.086,473163.669,0.0]
        addKnot sh k #corner #line [303018.411,473624.305,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302182.709,473119.601,0.0]
        addKnot sh k #corner #line [303042.033,473580.237,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317369.290,454094.883,0.0]
        addKnot sh k #corner #line [317334.592,454130.884,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316632.566,453454.286,0.0]
        addKnot sh k #corner #line [316667.264,453418.285,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317369.059,454094.660,0.0]
        addKnot sh k #corner #line [317535.227,453844.755,0.0]
        addKnot sh k #corner #line [317617.519,453556.151,0.0]
        addKnot sh k #corner #line [317608.138,453256.190,0.0]
        addKnot sh k #corner #line [317507.972,452973.292,0.0]
        addKnot sh k #corner #line [317326.513,452734.259,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316632.566,453454.286,0.0]
        addKnot sh k #corner #line [317334.592,454130.884,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316667.264,453418.285,0.0]
        addKnot sh k #corner #line [317369.290,454094.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321395.613,448814.503,0.0]
        addKnot sh k #corner #line [320956.298,449200.802,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321415.423,448837.032,0.0]
        addKnot sh k #corner #line [320976.108,449223.331,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321395.613,448814.503,0.0]
        addKnot sh k #corner #line [321415.423,448837.032,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320976.108,449223.331,0.0]
        addKnot sh k #corner #line [320956.298,449200.802,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321791.818,449265.082,0.0]
        addKnot sh k #corner #line [321597.840,449378.250,0.0]
        addKnot sh k #corner #line [321375.519,449409.997,0.0]
        addKnot sh k #corner #line [321157.619,449355.646,0.0]
        addKnot sh k #corner #line [320976.253,449223.204,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321729.042,450079.305,0.0]
        addKnot sh k #corner #line [321620.885,449882.489,0.0]
        addKnot sh k #corner #line [321594.849,449659.427,0.0]
        addKnot sh k #corner #line [321654.770,449442.993,0.0]
        addKnot sh k #corner #line [321791.818,449265.082,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322168.212,449693.132,0.0]
        addKnot sh k #corner #line [321728.898,450079.432,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322188.023,449715.661,0.0]
        addKnot sh k #corner #line [321748.708,450101.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321728.898,450079.432,0.0]
        addKnot sh k #corner #line [321748.708,450101.961,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322188.023,449715.661,0.0]
        addKnot sh k #corner #line [322168.212,449693.132,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317671.260,444579.029,0.0]
        addKnot sh k #corner #line [317231.945,444965.329,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317691.070,444601.558,0.0]
        addKnot sh k #corner #line [317251.756,444987.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317671.260,444579.029,0.0]
        addKnot sh k #corner #line [317691.070,444601.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317251.756,444987.858,0.0]
        addKnot sh k #corner #line [317231.945,444965.329,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318067.465,445029.608,0.0]
        addKnot sh k #corner #line [317873.487,445142.776,0.0]
        addKnot sh k #corner #line [317651.166,445174.524,0.0]
        addKnot sh k #corner #line [317433.266,445120.172,0.0]
        addKnot sh k #corner #line [317251.900,444987.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318004.689,445843.831,0.0]
        addKnot sh k #corner #line [317896.532,445647.015,0.0]
        addKnot sh k #corner #line [317870.496,445423.954,0.0]
        addKnot sh k #corner #line [317930.417,445207.519,0.0]
        addKnot sh k #corner #line [318067.465,445029.608,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318443.860,445457.658,0.0]
        addKnot sh k #corner #line [318004.545,445843.958,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318463.670,445480.187,0.0]
        addKnot sh k #corner #line [318024.355,445866.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318004.545,445843.958,0.0]
        addKnot sh k #corner #line [318024.355,445866.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318463.670,445480.187,0.0]
        addKnot sh k #corner #line [318443.860,445457.658,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283238.289,509764.145,0.0]
        addKnot sh k #corner #line [283188.423,509760.488,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283117.111,510732.876,0.0]
        addKnot sh k #corner #line [283166.977,510736.533,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283238.265,509764.464,0.0]
        addKnot sh k #corner #line [283528.792,509839.690,0.0]
        addKnot sh k #corner #line [283782.676,509999.711,0.0]
        addKnot sh k #corner #line [283975.866,510229.368,0.0]
        addKnot sh k #corner #line [284090.058,510506.901,0.0]
        addKnot sh k #corner #line [284114.433,510806.016,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283117.111,510732.876,0.0]
        addKnot sh k #corner #line [283188.423,509760.488,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [283166.977,510736.533,0.0]
        addKnot sh k #corner #line [283238.289,509764.145,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278091.971,510592.713,0.0]
        addKnot sh k #corner #line [278094.205,510542.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279068.231,510586.320,0.0]
        addKnot sh k #corner #line [279065.998,510636.270,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278092.291,510592.727,0.0]
        addKnot sh k #corner #line [278132.823,510890.085,0.0]
        addKnot sh k #corner #line [278261.871,511161.029,0.0]
        addKnot sh k #corner #line [278467.210,511379.891,0.0]
        addKnot sh k #corner #line [278729.385,511525.934,0.0]
        addKnot sh k #corner #line [279023.558,511585.321,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279068.231,510586.320,0.0]
        addKnot sh k #corner #line [278094.205,510542.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279065.998,510636.270,0.0]
        addKnot sh k #corner #line [278091.971,510592.713,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280136.806,508998.928,0.0]
        addKnot sh k #corner #line [280139.875,508949.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279166.712,508889.191,0.0]
        addKnot sh k #corner #line [279163.644,508939.097,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280136.486,508998.909,0.0]
        addKnot sh k #corner #line [280064.694,509290.302,0.0]
        addKnot sh k #corner #line [279907.680,509546.058,0.0]
        addKnot sh k #corner #line [279680.320,509741.945,0.0]
        addKnot sh k #corner #line [279404.154,509859.404,0.0]
        addKnot sh k #corner #line [279105.346,509887.306,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279166.712,508889.191,0.0]
        addKnot sh k #corner #line [280139.875,508949.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279163.644,508939.097,0.0]
        addKnot sh k #corner #line [280136.806,508998.928,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282634.990,510846.346,0.0]
        addKnot sh k #corner #line [282637.198,510796.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281663.149,510753.339,0.0]
        addKnot sh k #corner #line [281660.941,510803.290,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [282634.670,510846.332,0.0]
        addKnot sh k #corner #line [282567.909,511138.919,0.0]
        addKnot sh k #corner #line [282415.324,511397.342,0.0]
        addKnot sh k #corner #line [282191.373,511597.117,0.0]
        addKnot sh k #corner #line [281917.271,511719.316,0.0]
        addKnot sh k #corner #line [281618.989,511752.363,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281663.149,510753.339,0.0]
        addKnot sh k #corner #line [282637.198,510796.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [281660.941,510803.290,0.0]
        addKnot sh k #corner #line [282634.990,510846.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294042.737,470657.172,0.0]
        addKnot sh k #corner #line [293998.066,470634.711,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294436.067,469763.631,0.0]
        addKnot sh k #corner #line [294480.738,469786.092,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294042.881,470656.886,0.0]
        addKnot sh k #corner #line [294330.820,470741.478,0.0]
        addKnot sh k #corner #line [294630.845,470734.491,0.0]
        addKnot sh k #corner #line [294914.534,470636.586,0.0]
        addKnot sh k #corner #line [295155.007,470457.040,0.0]
        addKnot sh k #corner #line [295329.482,470212.862,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294436.067,469763.631,0.0]
        addKnot sh k #corner #line [293998.066,470634.711,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294480.738,469786.092,0.0]
        addKnot sh k #corner #line [294042.737,470657.172,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290051.708,467304.144,0.0]
        addKnot sh k #corner #line [290027.982,467348.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290886.219,467810.816,0.0]
        addKnot sh k #corner #line [290909.945,467766.804,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290051.990,467304.296,0.0]
        addKnot sh k #corner #line [290239.428,467069.922,0.0]
        addKnot sh k #corner #line [290489.269,466903.656,0.0]
        addKnot sh k #corner #line [290777.841,466821.253,0.0]
        addKnot sh k #corner #line [291077.805,466830.517,0.0]
        addKnot sh k #corner #line [291360.742,466930.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290886.219,467810.816,0.0]
        addKnot sh k #corner #line [290027.982,467348.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290909.945,467766.804,0.0]
        addKnot sh k #corner #line [290051.708,467304.144,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290988.310,469721.638,0.0]
        addKnot sh k #corner #line [290965.323,469766.041,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290099.472,469317.791,0.0]
        addKnot sh k #corner #line [290122.459,469273.388,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290988.025,469721.491,0.0]
        addKnot sh k #corner #line [291076.010,469434.570,0.0]
        addKnot sh k #corner #line [291072.563,469134.483,0.0]
        addKnot sh k #corner #line [290978.013,468849.659,0.0]
        addKnot sh k #corner #line [290801.317,468607.084,0.0]
        addKnot sh k #corner #line [290559.216,468429.739,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290099.472,469317.791,0.0]
        addKnot sh k #corner #line [290965.323,469766.041,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290122.459,469273.388,0.0]
        addKnot sh k #corner #line [290988.310,469721.638,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294080.580,469418.747,0.0]
        addKnot sh k #corner #line [294056.831,469462.747,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293198.832,468999.646,0.0]
        addKnot sh k #corner #line [293222.580,468955.646,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294080.297,469418.595,0.0]
        addKnot sh k #corner #line [294173.212,469133.233,0.0]
        addKnot sh k #corner #line [294174.936,468833.131,0.0]
        addKnot sh k #corner #line [294085.308,468546.720,0.0]
        addKnot sh k #corner #line [293912.817,468301.136,0.0]
        addKnot sh k #corner #line [293673.807,468119.647,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293198.832,468999.646,0.0]
        addKnot sh k #corner #line [294056.831,469462.747,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293222.580,468955.646,0.0]
        addKnot sh k #corner #line [294080.580,469418.747,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293051.737,533702.857,0.0]
        addKnot sh k #corner #line [292512.888,533813.047,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293047.550,533682.382,0.0]
        addKnot sh k #corner #line [292508.701,533792.572,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291902.192,533937.929,0.0]
        addKnot sh k #corner #line [291898.006,533917.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293051.737,533702.857,0.0]
        addKnot sh k #corner #line [293047.550,533682.382,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292441.041,533827.739,0.0]
        addKnot sh k #corner #line [292436.854,533807.264,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292436.854,533807.264,0.0]
        addKnot sh k #corner #line [291898.006,533917.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292441.041,533827.739,0.0]
        addKnot sh k #corner #line [291902.192,533937.929,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292512.888,533813.047,0.0]
        addKnot sh k #corner #line [292508.701,533792.572,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293003.997,533652.419,0.0]
        addKnot sh k #corner #line [291926.299,533872.799,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290619.646,534200.199,0.0]
        addKnot sh k #corner #line [289835.866,534360.475,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290615.459,534179.724,0.0]
        addKnot sh k #corner #line [289831.679,534340.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288947.581,534542.121,0.0]
        addKnot sh k #corner #line [288943.394,534521.646,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290619.646,534200.199,0.0]
        addKnot sh k #corner #line [290615.459,534179.724,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289731.362,534381.845,0.0]
        addKnot sh k #corner #line [289727.175,534361.370,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289727.175,534361.370,0.0]
        addKnot sh k #corner #line [288943.394,534521.646,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289731.362,534381.845,0.0]
        addKnot sh k #corner #line [288947.581,534542.121,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289835.866,534360.475,0.0]
        addKnot sh k #corner #line [289831.679,534340.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290555.578,534153.100,0.0]
        addKnot sh k #corner #line [288988.017,534473.652,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295666.088,534738.837,0.0]
        addKnot sh k #corner #line [295990.414,534234.047,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295538.481,534152.563,0.0]
        addKnot sh k #corner #line [295772.552,534148.358,0.0]
        addKnot sh k #corner #line [295990.414,534234.047,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295915.664,533890.616,0.0]
        addKnot sh k #corner #line [295753.125,534059.103,0.0]
        addKnot sh k #corner #line [295538.481,534152.563,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295410.874,533566.290,0.0]
        addKnot sh k #corner #line [295915.664,533890.616,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296716.167,538921.661,0.0]
        addKnot sh k #corner #line [297564.087,538695.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296704.582,538878.178,0.0]
        addKnot sh k #corner #line [297552.501,538652.260,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296716.167,538921.661,0.0]
        addKnot sh k #corner #line [296704.582,538878.178,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297552.501,538652.260,0.0]
        addKnot sh k #corner #line [297564.087,538695.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296484.457,538052.000,0.0]
        addKnot sh k #corner #line [296753.041,538023.458,0.0]
        addKnot sh k #corner #line [297017.583,538077.953,0.0]
        addKnot sh k #corner #line [297253.019,538210.323,0.0]
        addKnot sh k #corner #line [297437.044,538408.027,0.0]
        addKnot sh k #corner #line [297552.223,538652.335,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297111.973,536999.979,0.0]
        addKnot sh k #corner #line [297133.619,537269.207,0.0]
        addKnot sh k #corner #line [297072.359,537532.264,0.0]
        addKnot sh k #corner #line [296933.995,537764.229,0.0]
        addKnot sh k #corner #line [296731.637,537943.124,0.0]
        addKnot sh k #corner #line [296484.457,538052.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296264.332,537225.822,0.0]
        addKnot sh k #corner #line [297112.251,536999.905,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296252.746,537182.339,0.0]
        addKnot sh k #corner #line [297100.666,536956.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [297112.251,536999.905,0.0]
        addKnot sh k #corner #line [297100.666,536956.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [296252.746,537182.339,0.0]
        addKnot sh k #corner #line [296264.332,537225.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295613.309,539289.891,0.0]
        addKnot sh k #corner #line [295626.930,539338.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294688.806,539603.607,0.0]
        addKnot sh k #corner #line [294675.185,539555.498,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295613.001,539289.978,0.0]
        addKnot sh k #corner #line [295480.828,539020.544,0.0]
        addKnot sh k #corner #line [295272.972,538804.071,0.0]
        addKnot sh k #corner #line [295009.126,538661.070,0.0]
        addKnot sh k #corner #line [294714.286,538605.088,0.0]
        addKnot sh k #corner #line [294416.388,538641.428,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294688.806,539603.607,0.0]
        addKnot sh k #corner #line [295626.930,539338.000,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294675.185,539555.498,0.0]
        addKnot sh k #corner #line [295613.309,539289.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312303.616,455843.209,0.0]
        addKnot sh k #corner #line [311705.226,455887.131,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311911.548,456297.392,0.0]
        addKnot sh k #corner #line [311767.584,456112.782,0.0]
        addKnot sh k #corner #line [311705.226,455887.131,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311475.558,456153.185,0.0]
        addKnot sh k #corner #line [311707.895,456181.927,0.0]
        addKnot sh k #corner #line [311911.548,456297.392,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311519.480,456751.576,0.0]
        addKnot sh k #corner #line [311475.558,456153.185,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313780.384,455054.880,0.0]
        addKnot sh k #corner #line [313815.768,454823.461,0.0]
        addKnot sh k #corner #line [313937.018,454623.199,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314379.787,455028.114,0.0]
        addKnot sh k #corner #line [313780.384,455054.880,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310097.566,461007.557,0.0]
        addKnot sh k #corner #line [310115.005,460774.099,0.0]
        addKnot sh k #corner #line [310220.457,460565.086,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310693.122,460934.664,0.0]
        addKnot sh k #corner #line [310097.566,461007.557,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319406.631,453689.588,0.0]
        addKnot sh k #corner #line [319925.202,454205.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319380.192,453716.181,0.0]
        addKnot sh k #corner #line [319898.763,454231.749,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319406.631,453689.588,0.0]
        addKnot sh k #corner #line [319380.192,453716.181,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319898.763,454231.749,0.0]
        addKnot sh k #corner #line [319925.202,454205.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318877.843,454221.455,0.0]
        addKnot sh k #corner #line [319059.982,454353.692,0.0]
        addKnot sh k #corner #line [319273.710,454424.271,0.0]
        addKnot sh k #corner #line [319498.780,454426.503,0.0]
        addKnot sh k #corner #line [319713.866,454360.178,0.0]
        addKnot sh k #corner #line [319898.592,454231.580,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318893.895,455242.128,0.0]
        addKnot sh k #corner #line [319021.418,455056.659,0.0]
        addKnot sh k #corner #line [319086.493,454841.191,0.0]
        addKnot sh k #corner #line [319082.954,454616.138,0.0]
        addKnot sh k #corner #line [319011.136,454402.823,0.0]
        addKnot sh k #corner #line [318877.843,454221.455,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318375.494,454726.729,0.0]
        addKnot sh k #corner #line [318894.065,455242.298,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318349.055,454753.323,0.0]
        addKnot sh k #corner #line [318867.626,455268.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318894.065,455242.298,0.0]
        addKnot sh k #corner #line [318867.626,455268.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318349.055,454753.323,0.0]
        addKnot sh k #corner #line [318375.494,454726.729,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311496.415,452175.748,0.0]
        addKnot sh k #corner #line [311090.552,451804.567,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311482.312,452191.170,0.0]
        addKnot sh k #corner #line [311076.449,451819.989,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310630.574,451383.896,0.0]
        addKnot sh k #corner #line [310616.470,451399.317,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311496.415,452175.748,0.0]
        addKnot sh k #corner #line [311482.312,452191.170,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311036.437,451755.076,0.0]
        addKnot sh k #corner #line [311022.333,451770.498,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311022.333,451770.498,0.0]
        addKnot sh k #corner #line [310616.470,451399.317,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311036.437,451755.076,0.0]
        addKnot sh k #corner #line [310630.574,451383.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311090.552,451804.567,0.0]
        addKnot sh k #corner #line [311076.449,451819.989,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311429.554,452194.526,0.0]
        addKnot sh k #corner #line [310617.828,451452.164,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316655.509,456535.983,0.0]
        addKnot sh k #corner #line [317255.185,456516.273,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317065.607,456098.011,0.0]
        addKnot sh k #corner #line [317201.995,456288.287,0.0]
        addKnot sh k #corner #line [317255.185,456516.273,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317495.415,456259.714,0.0]
        addKnot sh k #corner #line [317264.428,456221.610,0.0]
        addKnot sh k #corner #line [317065.607,456098.011,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317475.704,455660.038,0.0]
        addKnot sh k #corner #line [317495.415,456259.714,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313267.184,453795.199,0.0]
        addKnot sh k #corner #line [312861.321,453424.018,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313253.080,453810.621,0.0]
        addKnot sh k #corner #line [312847.217,453439.440,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312401.343,453003.347,0.0]
        addKnot sh k #corner #line [312387.239,453018.768,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313267.184,453795.199,0.0]
        addKnot sh k #corner #line [313253.080,453810.621,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312807.206,453374.528,0.0]
        addKnot sh k #corner #line [312793.102,453389.949,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312793.102,453389.949,0.0]
        addKnot sh k #corner #line [312387.239,453018.768,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312807.206,453374.528,0.0]
        addKnot sh k #corner #line [312401.343,453003.347,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312861.321,453424.018,0.0]
        addKnot sh k #corner #line [312847.217,453439.440,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313200.322,453813.977,0.0]
        addKnot sh k #corner #line [312388.596,453071.615,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322105.528,446348.212,0.0]
        addKnot sh k #corner #line [322703.074,446402.419,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322566.387,445964.013,0.0]
        addKnot sh k #corner #line [322678.333,446169.622,0.0]
        addKnot sh k #corner #line [322703.074,446402.419,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322973.039,446177.361,0.0]
        addKnot sh k #corner #line [322748.494,446111.131,0.0]
        addKnot sh k #corner #line [322566.387,445964.013,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323027.247,445579.814,0.0]
        addKnot sh k #corner #line [322973.039,446177.361,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336316.972,448438.929,0.0]
        addKnot sh k #corner #line [336522.337,448269.355,0.0]
        addKnot sh k #corner #line [336662.938,448043.165,0.0]
        addKnot sh k #corner #line [336724.106,447783.957,0.0]
        addKnot sh k #corner #line [336699.460,447518.772,0.0]
        addKnot sh k #corner #line [336591.571,447275.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335831.913,447770.858,0.0]
        addKnot sh k #corner #line [336282.442,448461.456,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336316.972,448438.929,0.0]
        addKnot sh k #corner #line [335866.443,447748.331,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335866.443,447748.331,0.0]
        addKnot sh k #corner #line [335831.913,447770.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335752.330,447724.325,0.0]
        addKnot sh k #corner #line [335797.383,447793.384,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335797.383,447793.384,0.0]
        addKnot sh k #corner #line [335831.913,447770.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335831.913,447770.858,0.0]
        addKnot sh k #corner #line [335809.387,447736.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335809.387,447736.328,0.0]
        addKnot sh k #corner #line [335843.916,447713.802,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335821.390,447679.272,0.0]
        addKnot sh k #corner #line [335752.330,447724.325,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335752.330,447724.325,0.0]
        addKnot sh k #corner #line [335752.330,447724.325,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335843.916,447713.802,0.0]
        addKnot sh k #corner #line [335821.390,447679.272,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336278.918,448316.770,0.0]
        addKnot sh k #corner #line [336192.234,448183.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336185.970,448377.406,0.0]
        addKnot sh k #corner #line [336099.287,448244.533,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336282.442,448461.456,0.0]
        addKnot sh k #corner #line [336316.972,448438.929,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336581.048,447183.690,0.0]
        addKnot sh k #corner #line [336581.048,447183.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336511.988,447228.743,0.0]
        addKnot sh k #corner #line [336581.048,447183.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336534.514,447263.273,0.0]
        addKnot sh k #corner #line [336511.988,447228.743,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336569.044,447240.746,0.0]
        addKnot sh k #corner #line [336534.514,447263.273,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336591.571,447275.276,0.0]
        addKnot sh k #corner #line [336569.044,447240.746,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336626.100,447252.750,0.0]
        addKnot sh k #corner #line [336591.571,447275.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336581.048,447183.690,0.0]
        addKnot sh k #corner #line [336626.100,447252.750,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336185.970,448377.406,0.0]
        addKnot sh k #corner #line [336215.179,448358.351,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336099.287,448244.533,0.0]
        addKnot sh k #corner #line [336128.496,448225.478,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336249.709,448335.825,0.0]
        addKnot sh k #corner #line [336278.918,448316.770,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336163.026,448202.951,0.0]
        addKnot sh k #corner #line [336192.234,448183.896,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338688.535,446933.107,0.0]
        addKnot sh k #corner #line [338899.693,446770.802,0.0]
        addKnot sh k #corner #line [339048.101,446549.656,0.0]
        addKnot sh k #corner #line [339118.276,446292.741,0.0]
        addKnot sh k #corner #line [339102.899,446026.857,0.0]
        addKnot sh k #corner #line [339003.572,445779.745,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338227.084,446248.517,0.0]
        addKnot sh k #corner #line [338653.240,446954.415,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338688.535,446933.107,0.0]
        addKnot sh k #corner #line [338262.379,446227.209,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338262.379,446227.209,0.0]
        addKnot sh k #corner #line [338227.084,446248.517,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338149.173,446199.235,0.0]
        addKnot sh k #corner #line [338191.789,446269.825,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338191.789,446269.825,0.0]
        addKnot sh k #corner #line [338227.084,446248.517,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338227.084,446248.517,0.0]
        addKnot sh k #corner #line [338205.776,446213.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338205.776,446213.222,0.0]
        addKnot sh k #corner #line [338241.071,446191.914,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338219.763,446156.619,0.0]
        addKnot sh k #corner #line [338149.173,446199.235,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338149.173,446199.235,0.0]
        addKnot sh k #corner #line [338149.173,446199.235,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338241.071,446191.914,0.0]
        addKnot sh k #corner #line [338219.763,446156.619,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338654.767,446809.694,0.0]
        addKnot sh k #corner #line [338572.773,446673.877,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338559.761,446867.050,0.0]
        addKnot sh k #corner #line [338477.767,446731.233,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338653.240,446954.415,0.0]
        addKnot sh k #corner #line [338688.535,446933.107,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338996.251,445687.847,0.0]
        addKnot sh k #corner #line [338996.251,445687.847,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338925.661,445730.463,0.0]
        addKnot sh k #corner #line [338996.251,445687.847,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338946.969,445765.758,0.0]
        addKnot sh k #corner #line [338925.661,445730.463,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338982.264,445744.450,0.0]
        addKnot sh k #corner #line [338946.969,445765.758,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339003.572,445779.745,0.0]
        addKnot sh k #corner #line [338982.264,445744.450,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [339038.867,445758.437,0.0]
        addKnot sh k #corner #line [339003.572,445779.745,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338996.251,445687.847,0.0]
        addKnot sh k #corner #line [339038.867,445758.437,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338559.761,446867.050,0.0]
        addKnot sh k #corner #line [338589.616,446849.026,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338477.767,446731.233,0.0]
        addKnot sh k #corner #line [338507.622,446713.209,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338624.911,446827.718,0.0]
        addKnot sh k #corner #line [338654.767,446809.694,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338542.917,446691.901,0.0]
        addKnot sh k #corner #line [338572.773,446673.877,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333998.793,450027.019,0.0]
        addKnot sh k #corner #line [334198.114,449850.380,0.0]
        addKnot sh k #corner #line [334330.734,449619.420,0.0]
        addKnot sh k #corner #line [334382.817,449358.235,0.0]
        addKnot sh k #corner #line [334348.930,449094.072,0.0]
        addKnot sh k #corner #line [334232.608,448854.490,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333490.711,449376.285,0.0]
        addKnot sh k #corner #line [333965.070,450050.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333998.793,450027.019,0.0]
        addKnot sh k #corner #line [333524.434,449352.567,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333524.434,449352.567,0.0]
        addKnot sh k #corner #line [333490.711,449376.285,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333409.553,449332.558,0.0]
        addKnot sh k #corner #line [333456.989,449400.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333456.989,449400.003,0.0]
        addKnot sh k #corner #line [333490.711,449376.285,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333490.711,449376.285,0.0]
        addKnot sh k #corner #line [333466.993,449342.562,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333466.993,449342.562,0.0]
        addKnot sh k #corner #line [333500.716,449318.844,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333476.998,449285.122,0.0]
        addKnot sh k #corner #line [333409.553,449332.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333409.553,449332.558,0.0]
        addKnot sh k #corner #line [333409.553,449332.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333500.716,449318.844,0.0]
        addKnot sh k #corner #line [333476.998,449285.122,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333956.498,449906.262,0.0]
        addKnot sh k #corner #line [333865.229,449776.495,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333865.724,449970.106,0.0]
        addKnot sh k #corner #line [333774.455,449840.339,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333965.070,450050.737,0.0]
        addKnot sh k #corner #line [333998.793,450027.019,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334218.895,448763.327,0.0]
        addKnot sh k #corner #line [334218.895,448763.327,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334151.450,448810.763,0.0]
        addKnot sh k #corner #line [334218.895,448763.327,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334175.168,448844.486,0.0]
        addKnot sh k #corner #line [334151.450,448810.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334208.890,448820.768,0.0]
        addKnot sh k #corner #line [334175.168,448844.486,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334232.608,448854.490,0.0]
        addKnot sh k #corner #line [334208.890,448820.768,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334266.331,448830.772,0.0]
        addKnot sh k #corner #line [334232.608,448854.490,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334218.895,448763.327,0.0]
        addKnot sh k #corner #line [334266.331,448830.772,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333865.724,449970.106,0.0]
        addKnot sh k #corner #line [333894.249,449950.043,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333774.455,449840.339,0.0]
        addKnot sh k #corner #line [333802.981,449820.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333927.972,449926.325,0.0]
        addKnot sh k #corner #line [333956.498,449906.262,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333836.704,449796.558,0.0]
        addKnot sh k #corner #line [333865.229,449776.495,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331736.864,451695.507,0.0]
        addKnot sh k #corner #line [331929.897,451512.017,0.0]
        addKnot sh k #corner #line [332054.372,451276.568,0.0]
        addKnot sh k #corner #line [332097.305,451013.724,0.0]
        addKnot sh k #corner #line [332054.216,450750.905,0.0]
        addKnot sh k #corner #line [331929.600,450515.530,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331206.373,451062.909,0.0]
        addKnot sh k #corner #line [331703.990,451720.388,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331736.864,451695.507,0.0]
        addKnot sh k #corner #line [331239.247,451038.028,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331239.247,451038.028,0.0]
        addKnot sh k #corner #line [331206.373,451062.909,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331123.737,451022.041,0.0]
        addKnot sh k #corner #line [331173.499,451087.789,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331173.499,451087.789,0.0]
        addKnot sh k #corner #line [331206.373,451062.909,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331206.373,451062.909,0.0]
        addKnot sh k #corner #line [331181.492,451030.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331181.492,451030.035,0.0]
        addKnot sh k #corner #line [331214.366,451005.154,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331189.485,450972.280,0.0]
        addKnot sh k #corner #line [331123.737,451022.041,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331123.737,451022.041,0.0]
        addKnot sh k #corner #line [331123.737,451022.041,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331214.366,451005.154,0.0]
        addKnot sh k #corner #line [331189.485,450972.280,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331690.379,451576.300,0.0]
        addKnot sh k #corner #line [331594.635,451449.799,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331601.889,451643.274,0.0]
        addKnot sh k #corner #line [331506.146,451516.773,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331703.990,451720.388,0.0]
        addKnot sh k #corner #line [331736.864,451695.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331912.713,450424.901,0.0]
        addKnot sh k #corner #line [331912.713,450424.901,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331846.965,450474.663,0.0]
        addKnot sh k #corner #line [331912.713,450424.901,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331871.845,450507.537,0.0]
        addKnot sh k #corner #line [331846.965,450474.663,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331904.719,450482.656,0.0]
        addKnot sh k #corner #line [331871.845,450507.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331929.600,450515.530,0.0]
        addKnot sh k #corner #line [331904.719,450482.656,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331962.474,450490.649,0.0]
        addKnot sh k #corner #line [331929.600,450515.530,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331912.713,450424.901,0.0]
        addKnot sh k #corner #line [331962.474,450490.649,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331601.889,451643.274,0.0]
        addKnot sh k #corner #line [331629.697,451622.228,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331506.146,451516.773,0.0]
        addKnot sh k #corner #line [331533.954,451495.726,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331662.571,451597.347,0.0]
        addKnot sh k #corner #line [331690.379,451576.300,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331566.828,451470.846,0.0]
        addKnot sh k #corner #line [331594.635,451449.799,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329543.213,453434.843,0.0]
        addKnot sh k #corner #line [329729.748,453244.751,0.0]
        addKnot sh k #corner #line [329845.961,453005.116,0.0]
        addKnot sh k #corner #line [329879.728,452740.938,0.0]
        addKnot sh k #corner #line [329827.526,452479.777,0.0]
        addKnot sh k #corner #line [329694.800,452248.878,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328991.045,452821.075,0.0]
        addKnot sh k #corner #line [329511.224,453460.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329543.213,453434.843,0.0]
        addKnot sh k #corner #line [329023.034,452795.066,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329023.034,452795.066,0.0]
        addKnot sh k #corner #line [328991.045,452821.075,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328907.038,452783.106,0.0]
        addKnot sh k #corner #line [328959.056,452847.084,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328959.056,452847.084,0.0]
        addKnot sh k #corner #line [328991.045,452821.075,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328991.045,452821.075,0.0]
        addKnot sh k #corner #line [328965.036,452789.086,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328965.036,452789.086,0.0]
        addKnot sh k #corner #line [328997.025,452763.077,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328971.016,452731.088,0.0]
        addKnot sh k #corner #line [328907.038,452783.106,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328907.038,452783.106,0.0]
        addKnot sh k #corner #line [328907.038,452783.106,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328997.025,452763.077,0.0]
        addKnot sh k #corner #line [328971.016,452731.088,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329492.611,453317.325,0.0]
        addKnot sh k #corner #line [329392.526,453194.230,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329406.503,453387.336,0.0]
        addKnot sh k #corner #line [329306.419,453264.240,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329511.224,453460.852,0.0]
        addKnot sh k #corner #line [329543.213,453434.843,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329674.771,452158.891,0.0]
        addKnot sh k #corner #line [329674.771,452158.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329610.794,452210.909,0.0]
        addKnot sh k #corner #line [329674.771,452158.891,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329636.803,452242.898,0.0]
        addKnot sh k #corner #line [329610.794,452210.909,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329668.791,452216.889,0.0]
        addKnot sh k #corner #line [329636.803,452242.898,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329694.800,452248.878,0.0]
        addKnot sh k #corner #line [329668.791,452216.889,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329726.789,452222.869,0.0]
        addKnot sh k #corner #line [329694.800,452248.878,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329674.771,452158.891,0.0]
        addKnot sh k #corner #line [329726.789,452222.869,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329406.503,453387.336,0.0]
        addKnot sh k #corner #line [329433.563,453365.335,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329306.419,453264.240,0.0]
        addKnot sh k #corner #line [329333.478,453242.240,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329465.551,453339.326,0.0]
        addKnot sh k #corner #line [329492.611,453317.325,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329365.467,453216.231,0.0]
        addKnot sh k #corner #line [329392.526,453194.230,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325140.199,457330.288,0.0]
        addKnot sh k #corner #line [325312.363,457127.088,0.0]
        addKnot sh k #corner #line [325410.776,456879.611,0.0]
        addKnot sh k #corner #line [325425.171,456613.672,0.0]
        addKnot sh k #corner #line [325354.047,456357.017,0.0]
        addKnot sh k #corner #line [325204.823,456136.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324544.707,456758.456,0.0]
        addKnot sh k #corner #line [325110.194,457358.562,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325140.199,457330.288,0.0]
        addKnot sh k #corner #line [324574.712,456730.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324574.712,456730.182,0.0]
        addKnot sh k #corner #line [324544.707,456758.456,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324458.153,456726.720,0.0]
        addKnot sh k #corner #line [324514.702,456786.731,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324514.702,456786.731,0.0]
        addKnot sh k #corner #line [324544.707,456758.456,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324544.707,456758.456,0.0]
        addKnot sh k #corner #line [324516.433,456728.451,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324516.433,456728.451,0.0]
        addKnot sh k #corner #line [324546.438,456700.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324518.164,456670.171,0.0]
        addKnot sh k #corner #line [324458.153,456726.720,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324458.153,456726.720,0.0]
        addKnot sh k #corner #line [324458.153,456726.720,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324546.438,456700.177,0.0]
        addKnot sh k #corner #line [324518.164,456670.171,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325081.154,457216.776,0.0]
        addKnot sh k #corner #line [324972.353,457101.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325000.386,457292.885,0.0]
        addKnot sh k #corner #line [324891.585,457177.422,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325110.194,457358.562,0.0]
        addKnot sh k #corner #line [325140.199,457330.288,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325178.280,456048.136,0.0]
        addKnot sh k #corner #line [325178.280,456048.136,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325118.269,456104.685,0.0]
        addKnot sh k #corner #line [325178.280,456048.136,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325146.544,456134.690,0.0]
        addKnot sh k #corner #line [325118.269,456104.685,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325176.549,456106.416,0.0]
        addKnot sh k #corner #line [325146.544,456134.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325204.823,456136.421,0.0]
        addKnot sh k #corner #line [325176.549,456106.416,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325234.828,456108.147,0.0]
        addKnot sh k #corner #line [325204.823,456136.421,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325178.280,456048.136,0.0]
        addKnot sh k #corner #line [325234.828,456108.147,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325000.386,457292.885,0.0]
        addKnot sh k #corner #line [325025.768,457268.968,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324891.585,457177.422,0.0]
        addKnot sh k #corner #line [324916.966,457153.505,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [325055.773,457240.693,0.0]
        addKnot sh k #corner #line [325081.154,457216.776,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324946.971,457125.231,0.0]
        addKnot sh k #corner #line [324972.353,457101.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336758.343,443764.152,0.0]
        addKnot sh k #corner #line [337000.300,443652.854,0.0]
        addKnot sh k #corner #line [337265.113,443624.487,0.0]
        addKnot sh k #corner #line [337525.154,443682.009,0.0]
        addKnot sh k #corner #line [337753.296,443819.419,0.0]
        addKnot sh k #corner #line [337925.737,444022.383,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337149.331,444491.290,0.0]
        addKnot sh k #corner #line [336723.052,443785.466,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336758.343,443764.152,0.0]
        addKnot sh k #corner #line [337184.622,444469.976,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337184.622,444469.976,0.0]
        addKnot sh k #corner #line [337149.331,444491.290,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337156.667,444583.186,0.0]
        addKnot sh k #corner #line [337114.040,444512.604,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337114.040,444512.604,0.0]
        addKnot sh k #corner #line [337149.331,444491.290,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337149.331,444491.290,0.0]
        addKnot sh k #corner #line [337170.645,444526.581,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337170.645,444526.581,0.0]
        addKnot sh k #corner #line [337205.936,444505.267,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337227.250,444540.558,0.0]
        addKnot sh k #corner #line [337156.667,444583.186,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337156.667,444583.186,0.0]
        addKnot sh k #corner #line [337156.667,444583.186,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337205.936,444505.267,0.0]
        addKnot sh k #corner #line [337227.250,444540.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336851.838,443851.500,0.0]
        addKnot sh k #corner #line [336933.856,443987.303,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336756.842,443908.873,0.0]
        addKnot sh k #corner #line [336838.859,444044.676,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336723.052,443785.466,0.0]
        addKnot sh k #corner #line [336758.343,443764.152,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338003.656,444071.652,0.0]
        addKnot sh k #corner #line [338003.656,444071.652,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337933.074,444114.280,0.0]
        addKnot sh k #corner #line [338003.656,444071.652,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337911.760,444078.988,0.0]
        addKnot sh k #corner #line [337933.074,444114.280,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337947.051,444057.674,0.0]
        addKnot sh k #corner #line [337911.760,444078.988,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337925.737,444022.383,0.0]
        addKnot sh k #corner #line [337947.051,444057.674,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [337961.029,444001.069,0.0]
        addKnot sh k #corner #line [337925.737,444022.383,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [338003.656,444071.652,0.0]
        addKnot sh k #corner #line [337961.029,444001.069,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336756.842,443908.873,0.0]
        addKnot sh k #corner #line [336786.694,443890.844,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336838.859,444044.676,0.0]
        addKnot sh k #corner #line [336868.712,444026.647,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336821.985,443869.530,0.0]
        addKnot sh k #corner #line [336851.838,443851.500,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [336904.003,444005.333,0.0]
        addKnot sh k #corner #line [336933.856,443987.303,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334272.218,445342.659,0.0]
        addKnot sh k #corner #line [334510.135,445222.969,0.0]
        addKnot sh k #corner #line [334773.794,445185.359,0.0]
        addKnot sh k #corner #line [335035.688,445233.753,0.0]
        addKnot sh k #corner #line [335268.495,445363.102,0.0]
        addKnot sh k #corner #line [335447.928,445559.911,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334688.393,446055.681,0.0]
        addKnot sh k #corner #line [334237.694,445365.194,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334272.218,445342.659,0.0]
        addKnot sh k #corner #line [334722.918,446033.146,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334722.918,446033.146,0.0]
        addKnot sh k #corner #line [334688.393,446055.681,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334698.939,446147.264,0.0]
        addKnot sh k #corner #line [334653.869,446078.216,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334653.869,446078.216,0.0]
        addKnot sh k #corner #line [334688.393,446055.681,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334688.393,446055.681,0.0]
        addKnot sh k #corner #line [334710.928,446090.205,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334710.928,446090.205,0.0]
        addKnot sh k #corner #line [334745.452,446067.670,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334767.987,446102.194,0.0]
        addKnot sh k #corner #line [334698.939,446147.264,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334698.939,446147.264,0.0]
        addKnot sh k #corner #line [334698.939,446147.264,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334745.452,446067.670,0.0]
        addKnot sh k #corner #line [334767.987,446102.194,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334368.710,445426.685,0.0]
        addKnot sh k #corner #line [334455.427,445559.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334275.778,445487.345,0.0]
        addKnot sh k #corner #line [334362.494,445620.197,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334237.694,445365.194,0.0]
        addKnot sh k #corner #line [334272.218,445342.659,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335527.523,445606.425,0.0]
        addKnot sh k #corner #line [335527.523,445606.425,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335458.474,445651.495,0.0]
        addKnot sh k #corner #line [335527.523,445606.425,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335435.939,445616.971,0.0]
        addKnot sh k #corner #line [335458.474,445651.495,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335470.463,445594.436,0.0]
        addKnot sh k #corner #line [335435.939,445616.971,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335447.928,445559.911,0.0]
        addKnot sh k #corner #line [335470.463,445594.436,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335482.453,445537.377,0.0]
        addKnot sh k #corner #line [335447.928,445559.911,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [335527.523,445606.425,0.0]
        addKnot sh k #corner #line [335482.453,445537.377,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334275.778,445487.345,0.0]
        addKnot sh k #corner #line [334304.982,445468.282,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334362.494,445620.197,0.0]
        addKnot sh k #corner #line [334391.698,445601.134,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334339.506,445445.747,0.0]
        addKnot sh k #corner #line [334368.710,445426.685,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [334426.223,445578.599,0.0]
        addKnot sh k #corner #line [334455.427,445559.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331850.998,447001.314,0.0]
        addKnot sh k #corner #line [332084.600,446873.405,0.0]
        addKnot sh k #corner #line [332346.788,446826.630,0.0]
        addKnot sh k #corner #line [332610.209,446865.868,0.0]
        addKnot sh k #corner #line [332847.383,446987.025,0.0]
        addKnot sh k #corner #line [333033.565,447177.462,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332291.768,447699.399,0.0]
        addKnot sh k #corner #line [331817.280,447025.038,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331850.998,447001.314,0.0]
        addKnot sh k #corner #line [332325.486,447675.675,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332325.486,447675.675,0.0]
        addKnot sh k #corner #line [332291.768,447699.399,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332305.499,447790.560,0.0]
        addKnot sh k #corner #line [332258.050,447723.124,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332258.050,447723.124,0.0]
        addKnot sh k #corner #line [332291.768,447699.399,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332291.768,447699.399,0.0]
        addKnot sh k #corner #line [332315.493,447733.117,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332315.493,447733.117,0.0]
        addKnot sh k #corner #line [332349.211,447709.393,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332372.935,447743.111,0.0]
        addKnot sh k #corner #line [332305.499,447790.560,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332305.499,447790.560,0.0]
        addKnot sh k #corner #line [332305.499,447790.560,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332349.211,447709.393,0.0]
        addKnot sh k #corner #line [332372.935,447743.111,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331950.360,447081.926,0.0]
        addKnot sh k #corner #line [332041.653,447211.676,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331859.598,447145.787,0.0]
        addKnot sh k #corner #line [331950.892,447275.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331817.280,447025.038,0.0]
        addKnot sh k #corner #line [331850.998,447001.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333114.732,447221.174,0.0]
        addKnot sh k #corner #line [333114.732,447221.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333047.296,447268.623,0.0]
        addKnot sh k #corner #line [333114.732,447221.174,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333023.572,447234.905,0.0]
        addKnot sh k #corner #line [333047.296,447268.623,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333057.290,447211.180,0.0]
        addKnot sh k #corner #line [333023.572,447234.905,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333033.565,447177.462,0.0]
        addKnot sh k #corner #line [333057.290,447211.180,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333067.283,447153.738,0.0]
        addKnot sh k #corner #line [333033.565,447177.462,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [333114.732,447221.174,0.0]
        addKnot sh k #corner #line [333067.283,447153.738,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331859.598,447145.787,0.0]
        addKnot sh k #corner #line [331888.120,447125.719,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331950.892,447275.537,0.0]
        addKnot sh k #corner #line [331979.413,447255.468,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [331921.838,447101.995,0.0]
        addKnot sh k #corner #line [331950.360,447081.926,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [332013.131,447231.744,0.0]
        addKnot sh k #corner #line [332041.653,447211.676,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329484.056,448747.158,0.0]
        addKnot sh k #corner #line [329713.048,448611.169,0.0]
        addKnot sh k #corner #line [329973.443,448555.266,0.0]
        addKnot sh k #corner #line [330238.074,448585.280,0.0]
        addKnot sh k #corner #line [330479.334,448698.080,0.0]
        addKnot sh k #corner #line [330672.054,448881.899,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329948.937,449429.424,0.0]
        addKnot sh k #corner #line [329451.187,448772.045,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329484.056,448747.158,0.0]
        addKnot sh k #corner #line [329981.806,449404.537,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329981.806,449404.537,0.0]
        addKnot sh k #corner #line [329948.937,449429.424,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329965.843,449520.049,0.0]
        addKnot sh k #corner #line [329916.068,449454.311,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329916.068,449454.311,0.0]
        addKnot sh k #corner #line [329948.937,449429.424,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329948.937,449429.424,0.0]
        addKnot sh k #corner #line [329973.824,449462.293,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329973.824,449462.293,0.0]
        addKnot sh k #corner #line [330006.693,449437.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330031.581,449470.274,0.0]
        addKnot sh k #corner #line [329965.843,449520.049,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329965.843,449520.049,0.0]
        addKnot sh k #corner #line [329965.843,449520.049,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330006.693,449437.405,0.0]
        addKnot sh k #corner #line [330031.581,449470.274,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329586.173,448824.251,0.0]
        addKnot sh k #corner #line [329681.942,448950.733,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329497.697,448891.243,0.0]
        addKnot sh k #corner #line [329593.465,449017.724,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329451.187,448772.045,0.0]
        addKnot sh k #corner #line [329484.056,448747.158,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330754.698,448922.750,0.0]
        addKnot sh k #corner #line [330754.698,448922.750,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330688.960,448972.525,0.0]
        addKnot sh k #corner #line [330754.698,448922.750,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330664.072,448939.656,0.0]
        addKnot sh k #corner #line [330688.960,448972.525,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330696.941,448914.768,0.0]
        addKnot sh k #corner #line [330664.072,448939.656,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330672.054,448881.899,0.0]
        addKnot sh k #corner #line [330696.941,448914.768,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330704.923,448857.012,0.0]
        addKnot sh k #corner #line [330672.054,448881.899,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [330754.698,448922.750,0.0]
        addKnot sh k #corner #line [330704.923,448857.012,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329497.697,448891.243,0.0]
        addKnot sh k #corner #line [329525.500,448870.190,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329593.465,449017.724,0.0]
        addKnot sh k #corner #line [329621.269,448996.672,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329558.369,448845.303,0.0]
        addKnot sh k #corner #line [329586.173,448824.251,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [329654.138,448971.785,0.0]
        addKnot sh k #corner #line [329681.942,448950.733,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327183.431,450571.391,0.0]
        addKnot sh k #corner #line [327407.543,450427.501,0.0]
        addKnot sh k #corner #line [327665.830,450362.554,0.0]
        addKnot sh k #corner #line [327931.346,450383.324,0.0]
        addKnot sh k #corner #line [328176.392,450487.645,0.0]
        addKnot sh k #corner #line [328375.404,450664.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327671.815,451237.035,0.0]
        addKnot sh k #corner #line [327151.450,450597.409,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327183.431,450571.391,0.0]
        addKnot sh k #corner #line [327703.796,451211.017,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327703.796,451211.017,0.0]
        addKnot sh k #corner #line [327671.815,451237.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327691.870,451327.016,0.0]
        addKnot sh k #corner #line [327639.834,451263.053,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327639.834,451263.053,0.0]
        addKnot sh k #corner #line [327671.815,451237.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327671.815,451237.035,0.0]
        addKnot sh k #corner #line [327697.833,451269.017,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327697.833,451269.017,0.0]
        addKnot sh k #corner #line [327729.815,451242.998,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327755.833,451274.980,0.0]
        addKnot sh k #corner #line [327691.870,451327.016,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327691.870,451327.016,0.0]
        addKnot sh k #corner #line [327691.870,451327.016,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327729.815,451242.998,0.0]
        addKnot sh k #corner #line [327755.833,451274.980,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327288.173,450644.877,0.0]
        addKnot sh k #corner #line [327388.293,450767.943,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327202.086,450714.913,0.0]
        addKnot sh k #corner #line [327302.206,450837.979,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327151.450,450597.409,0.0]
        addKnot sh k #corner #line [327183.431,450571.391,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328459.421,450702.578,0.0]
        addKnot sh k #corner #line [328459.421,450702.578,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328395.459,450754.614,0.0]
        addKnot sh k #corner #line [328459.421,450702.578,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328369.440,450722.633,0.0]
        addKnot sh k #corner #line [328395.459,450754.614,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328401.422,450696.615,0.0]
        addKnot sh k #corner #line [328369.440,450722.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328375.404,450664.633,0.0]
        addKnot sh k #corner #line [328401.422,450696.615,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328407.385,450638.615,0.0]
        addKnot sh k #corner #line [328375.404,450664.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [328459.421,450702.578,0.0]
        addKnot sh k #corner #line [328407.385,450638.615,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327202.086,450714.913,0.0]
        addKnot sh k #corner #line [327229.139,450692.904,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327302.206,450837.979,0.0]
        addKnot sh k #corner #line [327329.259,450815.970,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327261.120,450666.886,0.0]
        addKnot sh k #corner #line [327288.173,450644.877,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327361.240,450789.952,0.0]
        addKnot sh k #corner #line [327388.293,450767.943,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313336.660,442342.938,0.0]
        addKnot sh k #corner #line [313518.660,442239.951,0.0]
        addKnot sh k #corner #line [313722.959,442195.321,0.0]
        addKnot sh k #corner #line [313931.325,442213.029,0.0]
        addKnot sh k #corner #line [314125.163,442291.496,0.0]
        addKnot sh k #corner #line [314287.173,442423.719,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314287.173,442423.719,0.0]
        addKnot sh k #corner #line [314171.449,442249.541,0.0]
        addKnot sh k #corner #line [314112.340,442048.951,0.0]
        addKnot sh k #corner #line [314115.120,441839.852,0.0]
        addKnot sh k #corner #line [314179.541,441640.905,0.0]
        addKnot sh k #corner #line [314299.854,441469.864,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314355.357,441568.321,0.0]
        addKnot sh k #corner #line [314518.194,441747.966,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314429.449,441501.162,0.0]
        addKnot sh k #corner #line [314592.286,441680.807,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314298.653,441468.540,0.0]
        addKnot sh k #corner #line [314768.770,441987.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314842.862,441920.023,0.0]
        addKnot sh k #corner #line [314768.770,441987.182,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314842.862,441920.023,0.0]
        addKnot sh k #corner #line [314910.021,441994.115,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314335.699,441434.960,0.0]
        addKnot sh k #corner #line [314872.975,442027.694,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314910.021,441994.115,0.0]
        addKnot sh k #corner #line [314872.975,442027.694,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313355.118,442474.975,0.0]
        addKnot sh k #corner #line [313517.954,442654.620,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313429.209,442407.815,0.0]
        addKnot sh k #corner #line [313592.046,442587.460,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313298.414,442375.193,0.0]
        addKnot sh k #corner #line [313835.690,442967.928,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313731.484,442927.416,0.0]
        addKnot sh k #corner #line [313798.644,443001.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313731.484,442927.416,0.0]
        addKnot sh k #corner #line [313805.576,442860.256,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313798.644,443001.507,0.0]
        addKnot sh k #corner #line [313835.690,442967.928,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313335.459,442341.613,0.0]
        addKnot sh k #corner #line [313805.576,442860.256,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313298.414,442375.193,0.0]
        addKnot sh k #corner #line [313335.459,442341.613,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314335.699,441434.960,0.0]
        addKnot sh k #corner #line [314298.653,441468.540,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314429.449,441501.162,0.0]
        addKnot sh k #corner #line [314410.926,441517.952,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314355.357,441568.321,0.0]
        addKnot sh k #corner #line [314373.880,441551.532,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314592.286,441680.807,0.0]
        addKnot sh k #corner #line [314573.763,441697.597,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314518.194,441747.966,0.0]
        addKnot sh k #corner #line [314536.717,441731.176,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313429.209,442407.815,0.0]
        addKnot sh k #corner #line [313410.686,442424.605,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313355.118,442474.975,0.0]
        addKnot sh k #corner #line [313373.641,442458.185,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313592.046,442587.460,0.0]
        addKnot sh k #corner #line [313573.523,442604.250,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313517.954,442654.620,0.0]
        addKnot sh k #corner #line [313536.477,442637.830,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308420.968,447182.180,0.0]
        addKnot sh k #corner #line [308315.142,447362.543,0.0]
        addKnot sh k #corner #line [308267.315,447566.118,0.0]
        addKnot sh k #corner #line [308281.755,447774.736,0.0]
        addKnot sh k #corner #line [308357.174,447969.780,0.0]
        addKnot sh k #corner #line [308486.842,448133.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308486.842,448133.842,0.0]
        addKnot sh k #corner #line [308314.498,448015.403,0.0]
        addKnot sh k #corner #line [308114.860,447953.157,0.0]
        addKnot sh k #corner #line [307905.743,447952.659,0.0]
        addKnot sh k #corner #line [307705.811,448013.954,0.0]
        addKnot sh k #corner #line [307532.905,448131.572,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307630.481,448188.611,0.0]
        addKnot sh k #corner #line [307807.551,448354.244,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307562.168,448261.642,0.0]
        addKnot sh k #corner #line [307739.239,448427.274,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307531.600,448130.350,0.0]
        addKnot sh k #corner #line [308042.810,448608.538,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307974.498,448681.568,0.0]
        addKnot sh k #corner #line [308042.810,448608.538,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307974.498,448681.568,0.0]
        addKnot sh k #corner #line [308047.528,448749.881,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307497.443,448166.866,0.0]
        addKnot sh k #corner #line [308081.684,448713.366,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308047.528,448749.881,0.0]
        addKnot sh k #corner #line [308081.684,448713.366,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308552.700,447202.705,0.0]
        addKnot sh k #corner #line [308729.770,447368.337,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308484.387,447275.735,0.0]
        addKnot sh k #corner #line [308661.458,447441.367,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308453.819,447144.444,0.0]
        addKnot sh k #corner #line [309038.060,447690.944,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308999.186,447586.116,0.0]
        addKnot sh k #corner #line [309072.216,447654.429,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308999.186,447586.116,0.0]
        addKnot sh k #corner #line [308930.873,447659.146,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309072.216,447654.429,0.0]
        addKnot sh k #corner #line [309038.060,447690.944,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308419.662,447180.959,0.0]
        addKnot sh k #corner #line [308930.873,447659.146,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308453.819,447144.444,0.0]
        addKnot sh k #corner #line [308419.662,447180.959,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307497.443,448166.866,0.0]
        addKnot sh k #corner #line [307531.600,448130.350,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307562.168,448261.642,0.0]
        addKnot sh k #corner #line [307579.246,448243.384,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307630.481,448188.611,0.0]
        addKnot sh k #corner #line [307613.402,448206.869,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307739.239,448427.274,0.0]
        addKnot sh k #corner #line [307756.317,448409.016,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307807.551,448354.244,0.0]
        addKnot sh k #corner #line [307790.473,448372.501,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308484.387,447275.735,0.0]
        addKnot sh k #corner #line [308501.465,447257.477,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308552.700,447202.705,0.0]
        addKnot sh k #corner #line [308535.621,447220.962,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308661.458,447441.367,0.0]
        addKnot sh k #corner #line [308678.536,447423.110,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [308729.770,447368.337,0.0]
        addKnot sh k #corner #line [308712.692,447386.595,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306044.887,449779.856,0.0]
        addKnot sh k #corner #line [306215.124,449658.410,0.0]
        addKnot sh k #corner #line [306413.639,449592.668,0.0]
        addKnot sh k #corner #line [306622.715,449588.499,0.0]
        addKnot sh k #corner #line [306823.693,449646.275,0.0]
        addKnot sh k #corner #line [306998.636,449760.839,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306998.636,449760.839,0.0]
        addKnot sh k #corner #line [306865.340,449599.711,0.0]
        addKnot sh k #corner #line [306785.587,449406.399,0.0]
        addKnot sh k #corner #line [306766.495,449198.155,0.0]
        addKnot sh k #corner #line [306809.767,448993.563,0.0]
        addKnot sh k #corner #line [306911.542,448810.884,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306977.033,448903.000,0.0]
        addKnot sh k #corner #line [307157.756,449064.639,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307043.699,448828.463,0.0]
        addKnot sh k #corner #line [307224.422,448990.103,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306910.210,448809.692,0.0]
        addKnot sh k #corner #line [307431.964,449276.352,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307498.630,449201.816,0.0]
        addKnot sh k #corner #line [307431.964,449276.352,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307498.630,449201.816,0.0]
        addKnot sh k #corner #line [307573.166,449268.482,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306943.542,448772.424,0.0]
        addKnot sh k #corner #line [307539.833,449305.750,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307573.166,449268.482,0.0]
        addKnot sh k #corner #line [307539.833,449305.750,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306077.045,449909.241,0.0]
        addKnot sh k #corner #line [306257.767,450070.880,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306143.710,449834.704,0.0]
        addKnot sh k #corner #line [306324.433,449996.344,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306010.221,449815.933,0.0]
        addKnot sh k #corner #line [306606.512,450349.259,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306498.643,450319.861,0.0]
        addKnot sh k #corner #line [306573.179,450386.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306498.643,450319.861,0.0]
        addKnot sh k #corner #line [306565.308,450245.325,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306573.179,450386.527,0.0]
        addKnot sh k #corner #line [306606.512,450349.259,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306043.554,449778.664,0.0]
        addKnot sh k #corner #line [306565.308,450245.325,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306010.221,449815.933,0.0]
        addKnot sh k #corner #line [306043.554,449778.664,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306943.542,448772.424,0.0]
        addKnot sh k #corner #line [306910.210,448809.692,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307043.699,448828.463,0.0]
        addKnot sh k #corner #line [307027.032,448847.098,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306977.033,448903.000,0.0]
        addKnot sh k #corner #line [306993.700,448884.366,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307224.422,448990.103,0.0]
        addKnot sh k #corner #line [307207.755,449008.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307157.756,449064.639,0.0]
        addKnot sh k #corner #line [307174.422,449046.005,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306143.710,449834.704,0.0]
        addKnot sh k #corner #line [306127.044,449853.338,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306077.045,449909.241,0.0]
        addKnot sh k #corner #line [306093.711,449890.607,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306324.433,449996.344,0.0]
        addKnot sh k #corner #line [306307.767,450014.978,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306257.767,450070.880,0.0]
        addKnot sh k #corner #line [306274.434,450052.246,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301661.952,455106.438,0.0]
        addKnot sh k #corner #line [301575.559,455296.875,0.0]
        addKnot sh k #corner #line [301549.273,455504.334,0.0]
        addKnot sh k #corner #line [301585.441,455710.300,0.0]
        addKnot sh k #corner #line [301680.835,455896.391,0.0]
        addKnot sh k #corner #line [301826.942,456046.001,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301826.942,456046.001,0.0]
        addKnot sh k #corner #line [301643.162,455946.225,0.0]
        addKnot sh k #corner #line [301438.111,455905.188,0.0]
        addKnot sh k #corner #line [301230.087,455926.552,0.0]
        addKnot sh k #corner #line [301037.657,456008.410,0.0]
        addKnot sh k #corner #line [300877.994,456143.457,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300980.997,456189.985,0.0]
        addKnot sh k #corner #line [301174.411,456336.201,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300920.692,456269.756,0.0]
        addKnot sh k #corner #line [301114.106,456415.971,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300876.567,456142.379,0.0]
        addKnot sh k #corner #line [301434.962,456564.510,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301374.658,456644.281,0.0]
        addKnot sh k #corner #line [301434.962,456564.510,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301374.658,456644.281,0.0]
        addKnot sh k #corner #line [301454.429,456704.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300846.415,456182.264,0.0]
        addKnot sh k #corner #line [301484.581,456664.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301454.429,456704.586,0.0]
        addKnot sh k #corner #line [301484.581,456664.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301795.107,455113.080,0.0]
        addKnot sh k #corner #line [301988.521,455259.296,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301734.803,455192.851,0.0]
        addKnot sh k #corner #line [301928.217,455339.067,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301690.678,455065.474,0.0]
        addKnot sh k #corner #line [302328.844,455547.910,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302279.225,455447.721,0.0]
        addKnot sh k #corner #line [302358.996,455508.025,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302279.225,455447.721,0.0]
        addKnot sh k #corner #line [302218.921,455527.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302358.996,455508.025,0.0]
        addKnot sh k #corner #line [302328.844,455547.910,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301660.526,455105.360,0.0]
        addKnot sh k #corner #line [302218.921,455527.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301690.678,455065.474,0.0]
        addKnot sh k #corner #line [301660.526,455105.360,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300846.415,456182.264,0.0]
        addKnot sh k #corner #line [300876.567,456142.379,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300920.692,456269.756,0.0]
        addKnot sh k #corner #line [300935.768,456249.813,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300980.997,456189.985,0.0]
        addKnot sh k #corner #line [300965.920,456209.927,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301114.106,456415.971,0.0]
        addKnot sh k #corner #line [301129.182,456396.029,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301174.411,456336.201,0.0]
        addKnot sh k #corner #line [301159.335,456356.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301734.803,455192.851,0.0]
        addKnot sh k #corner #line [301749.879,455172.908,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301795.107,455113.080,0.0]
        addKnot sh k #corner #line [301780.031,455133.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301928.217,455339.067,0.0]
        addKnot sh k #corner #line [301943.293,455319.124,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301988.521,455259.296,0.0]
        addKnot sh k #corner #line [301973.445,455279.239,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299570.489,457938.157,0.0]
        addKnot sh k #corner #line [299727.099,457799.581,0.0]
        addKnot sh k #corner #line [299917.655,457713.450,0.0]
        addKnot sh k #corner #line [300125.150,457687.449,0.0]
        addKnot sh k #corner #line [300331.066,457723.901,0.0]
        addKnot sh k #corner #line [300517.026,457819.550,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300517.026,457819.550,0.0]
        addKnot sh k #corner #line [300367.617,457673.238,0.0]
        addKnot sh k #corner #line [300268.095,457489.322,0.0]
        addKnot sh k #corner #line [300227.340,457284.214,0.0]
        addKnot sh k #corner #line [300248.990,457076.220,0.0]
        addKnot sh k #corner #line [300331.112,456883.903,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300405.873,456968.669,0.0]
        addKnot sh k #corner #line [300602.501,457110.532,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300464.382,456887.572,0.0]
        addKnot sh k #corner #line [300661.011,457029.436,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300329.662,456882.857,0.0]
        addKnot sh k #corner #line [300897.338,457292.423,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300955.847,457211.327,0.0]
        addKnot sh k #corner #line [300897.338,457292.423,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300955.847,457211.327,0.0]
        addKnot sh k #corner #line [301036.944,457269.836,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300358.917,456842.309,0.0]
        addKnot sh k #corner #line [301007.689,457310.384,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301036.944,457269.836,0.0]
        addKnot sh k #corner #line [301007.689,457310.384,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299615.995,458063.472,0.0]
        addKnot sh k #corner #line [299812.624,458205.335,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299674.505,457982.375,0.0]
        addKnot sh k #corner #line [299871.133,458124.239,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299539.784,457977.660,0.0]
        addKnot sh k #corner #line [300188.556,458445.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300078.205,458427.774,0.0]
        addKnot sh k #corner #line [300159.301,458486.284,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300078.205,458427.774,0.0]
        addKnot sh k #corner #line [300136.714,458346.678,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300159.301,458486.284,0.0]
        addKnot sh k #corner #line [300188.556,458445.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299569.039,457937.111,0.0]
        addKnot sh k #corner #line [300136.714,458346.678,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299539.784,457977.660,0.0]
        addKnot sh k #corner #line [299569.039,457937.111,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300358.917,456842.309,0.0]
        addKnot sh k #corner #line [300329.662,456882.857,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300464.382,456887.572,0.0]
        addKnot sh k #corner #line [300449.755,456907.846,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300405.873,456968.669,0.0]
        addKnot sh k #corner #line [300420.500,456948.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300661.011,457029.436,0.0]
        addKnot sh k #corner #line [300646.384,457049.710,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300602.501,457110.532,0.0]
        addKnot sh k #corner #line [300617.129,457090.258,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299674.505,457982.375,0.0]
        addKnot sh k #corner #line [299659.877,458002.649,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299615.995,458063.472,0.0]
        addKnot sh k #corner #line [299630.622,458043.197,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299871.133,458124.239,0.0]
        addKnot sh k #corner #line [299856.506,458144.513,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299812.624,458205.335,0.0]
        addKnot sh k #corner #line [299827.251,458185.061,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321040.375,435948.262,0.0]
        addKnot sh k #corner #line [321232.140,435864.856,0.0]
        addKnot sh k #corner #line [321439.984,435841.817,0.0]
        addKnot sh k #corner #line [321645.359,435881.202,0.0]
        addKnot sh k #corner #line [321829.937,435979.494,0.0]
        addKnot sh k #corner #line [321977.243,436127.921,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321977.243,436127.921,0.0]
        addKnot sh k #corner #line [321880.354,435942.604,0.0]
        addKnot sh k #corner #line [321842.528,435736.936,0.0]
        addKnot sh k #corner #line [321867.141,435529.272,0.0]
        addKnot sh k #corner #line [321951.998,435338.146,0.0]
        addKnot sh k #corner #line [322089.525,435180.613,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322134.436,435284.331,0.0]
        addKnot sh k #corner #line [322277.610,435480.008,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322215.140,435225.281,0.0]
        addKnot sh k #corner #line [322358.314,435420.958,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322088.469,435179.170,0.0]
        addKnot sh k #corner #line [322501.818,435744.097,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322582.522,435685.047,0.0]
        addKnot sh k #corner #line [322501.818,435744.097,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322582.522,435685.047,0.0]
        addKnot sh k #corner #line [322641.572,435765.751,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322128.821,435149.645,0.0]
        addKnot sh k #corner #line [322601.220,435795.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322641.572,435765.751,0.0]
        addKnot sh k #corner #line [322601.220,435795.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321044.934,436081.504,0.0]
        addKnot sh k #corner #line [321188.108,436277.181,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321125.638,436022.454,0.0]
        addKnot sh k #corner #line [321268.812,436218.131,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320998.967,435976.344,0.0]
        addKnot sh k #corner #line [321471.366,436621.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321371.964,436570.795,0.0]
        addKnot sh k #corner #line [321431.014,436651.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321371.964,436570.795,0.0]
        addKnot sh k #corner #line [321452.668,436511.746,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321431.014,436651.499,0.0]
        addKnot sh k #corner #line [321471.366,436621.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321039.319,435946.819,0.0]
        addKnot sh k #corner #line [321452.668,436511.746,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320998.967,435976.344,0.0]
        addKnot sh k #corner #line [321039.319,435946.819,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322128.821,435149.645,0.0]
        addKnot sh k #corner #line [322088.469,435179.170,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322215.140,435225.281,0.0]
        addKnot sh k #corner #line [322194.964,435240.044,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322134.436,435284.331,0.0]
        addKnot sh k #corner #line [322154.612,435269.569,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322358.314,435420.958,0.0]
        addKnot sh k #corner #line [322338.138,435435.720,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322277.610,435480.008,0.0]
        addKnot sh k #corner #line [322297.786,435465.245,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321125.638,436022.454,0.0]
        addKnot sh k #corner #line [321105.462,436037.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321044.934,436081.504,0.0]
        addKnot sh k #corner #line [321065.110,436066.742,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321268.812,436218.131,0.0]
        addKnot sh k #corner #line [321248.636,436232.894,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321188.108,436277.181,0.0]
        addKnot sh k #corner #line [321208.284,436262.418,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286756.199,471372.917,0.0]
        addKnot sh k #corner #line [286802.921,471169.086,0.0]
        addKnot sh k #corner #line [286787.349,470960.550,0.0]
        addKnot sh k #corner #line [286710.873,470765.918,0.0]
        addKnot sh k #corner #line [286580.318,470602.561,0.0]
        addKnot sh k #corner #line [286407.334,470485.058,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286407.334,470485.058,0.0]
        addKnot sh k #corner #line [286607.308,470546.221,0.0]
        addKnot sh k #corner #line [286816.424,470545.584,0.0]
        addKnot sh k #corner #line [287016.021,470483.206,0.0]
        addKnot sh k #corner #line [287188.286,470364.652,0.0]
        addKnot sh k #corner #line [287317.845,470200.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287207.637,470175.429,0.0]
        addKnot sh k #corner #line [286988.971,470070.677,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287250.841,470085.244,0.0]
        addKnot sh k #corner #line [287032.174,469980.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287319.457,470201.276,0.0]
        addKnot sh k #corner #line [286688.157,469898.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286731.361,469808.666,0.0]
        addKnot sh k #corner #line [286688.157,469898.852,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286731.361,469808.666,0.0]
        addKnot sh k #corner #line [286641.175,469765.462,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287341.059,470156.183,0.0]
        addKnot sh k #corner #line [286619.574,469810.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286641.175,469765.462,0.0]
        addKnot sh k #corner #line [286619.574,469810.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286624.389,471392.936,0.0]
        addKnot sh k #corner #line [286405.723,471288.183,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286667.593,471302.750,0.0]
        addKnot sh k #corner #line [286448.926,471197.998,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286736.209,471418.783,0.0]
        addKnot sh k #corner #line [286014.724,471073.154,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286083.308,471161.451,0.0]
        addKnot sh k #corner #line [285993.122,471118.247,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286083.308,471161.451,0.0]
        addKnot sh k #corner #line [286126.511,471071.265,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285993.122,471118.247,0.0]
        addKnot sh k #corner #line [286014.724,471073.154,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286757.811,471373.690,0.0]
        addKnot sh k #corner #line [286126.511,471071.265,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286736.209,471418.783,0.0]
        addKnot sh k #corner #line [286757.811,471373.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287341.059,470156.183,0.0]
        addKnot sh k #corner #line [287319.457,470201.276,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287250.841,470085.244,0.0]
        addKnot sh k #corner #line [287240.040,470107.790,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287207.637,470175.429,0.0]
        addKnot sh k #corner #line [287218.438,470152.883,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287032.174,469980.491,0.0]
        addKnot sh k #corner #line [287021.373,470003.038,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286988.971,470070.677,0.0]
        addKnot sh k #corner #line [286999.772,470048.131,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286667.593,471302.750,0.0]
        addKnot sh k #corner #line [286656.792,471325.297,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286624.389,471392.936,0.0]
        addKnot sh k #corner #line [286635.190,471370.389,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286448.926,471197.998,0.0]
        addKnot sh k #corner #line [286438.126,471220.544,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [286405.723,471288.183,0.0]
        addKnot sh k #corner #line [286416.524,471265.637,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291767.590,462014.653,0.0]
        addKnot sh k #corner #line [291834.888,461816.660,0.0]
        addKnot sh k #corner #line [291840.698,461607.623,0.0]
        addKnot sh k #corner #line [291784.502,461406.198,0.0]
        addKnot sh k #corner #line [291671.315,461230.360,0.0]
        addKnot sh k #corner #line [291511.238,461095.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291511.238,461095.803,0.0]
        addKnot sh k #corner #line [291703.918,461177.072,0.0]
        addKnot sh k #corner #line [291912.006,461197.798,0.0]
        addKnot sh k #corner #line [292116.931,461156.133,0.0]
        addKnot sh k #corner #line [292300.404,461055.795,0.0]
        addKnot sh k #corner #line [292446.051,460905.738,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292338.981,460869.538,0.0]
        addKnot sh k #corner #line [292132.158,460742.999,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292391.171,460784.237,0.0]
        addKnot sh k #corner #line [292184.347,460657.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292447.576,460906.671,0.0]
        addKnot sh k #corner #line [291850.469,460541.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291902.658,460456.045,0.0]
        addKnot sh k #corner #line [291850.469,460541.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291902.658,460456.045,0.0]
        addKnot sh k #corner #line [291817.357,460403.856,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292473.671,460864.021,0.0]
        addKnot sh k #corner #line [291791.262,460446.506,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291817.357,460403.856,0.0]
        addKnot sh k #corner #line [291791.262,460446.506,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291634.426,462021.103,0.0]
        addKnot sh k #corner #line [291427.603,461894.564,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291686.615,461935.802,0.0]
        addKnot sh k #corner #line [291479.792,461809.262,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291743.021,462058.236,0.0]
        addKnot sh k #corner #line [291060.612,461640.722,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291119.819,461735.562,0.0]
        addKnot sh k #corner #line [291034.518,461683.372,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291119.819,461735.562,0.0]
        addKnot sh k #corner #line [291172.008,461650.261,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291034.518,461683.372,0.0]
        addKnot sh k #corner #line [291060.612,461640.722,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291769.116,462015.586,0.0]
        addKnot sh k #corner #line [291172.008,461650.261,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291743.021,462058.236,0.0]
        addKnot sh k #corner #line [291769.116,462015.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292473.671,460864.021,0.0]
        addKnot sh k #corner #line [292447.576,460906.671,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292391.171,460784.237,0.0]
        addKnot sh k #corner #line [292378.123,460805.562,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292338.981,460869.538,0.0]
        addKnot sh k #corner #line [292352.029,460848.213,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292184.347,460657.698,0.0]
        addKnot sh k #corner #line [292171.300,460679.023,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292132.158,460742.999,0.0]
        addKnot sh k #corner #line [292145.205,460721.673,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291686.615,461935.802,0.0]
        addKnot sh k #corner #line [291673.568,461957.127,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291634.426,462021.103,0.0]
        addKnot sh k #corner #line [291647.473,461999.778,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291479.792,461809.262,0.0]
        addKnot sh k #corner #line [291466.745,461830.588,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291427.603,461894.564,0.0]
        addKnot sh k #corner #line [291440.650,461873.238,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327396.889,455262.181,0.0]
        addKnot sh k #corner #line [327576.655,455065.675,0.0]
        addKnot sh k #corner #line [327684.406,454822.118,0.0]
        addKnot sh k #corner #line [327708.902,454556.919,0.0]
        addKnot sh k #corner #line [327647.587,454297.746,0.0]
        addKnot sh k #corner #line [327506.859,454071.635,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326823.570,454668.123,0.0]
        addKnot sh k #corner #line [327365.831,455289.294,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327396.889,455262.181,0.0]
        addKnot sh k #corner #line [326854.628,454641.010,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326854.628,454641.010,0.0]
        addKnot sh k #corner #line [326823.570,454668.123,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326738.285,454633.118,0.0]
        addKnot sh k #corner #line [326792.511,454695.236,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326792.511,454695.236,0.0]
        addKnot sh k #corner #line [326823.570,454668.123,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326823.570,454668.123,0.0]
        addKnot sh k #corner #line [326796.457,454637.064,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326796.457,454637.064,0.0]
        addKnot sh k #corner #line [326827.515,454609.951,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326800.402,454578.892,0.0]
        addKnot sh k #corner #line [326738.285,454633.118,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326738.285,454633.118,0.0]
        addKnot sh k #corner #line [326738.285,454633.118,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326827.515,454609.951,0.0]
        addKnot sh k #corner #line [326800.402,454578.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327342.203,455146.507,0.0]
        addKnot sh k #corner #line [327237.871,455026.991,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327258.600,455219.490,0.0]
        addKnot sh k #corner #line [327154.267,455099.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327365.831,455289.294,0.0]
        addKnot sh k #corner #line [327396.889,455262.181,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327483.691,453982.405,0.0]
        addKnot sh k #corner #line [327483.691,453982.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327421.574,454036.631,0.0]
        addKnot sh k #corner #line [327483.691,453982.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327448.687,454067.690,0.0]
        addKnot sh k #corner #line [327421.574,454036.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327479.746,454040.577,0.0]
        addKnot sh k #corner #line [327448.687,454067.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327506.859,454071.635,0.0]
        addKnot sh k #corner #line [327479.746,454040.577,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327537.917,454044.522,0.0]
        addKnot sh k #corner #line [327506.859,454071.635,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327483.691,453982.405,0.0]
        addKnot sh k #corner #line [327537.917,454044.522,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327258.600,455219.490,0.0]
        addKnot sh k #corner #line [327284.873,455196.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327154.267,455099.974,0.0]
        addKnot sh k #corner #line [327180.540,455077.039,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327315.931,455169.442,0.0]
        addKnot sh k #corner #line [327342.203,455146.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327211.598,455049.926,0.0]
        addKnot sh k #corner #line [327237.871,455026.991,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326855.446,450842.296,0.0]
        addKnot sh k #corner #line [326671.812,451035.192,0.0]
        addKnot sh k #corner #line [326559.243,451276.560,0.0]
        addKnot sh k #corner #line [326529.482,451541.219,0.0]
        addKnot sh k #corner #line [326585.635,451801.560,0.0]
        addKnot sh k #corner #line [326721.843,452030.422,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327416.849,451447.629,0.0]
        addKnot sh k #corner #line [326887.038,450815.805,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326855.446,450842.296,0.0]
        addKnot sh k #corner #line [327385.258,451474.119,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327385.258,451474.119,0.0]
        addKnot sh k #corner #line [327416.849,451447.629,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327501.421,451484.321,0.0]
        addKnot sh k #corner #line [327448.440,451421.138,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327448.440,451421.138,0.0]
        addKnot sh k #corner #line [327416.849,451447.629,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327416.849,451447.629,0.0]
        addKnot sh k #corner #line [327443.340,451479.220,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327443.340,451479.220,0.0]
        addKnot sh k #corner #line [327411.748,451505.711,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327438.239,451537.302,0.0]
        addKnot sh k #corner #line [327501.421,451484.321,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327501.421,451484.321,0.0]
        addKnot sh k #corner #line [327501.421,451484.321,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327411.748,451505.711,0.0]
        addKnot sh k #corner #line [327438.239,451537.302,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326907.823,450959.034,0.0]
        addKnot sh k #corner #line [327009.761,451080.599,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326992.860,450887.727,0.0]
        addKnot sh k #corner #line [327094.798,451009.292,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326887.038,450815.805,0.0]
        addKnot sh k #corner #line [326855.446,450842.296,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326743.233,452120.095,0.0]
        addKnot sh k #corner #line [326743.233,452120.095,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326806.415,452067.113,0.0]
        addKnot sh k #corner #line [326743.233,452120.095,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326779.925,452035.522,0.0]
        addKnot sh k #corner #line [326806.415,452067.113,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326748.333,452062.013,0.0]
        addKnot sh k #corner #line [326779.925,452035.522,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326721.843,452030.422,0.0]
        addKnot sh k #corner #line [326748.333,452062.013,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326690.252,452056.912,0.0]
        addKnot sh k #corner #line [326721.843,452030.422,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326743.233,452120.095,0.0]
        addKnot sh k #corner #line [326690.252,452056.912,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326992.860,450887.727,0.0]
        addKnot sh k #corner #line [326966.137,450910.135,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327094.798,451009.292,0.0]
        addKnot sh k #corner #line [327068.075,451031.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326934.546,450936.626,0.0]
        addKnot sh k #corner #line [326907.823,450959.034,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [327036.484,451058.191,0.0]
        addKnot sh k #corner #line [327009.761,451080.599,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312266.091,462821.608,0.0]
        addKnot sh k #corner #line [312106.052,462956.210,0.0]
        addKnot sh k #corner #line [311913.395,463037.532,0.0]
        addKnot sh k #corner #line [311705.313,463058.317,0.0]
        addKnot sh k #corner #line [311500.377,463016.710,0.0]
        addKnot sh k #corner #line [311316.876,462916.424,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311316.876,462916.424,0.0]
        addKnot sh k #corner #line [311462.565,463066.439,0.0]
        addKnot sh k #corner #line [311557.441,463252.795,0.0]
        addKnot sh k #corner #line [311593.036,463458.861,0.0]
        addKnot sh k #corner #line [311566.173,463666.246,0.0]
        addKnot sh k #corner #line [311479.251,463856.442,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311406.640,463769.827,0.0]
        addKnot sh k #corner #line [311213.634,463623.073,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311346.114,463849.429,0.0]
        addKnot sh k #corner #line [311153.108,463702.676,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311480.674,463857.524,0.0]
        addKnot sh k #corner #line [310923.455,463433.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310862.929,463513.444,0.0]
        addKnot sh k #corner #line [310923.455,463433.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310862.929,463513.444,0.0]
        addKnot sh k #corner #line [310783.326,463452.917,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311450.411,463897.325,0.0]
        addKnot sh k #corner #line [310813.590,463413.116,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310783.326,463452.917,0.0]
        addKnot sh k #corner #line [310813.590,463413.116,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312223.744,462695.191,0.0]
        addKnot sh k #corner #line [312030.737,462548.438,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312163.218,462774.794,0.0]
        addKnot sh k #corner #line [311970.211,462628.040,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312297.777,462782.888,0.0]
        addKnot sh k #corner #line [311660.956,462298.679,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311770.822,462319.404,0.0]
        addKnot sh k #corner #line [311691.219,462258.878,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311770.822,462319.404,0.0]
        addKnot sh k #corner #line [311710.296,462399.007,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311691.219,462258.878,0.0]
        addKnot sh k #corner #line [311660.956,462298.679,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312267.514,462822.690,0.0]
        addKnot sh k #corner #line [311710.296,462399.007,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312297.777,462782.888,0.0]
        addKnot sh k #corner #line [312267.514,462822.690,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311450.411,463897.325,0.0]
        addKnot sh k #corner #line [311480.674,463857.524,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311346.114,463849.429,0.0]
        addKnot sh k #corner #line [311361.246,463829.529,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311406.640,463769.827,0.0]
        addKnot sh k #corner #line [311391.509,463789.727,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311153.108,463702.676,0.0]
        addKnot sh k #corner #line [311168.239,463682.775,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311213.634,463623.073,0.0]
        addKnot sh k #corner #line [311198.502,463642.974,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312163.218,462774.794,0.0]
        addKnot sh k #corner #line [312178.349,462754.893,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312223.744,462695.191,0.0]
        addKnot sh k #corner #line [312208.612,462715.092,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311970.211,462628.040,0.0]
        addKnot sh k #corner #line [311985.343,462608.140,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312030.737,462548.438,0.0]
        addKnot sh k #corner #line [312015.606,462568.338,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317260.989,456708.408,0.0]
        addKnot sh k #corner #line [317380.542,456879.981,0.0]
        addKnot sh k #corner #line [317444.080,457079.212,0.0]
        addKnot sh k #corner #line [317445.933,457288.321,0.0]
        addKnot sh k #corner #line [317385.935,457488.646,0.0]
        addKnot sh k #corner #line [317269.440,457662.310,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317269.440,457662.310,0.0]
        addKnot sh k #corner #line [317432.035,457530.807,0.0]
        addKnot sh k #corner #line [317626.218,457453.200,0.0]
        addKnot sh k #corner #line [317834.661,457436.416,0.0]
        addKnot sh k #corner #line [318038.760,457481.952,0.0]
        addKnot sh k #corner #line [318220.302,457585.745,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318127.466,457650.211,0.0]
        addKnot sh k #corner #line [317963.834,457829.132,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318201.259,457717.698,0.0]
        addKnot sh k #corner #line [318037.627,457896.620,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318221.508,457584.425,0.0]
        addKnot sh k #corner #line [317749.096,458100.978,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317822.890,458168.466,0.0]
        addKnot sh k #corner #line [317749.096,458100.978,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317822.890,458168.466,0.0]
        addKnot sh k #corner #line [317755.402,458242.259,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318258.405,457618.169,0.0]
        addKnot sh k #corner #line [317718.505,458208.515,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317755.402,458242.259,0.0]
        addKnot sh k #corner #line [317718.505,458208.515,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317131.256,456739.131,0.0]
        addKnot sh k #corner #line [316967.625,456918.052,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317205.050,456806.618,0.0]
        addKnot sh k #corner #line [317041.418,456985.539,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317225.299,456673.345,0.0]
        addKnot sh k #corner #line [316685.400,457263.691,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316715.990,457156.154,0.0]
        addKnot sh k #corner #line [316648.503,457229.948,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316715.990,457156.154,0.0]
        addKnot sh k #corner #line [316789.784,457223.642,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316648.503,457229.948,0.0]
        addKnot sh k #corner #line [316685.400,457263.691,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317262.196,456707.089,0.0]
        addKnot sh k #corner #line [316789.784,457223.642,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317225.299,456673.345,0.0]
        addKnot sh k #corner #line [317262.196,456707.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318258.405,457618.169,0.0]
        addKnot sh k #corner #line [318221.508,457584.425,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318201.259,457717.698,0.0]
        addKnot sh k #corner #line [318182.811,457700.827,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318127.466,457650.211,0.0]
        addKnot sh k #corner #line [318145.914,457667.083,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [318037.627,457896.620,0.0]
        addKnot sh k #corner #line [318019.179,457879.748,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317963.834,457829.132,0.0]
        addKnot sh k #corner #line [317982.282,457846.004,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317205.050,456806.618,0.0]
        addKnot sh k #corner #line [317186.601,456789.746,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317131.256,456739.131,0.0]
        addKnot sh k #corner #line [317149.705,456756.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317041.418,456985.539,0.0]
        addKnot sh k #corner #line [317022.970,456968.668,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316967.625,456918.052,0.0]
        addKnot sh k #corner #line [316986.073,456934.924,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315971.281,440007.843,0.0]
        addKnot sh k #corner #line [315847.181,440176.156,0.0]
        addKnot sh k #corner #line [315778.336,440373.616,0.0]
        addKnot sh k #corner #line [315770.891,440582.601,0.0]
        addKnot sh k #corner #line [315825.509,440784.459,0.0]
        addKnot sh k #corner #line [315937.317,440961.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315937.317,440961.177,0.0]
        addKnot sh k #corner #line [315778.298,440825.372,0.0]
        addKnot sh k #corner #line [315586.260,440742.598,0.0]
        addKnot sh k #corner #line [315378.341,440720.245,0.0]
        addKnot sh k #corner #line [315173.096,440760.305,0.0]
        addKnot sh k #corner #line [314988.844,440859.205,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315079.922,440926.131,0.0]
        addKnot sh k #corner #line [315238.709,441109.365,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315004.350,440991.620,0.0]
        addKnot sh k #corner #line [315163.137,441174.854,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314987.673,440857.853,0.0]
        addKnot sh k #corner #line [315446.098,441386.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315370.526,441452.347,0.0]
        addKnot sh k #corner #line [315446.098,441386.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315370.526,441452.347,0.0]
        addKnot sh k #corner #line [315436.016,441527.919,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314949.887,440890.598,0.0]
        addKnot sh k #corner #line [315473.802,441495.175,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315436.016,441527.919,0.0]
        addKnot sh k #corner #line [315473.802,441495.175,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316100.145,440042.024,0.0]
        addKnot sh k #corner #line [316258.932,440225.258,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316024.573,440107.514,0.0]
        addKnot sh k #corner #line [316183.360,440290.748,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316007.896,439973.747,0.0]
        addKnot sh k #corner #line [316531.811,440578.323,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316504.108,440470.007,0.0]
        addKnot sh k #corner #line [316569.597,440545.579,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316504.108,440470.007,0.0]
        addKnot sh k #corner #line [316428.536,440535.496,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316569.597,440545.579,0.0]
        addKnot sh k #corner #line [316531.811,440578.323,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315970.110,440006.491,0.0]
        addKnot sh k #corner #line [316428.536,440535.496,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316007.896,439973.747,0.0]
        addKnot sh k #corner #line [315970.110,440006.491,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314949.887,440890.598,0.0]
        addKnot sh k #corner #line [314987.673,440857.853,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315004.350,440991.620,0.0]
        addKnot sh k #corner #line [315023.243,440975.248,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315079.922,440926.131,0.0]
        addKnot sh k #corner #line [315061.029,440942.503,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315163.137,441174.854,0.0]
        addKnot sh k #corner #line [315182.030,441158.482,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315238.709,441109.365,0.0]
        addKnot sh k #corner #line [315219.816,441125.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316024.573,440107.514,0.0]
        addKnot sh k #corner #line [316043.466,440091.141,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316100.145,440042.024,0.0]
        addKnot sh k #corner #line [316081.252,440058.397,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316183.360,440290.748,0.0]
        addKnot sh k #corner #line [316202.253,440274.375,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316258.932,440225.258,0.0]
        addKnot sh k #corner #line [316240.039,440241.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321776.052,455490.666,0.0]
        addKnot sh k #corner #line [321980.765,455661.027,0.0]
        addKnot sh k #corner #line [322229.103,455757.249,0.0]
        addKnot sh k #corner #line [322495.159,455769.293,0.0]
        addKnot sh k #corner #line [322751.175,455695.903,0.0]
        addKnot sh k #corner #line [322970.443,455544.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322342.597,454890.143,0.0]
        addKnot sh k #corner #line [321747.514,455460.912,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321776.052,455490.666,0.0]
        addKnot sh k #corner #line [322371.136,454919.897,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322371.136,454919.897,0.0]
        addKnot sh k #corner #line [322342.597,454890.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322373.567,454803.312,0.0]
        addKnot sh k #corner #line [322314.059,454860.389,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322314.059,454860.389,0.0]
        addKnot sh k #corner #line [322342.597,454890.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322342.597,454890.143,0.0]
        addKnot sh k #corner #line [322372.351,454861.605,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322372.351,454861.605,0.0]
        addKnot sh k #corner #line [322400.890,454891.359,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322430.644,454862.820,0.0]
        addKnot sh k #corner #line [322373.567,454803.312,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322373.567,454803.312,0.0]
        addKnot sh k #corner #line [322373.567,454803.312,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322400.890,454891.359,0.0]
        addKnot sh k #corner #line [322430.644,454862.820,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321889.037,455430.621,0.0]
        addKnot sh k #corner #line [322003.533,455320.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321812.218,455350.529,0.0]
        addKnot sh k #corner #line [321926.714,455240.711,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321747.514,455460.912,0.0]
        addKnot sh k #corner #line [321776.052,455490.666,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323058.490,455517.412,0.0]
        addKnot sh k #corner #line [323058.490,455517.412,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323001.413,455457.904,0.0]
        addKnot sh k #corner #line [323058.490,455517.412,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322971.659,455486.442,0.0]
        addKnot sh k #corner #line [323001.413,455457.904,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323000.197,455516.196,0.0]
        addKnot sh k #corner #line [322971.659,455486.442,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322970.443,455544.735,0.0]
        addKnot sh k #corner #line [323000.197,455516.196,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322998.982,455574.489,0.0]
        addKnot sh k #corner #line [322970.443,455544.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323058.490,455517.412,0.0]
        addKnot sh k #corner #line [322998.982,455574.489,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321812.218,455350.529,0.0]
        addKnot sh k #corner #line [321836.358,455375.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321926.714,455240.711,0.0]
        addKnot sh k #corner #line [321950.855,455265.880,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321864.897,455405.452,0.0]
        addKnot sh k #corner #line [321889.037,455430.621,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321979.393,455295.634,0.0]
        addKnot sh k #corner #line [322003.533,455320.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305272.664,466270.786,0.0]
        addKnot sh k #corner #line [305123.571,466417.420,0.0]
        addKnot sh k #corner #line [304937.817,466513.469,0.0]
        addKnot sh k #corner #line [304731.980,466550.364,0.0]
        addKnot sh k #corner #line [304524.430,466524.810,0.0]
        addKnot sh k #corner #line [304333.689,466439.089,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304333.689,466439.089,0.0]
        addKnot sh k #corner #line [304490.597,466577.328,0.0]
        addKnot sh k #corner #line [304599.670,466755.746,0.0]
        addKnot sh k #corner #line [304651.173,466958.422,0.0]
        addKnot sh k #corner #line [304640.510,467167.268,0.0]
        addKnot sh k #corner #line [304568.632,467363.644,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304489.510,467282.934,0.0]
        addKnot sh k #corner #line [304285.681,467151.625,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304435.353,467367.000,0.0]
        addKnot sh k #corner #line [304231.525,467235.691,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304570.135,467364.613,0.0]
        addKnot sh k #corner #line [303981.673,466985.518,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303927.517,467069.584,0.0]
        addKnot sh k #corner #line [303981.673,466985.518,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303927.517,467069.584,0.0]
        addKnot sh k #corner #line [303843.451,467015.428,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304543.057,467406.646,0.0]
        addKnot sh k #corner #line [303870.529,466973.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303843.451,467015.428,0.0]
        addKnot sh k #corner #line [303870.529,466973.395,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305220.620,466148.043,0.0]
        addKnot sh k #corner #line [305016.792,466016.734,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305166.464,466232.109,0.0]
        addKnot sh k #corner #line [304962.635,466100.800,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305301.245,466229.721,0.0]
        addKnot sh k #corner #line [304628.717,465796.471,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304739.862,465808.594,0.0]
        addKnot sh k #corner #line [304655.796,465754.438,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304739.862,465808.594,0.0]
        addKnot sh k #corner #line [304685.705,465892.660,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304655.796,465754.438,0.0]
        addKnot sh k #corner #line [304628.717,465796.471,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305274.167,466271.754,0.0]
        addKnot sh k #corner #line [304685.705,465892.660,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305301.245,466229.721,0.0]
        addKnot sh k #corner #line [305274.167,466271.754,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304543.057,467406.646,0.0]
        addKnot sh k #corner #line [304570.135,467364.613,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304435.353,467367.000,0.0]
        addKnot sh k #corner #line [304448.893,467345.984,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304489.510,467282.934,0.0]
        addKnot sh k #corner #line [304475.971,467303.951,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304231.525,467235.691,0.0]
        addKnot sh k #corner #line [304245.064,467214.675,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304285.681,467151.625,0.0]
        addKnot sh k #corner #line [304272.142,467172.642,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305166.464,466232.109,0.0]
        addKnot sh k #corner #line [305180.003,466211.093,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305220.620,466148.043,0.0]
        addKnot sh k #corner #line [305207.081,466169.060,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304962.635,466100.800,0.0]
        addKnot sh k #corner #line [304976.174,466079.784,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305016.792,466016.734,0.0]
        addKnot sh k #corner #line [305003.252,466037.751,0.0]
        updateShape sh
        append made sh
      )
      -- WINDOWS reference only, 33 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_WINDOWS_")
        sh.wirecolor = (color 66 149 244)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268644.668,516216.879,0.0]
        addKnot sh k #corner #line [268644.826,516216.878,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278780.077,536354.283,0.0]
        addKnot sh k #corner #line [279955.754,536113.900,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278820.141,536550.229,0.0]
        addKnot sh k #corner #line [279995.818,536309.846,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279729.358,543153.076,0.0]
        addKnot sh k #corner #line [279420.241,541993.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279922.612,543101.555,0.0]
        addKnot sh k #corner #line [279613.495,541942.052,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [278986.099,540266.607,0.0]
        addKnot sh k #corner #line [278710.145,539098.767,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [279180.742,540220.614,0.0]
        addKnot sh k #corner #line [278904.788,539052.774,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280395.995,536023.887,0.0]
        addKnot sh k #corner #line [281571.671,535783.504,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [280436.058,536219.833,0.0]
        addKnot sh k #corner #line [281611.735,535979.450,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [303136.813,476109.852,0.0]
        addKnot sh k #corner #line [303689.265,475044.584,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302959.264,476017.774,0.0]
        addKnot sh k #corner #line [303511.716,474952.506,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293768.462,510960.992,0.0]
        addKnot sh k #corner #line [293841.112,509763.193,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293568.824,510948.883,0.0]
        addKnot sh k #corner #line [293641.474,509751.084,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [312380.029,478325.600,0.0]
        addKnot sh k #corner #line [312205.671,478227.623,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313087.468,476658.408,0.0]
        addKnot sh k #corner #line [313261.826,476756.386,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304901.645,534262.939,0.0]
        addKnot sh k #corner #line [305095.288,534212.913,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [305545.525,535955.694,0.0]
        addKnot sh k #corner #line [305351.882,536005.720,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321320.516,448880.537,0.0]
        addKnot sh k #corner #line [322112.926,449781.695,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317596.163,444645.063,0.0]
        addKnot sh k #corner #line [318388.573,445546.222,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295763.802,534717.568,0.0]
        addKnot sh k #corner #line [295508.589,533545.022,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [295568.373,534760.105,0.0]
        addKnot sh k #corner #line [295313.160,533587.558,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311443.781,456686.229,0.0]
        addKnot sh k #corner #line [312227.917,455777.863,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311595.179,456816.922,0.0]
        addKnot sh k #corner #line [312379.315,455908.555,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313869.533,454696.994,0.0]
        addKnot sh k #corner #line [314312.301,455101.909,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314004.504,454549.404,0.0]
        addKnot sh k #corner #line [314447.273,454954.319,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310158.861,460643.863,0.0]
        addKnot sh k #corner #line [310631.525,461013.442,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [310282.054,460486.308,0.0]
        addKnot sh k #corner #line [310754.718,460855.887,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316728.506,456604.335,0.0]
        addKnot sh k #corner #line [317548.701,455728.389,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316582.512,456467.632,0.0]
        addKnot sh k #corner #line [317402.707,455591.687,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322169.562,446425.023,0.0]
        addKnot sh k #corner #line [323091.281,445656.626,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [322041.493,446271.400,0.0]
        addKnot sh k #corner #line [322963.212,445503.003,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302724.762,512061.646,0.0]
        addKnot sh k #corner #line [302924.645,512068.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302863.073,513867.434,0.0]
        addKnot sh k #corner #line [302663.190,513860.592,0.0]
        updateShape sh
        append made sh
      )
      -- WINDOW_FRAMES reference only, 105 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_WINDOW_FRAMES_")
        sh.wirecolor = (color 52 158 236)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267723.458,527102.314,0.0]
        addKnot sh k #corner #line [267962.004,527075.938,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268181.811,529063.822,0.0]
        addKnot sh k #corner #line [267943.265,529090.199,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267723.458,527102.314,0.0]
        addKnot sh k #corner #line [267943.265,529090.199,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267962.004,527075.938,0.0]
        addKnot sh k #corner #line [268181.811,529063.822,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268102.295,529072.614,0.0]
        addKnot sh k #corner #line [267882.488,527084.730,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268022.780,529081.407,0.0]
        addKnot sh k #corner #line [267802.973,527093.522,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267802.973,527093.522,0.0]
        addKnot sh k #corner #line [267896.579,527212.158,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267832.863,527363.839,0.0]
        addKnot sh k #corner #line [267926.468,527482.475,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267817.918,527228.680,0.0]
        addKnot sh k #corner #line [267911.523,527347.317,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267862.753,527634.155,0.0]
        addKnot sh k #corner #line [267956.358,527752.792,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267847.808,527498.997,0.0]
        addKnot sh k #corner #line [267941.413,527617.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267892.642,527904.472,0.0]
        addKnot sh k #corner #line [267986.248,528023.108,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267877.698,527769.314,0.0]
        addKnot sh k #corner #line [267971.303,527887.950,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267922.532,528174.789,0.0]
        addKnot sh k #corner #line [268016.138,528293.425,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267907.587,528039.630,0.0]
        addKnot sh k #corner #line [268001.193,528158.267,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267952.422,528445.105,0.0]
        addKnot sh k #corner #line [268046.028,528563.742,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267937.477,528309.947,0.0]
        addKnot sh k #corner #line [268031.083,528428.583,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267982.312,528715.422,0.0]
        addKnot sh k #corner #line [268075.917,528834.058,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267967.367,528580.264,0.0]
        addKnot sh k #corner #line [268060.973,528698.900,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268012.202,528985.739,0.0]
        addKnot sh k #corner #line [268082.477,529074.806,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [267997.257,528850.580,0.0]
        addKnot sh k #corner #line [268090.862,528969.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288605.929,537925.100,0.0]
        addKnot sh k #corner #line [288559.046,537730.673,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287878.551,537894.763,0.0]
        addKnot sh k #corner #line [287925.434,538089.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288605.929,537925.100,0.0]
        addKnot sh k #corner #line [287925.434,538089.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288559.046,537730.673,0.0]
        addKnot sh k #corner #line [287878.551,537894.763,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287894.178,537959.573,0.0]
        addKnot sh k #corner #line [288574.674,537795.482,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287909.806,538024.382,0.0]
        addKnot sh k #corner #line [288590.302,537860.291,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288590.302,537860.291,0.0]
        addKnot sh k #corner #line [288531.052,537806.001,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288497.766,537882.604,0.0]
        addKnot sh k #corner #line [288438.517,537828.314,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288544.034,537871.448,0.0]
        addKnot sh k #corner #line [288484.785,537817.157,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288405.231,537904.918,0.0]
        addKnot sh k #corner #line [288345.982,537850.627,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288451.499,537893.761,0.0]
        addKnot sh k #corner #line [288392.250,537839.471,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288312.696,537927.231,0.0]
        addKnot sh k #corner #line [288253.447,537872.941,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288358.964,537916.075,0.0]
        addKnot sh k #corner #line [288299.714,537861.784,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288220.161,537949.545,0.0]
        addKnot sh k #corner #line [288160.912,537895.254,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288266.428,537938.388,0.0]
        addKnot sh k #corner #line [288207.179,537884.097,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288127.626,537971.858,0.0]
        addKnot sh k #corner #line [288068.376,537917.567,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288173.893,537960.701,0.0]
        addKnot sh k #corner #line [288114.644,537906.411,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288035.090,537994.171,0.0]
        addKnot sh k #corner #line [287975.841,537939.881,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288081.358,537983.015,0.0]
        addKnot sh k #corner #line [288022.109,537928.724,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287942.555,538016.485,0.0]
        addKnot sh k #corner #line [287898.073,537975.726,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287988.823,538005.328,0.0]
        addKnot sh k #corner #line [287929.574,537951.038,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292037.194,511559.352,0.0]
        addKnot sh k #corner #line [292046.596,511359.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291347.370,511326.667,0.0]
        addKnot sh k #corner #line [291337.968,511526.446,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292037.194,511559.352,0.0]
        addKnot sh k #corner #line [291337.968,511526.446,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292046.596,511359.573,0.0]
        addKnot sh k #corner #line [291347.370,511326.667,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291344.236,511393.260,0.0]
        addKnot sh k #corner #line [292043.462,511426.166,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291341.102,511459.853,0.0]
        addKnot sh k #corner #line [292040.328,511492.759,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292040.328,511492.759,0.0]
        addKnot sh k #corner #line [291998.640,511424.057,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291945.246,511488.285,0.0]
        addKnot sh k #corner #line [291903.558,511419.582,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291992.787,511490.522,0.0]
        addKnot sh k #corner #line [291951.099,511421.820,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291850.164,511483.810,0.0]
        addKnot sh k #corner #line [291808.476,511415.108,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291897.705,511486.047,0.0]
        addKnot sh k #corner #line [291856.017,511417.345,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291755.082,511479.335,0.0]
        addKnot sh k #corner #line [291713.393,511410.633,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291802.623,511481.573,0.0]
        addKnot sh k #corner #line [291760.935,511412.870,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291659.999,511474.861,0.0]
        addKnot sh k #corner #line [291618.311,511406.158,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291707.541,511477.098,0.0]
        addKnot sh k #corner #line [291665.852,511408.396,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291564.917,511470.386,0.0]
        addKnot sh k #corner #line [291523.229,511401.684,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291612.458,511472.623,0.0]
        addKnot sh k #corner #line [291570.770,511403.921,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291469.835,511465.912,0.0]
        addKnot sh k #corner #line [291428.147,511397.209,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291517.376,511468.149,0.0]
        addKnot sh k #corner #line [291475.688,511399.447,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291374.753,511461.437,0.0]
        addKnot sh k #corner #line [291343.455,511409.858,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291422.294,511463.674,0.0]
        addKnot sh k #corner #line [291380.606,511394.972,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301895.376,473301.387,0.0]
        addKnot sh k #corner #line [301800.884,473477.657,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301183.939,473146.932,0.0]
        addKnot sh k #corner #line [301278.432,472970.662,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301895.376,473301.387,0.0]
        addKnot sh k #corner #line [301278.432,472970.662,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301800.884,473477.657,0.0]
        addKnot sh k #corner #line [301183.939,473146.932,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301215.436,473088.175,0.0]
        addKnot sh k #corner #line [301832.381,473418.900,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301246.934,473029.418,0.0]
        addKnot sh k #corner #line [301863.879,473360.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301863.879,473360.143,0.0]
        addKnot sh k #corner #line [301792.833,473397.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301779.985,473315.171,0.0]
        addKnot sh k #corner #line [301708.940,473352.727,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301821.932,473337.657,0.0]
        addKnot sh k #corner #line [301750.887,473375.213,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301696.092,473270.198,0.0]
        addKnot sh k #corner #line [301625.047,473307.754,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301738.039,473292.684,0.0]
        addKnot sh k #corner #line [301666.993,473330.241,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301612.198,473225.225,0.0]
        addKnot sh k #corner #line [301541.153,473262.782,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301654.145,473247.712,0.0]
        addKnot sh k #corner #line [301583.100,473285.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301528.305,473180.253,0.0]
        addKnot sh k #corner #line [301457.260,473217.809,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301570.252,473202.739,0.0]
        addKnot sh k #corner #line [301499.206,473240.295,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301444.412,473135.280,0.0]
        addKnot sh k #corner #line [301373.366,473172.836,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301486.358,473157.766,0.0]
        addKnot sh k #corner #line [301415.313,473195.323,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301360.518,473090.307,0.0]
        addKnot sh k #corner #line [301289.473,473127.864,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301402.465,473112.794,0.0]
        addKnot sh k #corner #line [301331.419,473150.350,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301276.625,473045.335,0.0]
        addKnot sh k #corner #line [301223.287,473073.530,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301318.571,473067.821,0.0]
        addKnot sh k #corner #line [301247.526,473105.377,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315916.485,453383.509,0.0]
        addKnot sh k #corner #line [316055.277,453239.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315551.267,452753.735,0.0]
        addKnot sh k #corner #line [315412.475,452897.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315916.485,453383.509,0.0]
        addKnot sh k #corner #line [315412.475,452897.737,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316055.277,453239.507,0.0]
        addKnot sh k #corner #line [315551.267,452753.735,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315505.003,452801.736,0.0]
        addKnot sh k #corner #line [316009.013,453287.508,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315458.739,452849.737,0.0]
        addKnot sh k #corner #line [315962.749,453335.508,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315962.749,453335.508,0.0]
        addKnot sh k #corner #line [315976.705,453256.368,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315894.213,453269.452,0.0]
        addKnot sh k #corner #line [315908.169,453190.312,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315928.481,453302.480,0.0]
        addKnot sh k #corner #line [315942.437,453223.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315825.677,453203.396,0.0]
        addKnot sh k #corner #line [315839.632,453124.256,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315859.945,453236.424,0.0]
        addKnot sh k #corner #line [315873.900,453157.284,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315757.140,453137.340,0.0]
        addKnot sh k #corner #line [315771.096,453058.200,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315791.408,453170.368,0.0]
        addKnot sh k #corner #line [315805.364,453091.228,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315688.604,453071.283,0.0]
        addKnot sh k #corner #line [315702.560,452992.143,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315722.872,453104.312,0.0]
        addKnot sh k #corner #line [315736.828,453025.171,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315620.068,453005.227,0.0]
        addKnot sh k #corner #line [315634.023,452926.087,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315654.336,453038.255,0.0]
        addKnot sh k #corner #line [315668.292,452959.115,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315551.531,452939.171,0.0]
        addKnot sh k #corner #line [315565.487,452860.031,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315585.800,452972.199,0.0]
        addKnot sh k #corner #line [315599.755,452893.059,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315482.995,452873.115,0.0]
        addKnot sh k #corner #line [315493.473,452813.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315517.263,452906.143,0.0]
        addKnot sh k #corner #line [315531.219,452827.003,0.0]
        updateShape sh
        append made sh
      )
      -- DOOR_THRESHOLDS reference only, 17 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_DOOR_THRESHOLDS_")
        sh.wirecolor = (color 234 136 67)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324334.503,456778.086,0.0]
        addKnot sh k #corner #line [326191.025,455056.238,0.0]
        addKnot sh k #corner #line [328100.171,453392.929,0.0]
        addKnot sh k #corner #line [330060.097,451789.768,0.0]
        addKnot sh k #corner #line [332068.909,450248.303,0.0]
        addKnot sh k #corner #line [334124.664,448770.024,0.0]
        addKnot sh k #corner #line [336225.376,447356.361,0.0]
        addKnot sh k #corner #line [338369.015,446008.678,0.0]
        addKnot sh k #corner #line [340553.510,444728.280,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [324403.636,456850.340,0.0]
        addKnot sh k #corner #line [326257.878,455130.606,0.0]
        addKnot sh k #corner #line [328164.681,453469.339,0.0]
        addKnot sh k #corner #line [330122.201,451868.146,0.0]
        addKnot sh k #corner #line [332128.546,450328.574,0.0]
        addKnot sh k #corner #line [334181.777,448852.110,0.0]
        addKnot sh k #corner #line [336279.910,447440.182,0.0]
        addKnot sh k #corner #line [338420.917,446094.155,0.0]
        addKnot sh k #corner #line [340602.730,444815.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326769.741,452160.829,0.0]
        addKnot sh k #corner #line [328912.737,450402.341,0.0]
        addKnot sh k #corner #line [331113.092,448716.179,0.0]
        addKnot sh k #corner #line [333368.367,447104.210,0.0]
        addKnot sh k #corner #line [335676.061,445568.223,0.0]
        addKnot sh k #corner #line [338033.615,444109.920,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [326705.029,452084.590,0.0]
        addKnot sh k #corner #line [328850.599,450323.991,0.0]
        addKnot sh k #corner #line [331053.597,448635.803,0.0]
        addKnot sh k #corner #line [333311.581,447021.898,0.0]
        addKnot sh k #corner #line [335622.047,445484.065,0.0]
        addKnot sh k #corner #line [337982.433,444024.011,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300164.429,458489.983,0.0]
        addKnot sh k #corner #line [300002.232,458372.961,0.0]
        addKnot sh k #corner #line [300879.874,457156.513,0.0]
        addKnot sh k #corner #line [301042.071,457273.536,0.0]
        addKnot sh k #corner #line [300164.429,458489.983,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301459.472,456708.399,0.0]
        addKnot sh k #corner #line [301299.926,456587.786,0.0]
        addKnot sh k #corner #line [302204.496,455391.227,0.0]
        addKnot sh k #corner #line [302364.042,455511.840,0.0]
        addKnot sh k #corner #line [301459.472,456708.399,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [306428.918,450257.500,0.0]
        addKnot sh k #corner #line [307428.802,449139.362,0.0]
        addKnot sh k #corner #line [307577.879,449272.697,0.0]
        addKnot sh k #corner #line [306577.892,450390.743,0.0]
        addKnot sh k #corner #line [306427.810,450258.548,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [307906.081,448617.571,0.0]
        addKnot sh k #corner #line [308930.769,447522.119,0.0]
        addKnot sh k #corner #line [309076.834,447658.748,0.0]
        addKnot sh k #corner #line [308052.146,448754.200,0.0]
        addKnot sh k #corner #line [307905.052,448618.689,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313802.890,443006.192,0.0]
        addKnot sh k #corner #line [314914.268,441998.800,0.0]
        addKnot sh k #corner #line [314779.945,441850.612,0.0]
        addKnot sh k #corner #line [313668.567,442858.004,0.0]
        addKnot sh k #corner #line [313798.644,443001.507,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315440.157,441532.698,0.0]
        addKnot sh k #corner #line [316573.738,440550.357,0.0]
        addKnot sh k #corner #line [316442.755,440399.209,0.0]
        addKnot sh k #corner #line [315309.174,441381.549,0.0]
        addKnot sh k #corner #line [315440.157,441532.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321434.748,436656.602,0.0]
        addKnot sh k #corner #line [322645.306,435770.854,0.0]
        addKnot sh k #corner #line [322527.203,435609.442,0.0]
        addKnot sh k #corner #line [321316.645,436495.190,0.0]
        addKnot sh k #corner #line [321431.014,436651.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291199.731,461784.454,0.0]
        addKnot sh k #corner #line [291982.570,460504.937,0.0]
        addKnot sh k #corner #line [291811.963,460400.556,0.0]
        addKnot sh k #corner #line [291029.124,461680.073,0.0]
        addKnot sh k #corner #line [291199.731,461784.454,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [285987.420,471115.516,0.0]
        addKnot sh k #corner #line [286635.473,469762.731,0.0]
        addKnot sh k #corner #line [286815.849,469849.140,0.0]
        addKnot sh k #corner #line [286167.796,471201.925,0.0]
        addKnot sh k #corner #line [285987.420,471115.516,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [304818.617,465859.330,0.0]
        addKnot sh k #corner #line [304006.272,467120.320,0.0]
        addKnot sh k #corner #line [303838.135,467012.003,0.0]
        addKnot sh k #corner #line [304650.479,465751.013,0.0]
        addKnot sh k #corner #line [304818.617,465859.330,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317886.112,458099.336,0.0]
        addKnot sh k #corner #line [316779.212,457087.025,0.0]
        addKnot sh k #corner #line [316644.238,457234.612,0.0]
        addKnot sh k #corner #line [317751.137,458246.923,0.0]
        addKnot sh k #corner #line [317886.112,458099.336,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [323097.365,455488.247,0.0]
        addKnot sh k #corner #line [322405.156,454766.550,0.0]
        addKnot sh k #corner #line [322332.986,454835.771,0.0]
        addKnot sh k #corner #line [323025.195,455557.468,0.0]
        addKnot sh k #corner #line [323097.365,455488.247,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [311845.396,462376.107,0.0]
        addKnot sh k #corner #line [310937.504,463570.147,0.0]
        addKnot sh k #corner #line [310778.292,463449.090,0.0]
        addKnot sh k #corner #line [311686.185,462255.050,0.0]
        addKnot sh k #corner #line [311845.396,462376.107,0.0]
        updateShape sh
        sh.isHidden = true
        append made sh
      )
      -- STAIRS reference only, 185 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_STAIRS_")
        sh.wirecolor = (color 173 173 173)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299059.127,469942.993,0.0]
        addKnot sh k #corner #line [299997.432,468346.524,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299800.031,470340.170,0.0]
        addKnot sh k #corner #line [300721.614,468772.154,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300984.163,471088.411,0.0]
        addKnot sh k #corner #line [301928.584,469481.536,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301775.777,471399.309,0.0]
        addKnot sh k #corner #line [302652.767,469907.165,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302763.650,471928.878,0.0]
        addKnot sh k #corner #line [303618.343,470474.671,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302269.713,471664.094,0.0]
        addKnot sh k #corner #line [303135.555,470190.918,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302516.682,471796.486,0.0]
        addKnot sh k #corner #line [303376.949,470332.795,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300293.968,470604.955,0.0]
        addKnot sh k #corner #line [301204.402,469055.907,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302022.745,471531.701,0.0]
        addKnot sh k #corner #line [302894.161,470049.042,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301281.841,471134.524,0.0]
        addKnot sh k #corner #line [302169.979,469623.412,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300047.000,470472.563,0.0]
        addKnot sh k #corner #line [300963.008,468914.030,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299306.095,470075.385,0.0]
        addKnot sh k #corner #line [300238.826,468488.401,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299553.063,470207.778,0.0]
        addKnot sh k #corner #line [300480.220,468630.277,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300540.936,470737.347,0.0]
        addKnot sh k #corner #line [301445.796,469197.783,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300787.904,470869.740,0.0]
        addKnot sh k #corner #line [301687.190,469339.660,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301236.915,471223.786,0.0]
        addKnot sh k #corner #line [300518.819,472563.409,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302717.583,472017.526,0.0]
        addKnot sh k #corner #line [301999.503,473357.119,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300003.025,470562.336,0.0]
        addKnot sh k #corner #line [299284.917,471901.983,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299015.914,470033.176,0.0]
        addKnot sh k #corner #line [298297.794,471372.842,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302470.805,471885.236,0.0]
        addKnot sh k #corner #line [301752.722,473224.834,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301483.693,471356.076,0.0]
        addKnot sh k #corner #line [300765.600,472695.694,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301977.249,471620.656,0.0]
        addKnot sh k #corner #line [301259.161,472960.264,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301528.809,471266.917,0.0]
        addKnot sh k #corner #line [302411.373,469765.289,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [301730.471,471488.366,0.0]
        addKnot sh k #corner #line [301012.380,472827.979,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [302224.027,471752.946,0.0]
        addKnot sh k #corner #line [301505.942,473092.549,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300990.137,471091.496,0.0]
        addKnot sh k #corner #line [300272.039,472431.123,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300496.581,470826.916,0.0]
        addKnot sh k #corner #line [300337.553,471123.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300296.556,471200.068,0.0]
        addKnot sh k #corner #line [299778.478,472166.553,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300743.359,470959.206,0.0]
        addKnot sh k #corner #line [300025.258,472298.838,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300249.803,470694.626,0.0]
        addKnot sh k #corner #line [299731.722,471661.118,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299690.724,471737.600,0.0]
        addKnot sh k #corner #line [299531.697,472034.268,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299756.247,470430.046,0.0]
        addKnot sh k #corner #line [299038.136,471769.698,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299262.692,470165.466,0.0]
        addKnot sh k #corner #line [298544.575,471505.128,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299509.469,470297.756,0.0]
        addKnot sh k #corner #line [298791.355,471637.413,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298961.800,470004.168,0.0]
        addKnot sh k #corner #line [300605.881,470885.509,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299394.218,471960.573,0.0]
        addKnot sh k #corner #line [299964.999,471454.140,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299422.396,471975.678,0.0]
        addKnot sh k #corner #line [299991.225,471470.977,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300084.882,471347.772,0.0]
        addKnot sh k #corner #line [300653.711,470843.071,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300111.108,471364.609,0.0]
        addKnot sh k #corner #line [300681.889,470858.177,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300111.108,471364.609,0.0]
        addKnot sh k #corner #line [299987.024,471284.946,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299987.024,471284.946,0.0]
        addKnot sh k #corner #line [300089.083,471533.804,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [300089.083,471533.804,0.0]
        addKnot sh k #corner #line [299964.999,471454.140,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [298297.794,471372.842,0.0]
        addKnot sh k #corner #line [299394.218,471960.573,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299422.396,471975.678,0.0]
        addKnot sh k #corner #line [301999.503,473357.119,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [299997.432,468346.524,0.0]
        addKnot sh k #corner #line [303618.343,470474.671,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291433.089,513317.115,0.0]
        addKnot sh k #corner #line [291435.734,513217.245,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291374.656,513256.660,0.0]
        addKnot sh k #corner #line [291378.671,513110.110,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287170.189,513184.156,0.0]
        addKnot sh k #corner #line [287257.239,511334.405,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288010.812,513190.677,0.0]
        addKnot sh k #corner #line [288096.310,511373.892,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289411.850,513201.545,0.0]
        addKnot sh k #corner #line [289494.763,511439.704,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290252.472,513208.066,0.0]
        addKnot sh k #corner #line [290333.834,511479.191,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291373.303,513216.760,0.0]
        addKnot sh k #corner #line [291452.596,511531.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290812.888,513212.413,0.0]
        addKnot sh k #corner #line [290893.215,511505.516,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291093.095,513214.587,0.0]
        addKnot sh k #corner #line [291172.905,511518.678,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288566.522,513294.990,0.0]
        addKnot sh k #corner #line [288655.691,511400.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290532.680,513210.239,0.0]
        addKnot sh k #corner #line [290613.525,511492.354,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289692.057,513203.718,0.0]
        addKnot sh k #corner #line [289774.453,511452.866,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288291.019,513192.850,0.0]
        addKnot sh k #corner #line [288376.001,511387.055,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287450.396,513186.329,0.0]
        addKnot sh k #corner #line [287536.930,511347.567,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287730.604,513188.503,0.0]
        addKnot sh k #corner #line [287816.620,511360.730,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288851.434,513197.198,0.0]
        addKnot sh k #corner #line [288935.382,511413.379,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289131.642,513199.371,0.0]
        addKnot sh k #corner #line [289215.072,511426.542,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289693.861,513303.625,0.0]
        addKnot sh k #corner #line [289682.102,514823.530,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291373.810,513316.655,0.0]
        addKnot sh k #corner #line [291362.052,514836.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288293.903,513292.767,0.0]
        addKnot sh k #corner #line [288282.144,514812.700,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287173.937,513284.081,0.0]
        addKnot sh k #corner #line [287162.178,514804.035,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291093.819,513314.484,0.0]
        addKnot sh k #corner #line [291082.060,514834.361,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289973.852,513305.797,0.0]
        addKnot sh k #corner #line [289962.094,514825.696,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290533.836,513310.140,0.0]
        addKnot sh k #corner #line [290522.077,514830.029,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289972.265,513205.892,0.0]
        addKnot sh k #corner #line [290054.144,511466.029,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290253.844,513307.969,0.0]
        addKnot sh k #corner #line [290242.085,514827.863,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290813.827,513312.312,0.0]
        addKnot sh k #corner #line [290802.069,514832.195,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289413.869,513301.454,0.0]
        addKnot sh k #corner #line [289402.111,514821.364,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288853.886,513297.111,0.0]
        addKnot sh k #corner #line [288851.282,513633.706,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288850.611,513720.480,0.0]
        addKnot sh k #corner #line [288842.127,514817.032,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289133.878,513299.282,0.0]
        addKnot sh k #corner #line [289122.119,514819.198,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288573.894,513294.939,0.0]
        addKnot sh k #corner #line [288565.411,514391.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288564.740,514478.274,0.0]
        addKnot sh k #corner #line [288562.136,514814.866,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288013.911,513290.596,0.0]
        addKnot sh k #corner #line [288002.153,514810.534,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287453.928,513286.252,0.0]
        addKnot sh k #corner #line [287442.169,514806.201,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287733.920,513288.424,0.0]
        addKnot sh k #corner #line [287722.161,514808.367,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287112.540,513283.605,0.0]
        addKnot sh k #corner #line [288977.897,513298.072,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289009.867,513298.320,0.0]
        addKnot sh k #corner #line [291433.089,513317.115,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287174.072,513224.080,0.0]
        addKnot sh k #corner #line [289000.466,513238.246,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289032.436,513238.494,0.0]
        addKnot sh k #corner #line [291374.656,513256.660,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288406.155,514813.659,0.0]
        addKnot sh k #corner #line [288675.487,514099.708,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288438.125,514813.906,0.0]
        addKnot sh k #corner #line [288706.536,514102.398,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288732.055,513949.754,0.0]
        addKnot sh k #corner #line [289000.466,513238.246,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288763.104,513952.444,0.0]
        addKnot sh k #corner #line [289032.436,513238.494,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288763.104,513952.444,0.0]
        addKnot sh k #corner #line [288616.199,513939.718,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288616.199,513939.718,0.0]
        addKnot sh k #corner #line [288822.392,514112.434,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288822.392,514112.434,0.0]
        addKnot sh k #corner #line [288675.487,514099.708,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287162.178,514804.035,0.0]
        addKnot sh k #corner #line [288406.155,514813.659,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288438.125,514813.906,0.0]
        addKnot sh k #corner #line [291362.052,514836.527,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287257.239,511334.405,0.0]
        addKnot sh k #corner #line [291452.596,511531.841,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294351.389,538375.146,0.0]
        addKnot sh k #corner #line [294367.711,538432.796,0.0]
        addKnot sh k #corner #line [292014.119,539099.160,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291983.357,539107.870,0.0]
        addKnot sh k #corner #line [290152.021,539626.369,0.0]
        addKnot sh k #corner #line [290092.093,539414.688,0.0]
        addKnot sh k #corner #line [294308.889,538220.891,0.0]
        addKnot sh k #corner #line [294323.517,538281.556,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293754.835,538544.035,0.0]
        addKnot sh k #corner #line [294168.891,540006.478,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292138.366,539001.666,0.0]
        addKnot sh k #corner #line [292552.431,540464.141,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291921.914,540292.823,0.0]
        addKnot sh k #corner #line [292013.611,540616.695,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291060.719,539306.753,0.0]
        addKnot sh k #corner #line [291474.790,540769.249,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290521.896,539459.297,0.0]
        addKnot sh k #corner #line [290935.970,540921.803,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292019.041,539035.447,0.0]
        addKnot sh k #corner #line [294350.698,538375.343,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291863.524,540659.188,0.0]
        addKnot sh k #corner #line [291922.293,539898.391,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291965.197,539732.492,0.0]
        addKnot sh k #corner #line [292019.041,539035.447,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291965.197,539732.492,0.0]
        addKnot sh k #corner #line [291820.601,539761.386,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291894.287,540650.479,0.0]
        addKnot sh k #corner #line [294707.712,539853.924,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290220.897,539440.581,0.0]
        addKnot sh k #corner #line [289786.835,537640.484,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292377.853,538829.936,0.0]
        addKnot sh k #corner #line [291964.421,537115.396,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293995.570,538371.952,0.0]
        addKnot sh k #corner #line [293597.611,536721.581,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291568.994,539058.927,0.0]
        addKnot sh k #corner #line [291147.826,537312.304,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292647.472,538753.605,0.0]
        addKnot sh k #corner #line [292236.619,537049.761,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291299.375,539135.258,0.0]
        addKnot sh k #corner #line [290875.628,537377.940,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291838.614,538982.597,0.0]
        addKnot sh k #corner #line [291420.024,537246.668,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292108.233,538906.266,0.0]
        addKnot sh k #corner #line [291692.223,537181.032,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292677.189,538849.122,0.0]
        addKnot sh k #corner #line [293091.251,540311.586,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291330.131,539230.481,0.0]
        addKnot sh k #corner #line [291744.200,540692.972,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290252.484,539535.568,0.0]
        addKnot sh k #corner #line [290666.560,540998.080,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294024.247,538467.763,0.0]
        addKnot sh k #corner #line [294438.301,539930.201,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292946.600,538772.850,0.0]
        addKnot sh k #corner #line [293360.661,540235.309,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293485.424,538620.307,0.0]
        addKnot sh k #corner #line [293899.481,540082.755,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292917.092,538677.274,0.0]
        addKnot sh k #corner #line [292508.818,536984.125,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293216.012,538696.579,0.0]
        addKnot sh k #corner #line [293630.071,540159.032,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292407.777,538925.394,0.0]
        addKnot sh k #corner #line [292821.841,540387.864,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291868.954,539077.938,0.0]
        addKnot sh k #corner #line [291960.651,539401.812,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291984.291,539485.307,0.0]
        addKnot sh k #corner #line [292283.021,540540.418,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291599.542,539154.209,0.0]
        addKnot sh k #corner #line [291898.274,540209.328,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290791.308,539383.025,0.0]
        addKnot sh k #corner #line [291205.380,540845.526,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290193.408,539552.293,0.0]
        addKnot sh k #corner #line [291988.279,539044.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291894.287,540650.479,0.0]
        addKnot sh k #corner #line [291952.854,539892.284,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291934.636,539738.598,0.0]
        addKnot sh k #corner #line [291988.279,539044.156,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291820.601,539761.386,0.0]
        addKnot sh k #corner #line [292066.889,539869.497,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [292066.889,539869.497,0.0]
        addKnot sh k #corner #line [291922.293,539898.391,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290666.560,540998.080,0.0]
        addKnot sh k #corner #line [291863.524,540659.188,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289786.835,537640.484,0.0]
        addKnot sh k #corner #line [293869.809,536655.945,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291029.755,539211.589,0.0]
        addKnot sh k #corner #line [290603.430,537443.576,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293186.711,538600.944,0.0]
        addKnot sh k #corner #line [292781.016,536918.489,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294265.189,538295.621,0.0]
        addKnot sh k #corner #line [293869.809,536655.945,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293725.950,538448.282,0.0]
        addKnot sh k #corner #line [293325.413,536787.217,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293456.331,538524.613,0.0]
        addKnot sh k #corner #line [293053.214,536852.853,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290490.516,539364.250,0.0]
        addKnot sh k #corner #line [290059.033,537574.848,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [290760.136,539287.919,0.0]
        addKnot sh k #corner #line [290331.231,537509.212,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [294293.658,538391.491,0.0]
        addKnot sh k #corner #line [294707.712,539853.924,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314523.215,449513.075,0.0]
        addKnot sh k #corner #line [315859.654,448231.225,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315128.493,450096.451,0.0]
        addKnot sh k #corner #line [316441.113,448837.447,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316137.289,451068.746,0.0]
        addKnot sh k #corner #line [317410.213,449847.816,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316742.566,451652.123,0.0]
        addKnot sh k #corner #line [317991.673,450454.037,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317549.603,452429.958,0.0]
        addKnot sh k #corner #line [318766.952,451262.333,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317146.084,452041.040,0.0]
        addKnot sh k #corner #line [318379.312,450858.185,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317347.844,452235.499,0.0]
        addKnot sh k #corner #line [318573.132,451060.259,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315532.011,450485.369,0.0]
        addKnot sh k #corner #line [316828.753,449241.594,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316944.325,451846.581,0.0]
        addKnot sh k #corner #line [318185.492,450656.111,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316339.048,451263.205,0.0]
        addKnot sh k #corner #line [317604.033,450049.890,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315330.252,450290.910,0.0]
        addKnot sh k #corner #line [316634.933,449039.520,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314724.974,449707.534,0.0]
        addKnot sh k #corner #line [316053.474,448433.299,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314926.734,449901.993,0.0]
        addKnot sh k #corner #line [316247.293,448635.373,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315733.770,450679.828,0.0]
        addKnot sh k #corner #line [317022.573,449443.668,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315935.529,450874.287,0.0]
        addKnot sh k #corner #line [317216.393,449645.742,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316271.595,451336.907,0.0]
        addKnot sh k #corner #line [315216.832,452431.313,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317481.218,452502.759,0.0]
        addKnot sh k #corner #line [316426.478,453597.141,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315263.575,450365.363,0.0]
        addKnot sh k #corner #line [314208.793,451459.789,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314457.160,449588.128,0.0]
        addKnot sh k #corner #line [313402.363,450682.570,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317279.614,452308.450,0.0]
        addKnot sh k #corner #line [316224.870,453402.836,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316473.199,451531.215,0.0]
        addKnot sh k #corner #line [315418.439,452625.617,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316876.406,451919.833,0.0]
        addKnot sh k #corner #line [315821.655,453014.227,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316540.807,451457.664,0.0]
        addKnot sh k #corner #line [317797.853,450251.964,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316674.802,451725.524,0.0]
        addKnot sh k #corner #line [315620.047,452819.922,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [317078.010,452114.142,0.0]
        addKnot sh k #corner #line [316023.263,453208.532,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [316069.991,451142.598,0.0]
        addKnot sh k #corner #line [315015.224,452237.008,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315666.783,450753.980,0.0]
        addKnot sh k #corner #line [315433.197,450996.345,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315372.979,451058.827,0.0]
        addKnot sh k #corner #line [314612.009,451848.398,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315868.387,450948.289,0.0]
        addKnot sh k #corner #line [314813.616,452042.703,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315465.179,450559.672,0.0]
        addKnot sh k #corner #line [314704.204,451349.249,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314643.985,451411.731,0.0]
        addKnot sh k #corner #line [314410.401,451654.094,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315061.972,450171.054,0.0]
        addKnot sh k #corner #line [314007.186,451265.484,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314658.764,449782.437,0.0]
        addKnot sh k #corner #line [313603.970,450876.875,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314860.368,449976.746,0.0]
        addKnot sh k #corner #line [313805.578,451071.179,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314298.087,451545.848,0.0]
        addKnot sh k #corner #line [314984.905,451213.362,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [314321.107,451568.034,0.0]
        addKnot sh k #corner #line [315005.576,451236.686,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315129.160,451143.529,0.0]
        addKnot sh k #corner #line [315813.628,450812.180,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315149.830,451166.853,0.0]
        addKnot sh k #corner #line [315836.648,450834.367,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315149.830,451166.853,0.0]
        addKnot sh k #corner #line [315052.029,451056.499,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315052.029,451056.499,0.0]
        addKnot sh k #corner #line [315082.706,451323.716,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [315082.706,451323.716,0.0]
        addKnot sh k #corner #line [314984.905,451213.362,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [313402.363,450682.570,0.0]
        addKnot sh k #corner #line [314298.087,451545.848,0.0]
        updateShape sh
        sh.isHidden = true
        append made sh
      )
      -- RAMPS reference only, 26 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_RAMPS_")
        sh.wirecolor = (color 219 191 122)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287276.538,494828.858,0.0]
        addKnot sh k #corner #line [291903.208,496107.107,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287399.297,494572.284,0.0]
        addKnot sh k #corner #line [291929.578,495823.903,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287276.523,494828.854,0.0]
        addKnot sh k #corner #line [289811.743,485652.631,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287473.861,494302.395,0.0]
        addKnot sh k #corner #line [292004.143,495554.013,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287548.426,494032.506,0.0]
        addKnot sh k #corner #line [292078.707,495284.124,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287622.990,493762.617,0.0]
        addKnot sh k #corner #line [292153.272,495014.235,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287697.555,493492.728,0.0]
        addKnot sh k #corner #line [292227.837,494744.346,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287772.119,493222.838,0.0]
        addKnot sh k #corner #line [292302.401,494474.457,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287846.684,492952.949,0.0]
        addKnot sh k #corner #line [292376.966,494204.568,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287921.248,492683.060,0.0]
        addKnot sh k #corner #line [292451.530,493934.679,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287995.813,492413.171,0.0]
        addKnot sh k #corner #line [292526.095,493664.790,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288070.377,492143.282,0.0]
        addKnot sh k #corner #line [292600.659,493394.901,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288144.942,491873.393,0.0]
        addKnot sh k #corner #line [292675.224,493125.011,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288219.507,491603.504,0.0]
        addKnot sh k #corner #line [292749.788,492855.122,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288294.071,491333.615,0.0]
        addKnot sh k #corner #line [292824.353,492585.233,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288368.636,491063.726,0.0]
        addKnot sh k #corner #line [292898.917,492315.344,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288443.200,490793.836,0.0]
        addKnot sh k #corner #line [292973.482,492045.455,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288741.470,489714.283,0.0]
        addKnot sh k #corner #line [291583.412,490499.450,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288816.034,489444.394,0.0]
        addKnot sh k #corner #line [291194.409,490101.487,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288890.599,489174.505,0.0]
        addKnot sh k #corner #line [290565.222,489637.167,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [288965.163,488904.616,0.0]
        addKnot sh k #corner #line [290056.127,489206.026,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289039.728,488634.727,0.0]
        addKnot sh k #corner #line [289547.032,488774.884,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [287276.523,494828.854,0.0]
        addKnot sh k #corner #line [287324.718,494842.169,0.0]
        addKnot sh k #corner #line [289859.937,485665.946,0.0]
        addKnot sh k #corner #line [289811.743,485652.631,0.0]
        close sh k
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291903.194,496107.103,0.0]
        addKnot sh k #corner #line [294438.413,486930.880,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [293098.085,491782.195,0.0]
        addKnot sh k #corner #line [291903.194,496107.103,0.0]
        addKnot sh k #corner #line [291854.999,496093.788,0.0]
        addKnot sh k #corner #line [293056.048,491746.594,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [291903.194,496107.103,0.0]
        addKnot sh k #corner #line [294438.413,486930.880,0.0]
        updateShape sh
        sh.isHidden = true
        append made sh
      )
      -- RAILINGS reference only, 6 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_RAILINGS_")
        sh.wirecolor = (color 129 203 153)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268738.135,538407.493,0.0]
        addKnot sh k #corner #line [268171.405,535428.866,0.0]
        addKnot sh k #corner #line [267685.512,532435.989,0.0]
        addKnot sh k #corner #line [267280.810,529431.057,0.0]
        addKnot sh k #corner #line [266957.597,526416.271,0.0]
        addKnot sh k #corner #line [266716.109,523393.841,0.0]
        addKnot sh k #corner #line [266556.524,520365.981,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [268836.110,538387.474,0.0]
        addKnot sh k #corner #line [268269.880,535411.467,0.0]
        addKnot sh k #corner #line [267784.416,532421.223,0.0]
        addKnot sh k #corner #line [267380.073,529418.934,0.0]
        addKnot sh k #corner #line [267057.148,526406.800,0.0]
        addKnot sh k #corner #line [266815.877,523387.029,0.0]
        addKnot sh k #corner #line [266656.438,520361.832,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284765.080,443351.548,0.0]
        addKnot sh k #corner #line [286595.153,440985.477,0.0]
        addKnot sh k #corner #line [288483.618,438665.744,0.0]
        addKnot sh k #corner #line [290429.301,436393.790,0.0]
        addKnot sh k #corner #line [292430.995,434171.025,0.0]
        addKnot sh k #corner #line [294487.455,431998.831,0.0]
        addKnot sh k #corner #line [296597.406,429878.556,0.0]
        addKnot sh k #corner #line [298759.537,427811.517,0.0]
        addKnot sh k #corner #line [300972.505,425798.998,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [284717.166,443315.433,0.0]
        addKnot sh k #corner #line [286552.818,440942.303,0.0]
        addKnot sh k #corner #line [288447.180,438615.771,0.0]
        addKnot sh k #corner #line [290399.071,436337.288,0.0]
        addKnot sh k #corner #line [292407.272,434108.278,0.0]
        addKnot sh k #corner #line [294470.531,431930.130,0.0]
        addKnot sh k #corner #line [296587.558,429804.206,0.0]
        addKnot sh k #corner #line [298757.034,427731.831,0.0]
        addKnot sh k #corner #line [300977.603,425714.299,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289476.371,446903.130,0.0]
        addKnot sh k #corner #line [291474.879,444328.948,0.0]
        addKnot sh k #corner #line [293546.070,441812.877,0.0]
        addKnot sh k #corner #line [295688.255,439356.968,0.0]
        addKnot sh k #corner #line [297899.686,436963.222,0.0]
        addKnot sh k #corner #line [300178.562,434633.593,0.0]
        addKnot sh k #corner #line [302523.023,432369.979,0.0]
        addKnot sh k #corner #line [304931.158,430174.226,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [289428.457,446867.015,0.0]
        addKnot sh k #corner #line [291422.662,444298.177,0.0]
        addKnot sh k #corner #line [293489.211,441787.169,0.0]
        addKnot sh k #corner #line [295626.426,439336.028,0.0]
        addKnot sh k #corner #line [297832.575,436946.741,0.0]
        addKnot sh k #corner #line [300105.868,434621.247,0.0]
        addKnot sh k #corner #line [302444.461,432361.432,0.0]
        addKnot sh k #corner #line [304846.458,430169.129,0.0]
        updateShape sh
        sh.isHidden = true
        append made sh
      )
      -- PROJECTION reference only, 6 2D entities
      if makeReference2D do
      (
        sh = splineShape name:(uniqueName "DQ1F3D_REF_PROJECTION_")
        sh.wirecolor = (color 224 71 171)
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [321434.355,473627.341,0.0]
        addKnot sh k #corner #line [323000.840,472179.191,0.0]
        addKnot sh k #corner #line [324627.089,470798.493,0.0]
        addKnot sh k #corner #line [326310.199,469487.711,0.0]
        addKnot sh k #corner #line [328047.168,468249.183,0.0]
        addKnot sh k #corner #line [329834.895,467085.119,0.0]
        addKnot sh k #corner #line [331670.191,465997.598,0.0]
        addKnot sh k #corner #line [333549.780,464988.560,0.0]
        addKnot sh k #corner #line [335470.308,464059.806,0.0]
        addKnot sh k #corner #line [337428.348,463212.992,0.0]
        addKnot sh k #corner #line [339420.405,462449.630,0.0]
        addKnot sh k #corner #line [341442.924,461771.083,0.0]
        addKnot sh k #corner #line [343492.298,461178.561,0.0]
        addKnot sh k #corner #line [345564.867,460673.122,0.0]
        addKnot sh k #corner #line [347656.934,460255.667,0.0]
        addKnot sh k #corner #line [349764.765,459926.942,0.0]
        addKnot sh k #corner #line [351884.599,459687.533,0.0]
        addKnot sh k #corner #line [354012.653,459537.867,0.0]
        addKnot sh k #corner #line [356145.129,459478.212,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [309629.468,502203.859,0.0]
        addKnot sh k #corner #line [309738.343,500232.458,0.0]
        addKnot sh k #corner #line [309935.550,498267.927,0.0]
        addKnot sh k #corner #line [310220.689,496314.221,0.0]
        addKnot sh k #corner #line [310593.188,494375.273,0.0]
        addKnot sh k #corner #line [311052.296,492454.989,0.0]
        addKnot sh k #corner #line [311597.089,490557.234,0.0]
        addKnot sh k #corner #line [312226.469,488685.829,0.0]
        addKnot sh k #corner #line [312939.170,486844.544,0.0]
        addKnot sh k #corner #line [313733.756,485037.086,0.0]
        addKnot sh k #corner #line [314608.627,483267.093,0.0]
        addKnot sh k #corner #line [315562.022,481538.131,0.0]
        addKnot sh k #corner #line [316592.022,479853.680,0.0]
        addKnot sh k #corner #line [317696.551,478217.133,0.0]
        addKnot sh k #corner #line [318873.386,476631.784,0.0]
        addKnot sh k #corner #line [320120.158,475100.825,0.0]
        addKnot sh k #corner #line [321434.356,473627.340,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320596.866,540222.764,0.0]
        addKnot sh k #corner #line [319278.444,538089.095,0.0]
        addKnot sh k #corner #line [318038.439,535908.918,0.0]
        addKnot sh k #corner #line [316878.489,533685.116,0.0]
        addKnot sh k #corner #line [315800.127,531420.626,0.0]
        addKnot sh k #corner #line [314804.778,529118.440,0.0]
        addKnot sh k #corner #line [313893.757,526781.600,0.0]
        addKnot sh k #corner #line [313068.268,524413.193,0.0]
        addKnot sh k #corner #line [312329.401,522016.350,0.0]
        addKnot sh k #corner #line [311678.133,519594.237,0.0]
        addKnot sh k #corner #line [311115.324,517150.055,0.0]
        addKnot sh k #corner #line [310641.718,514687.033,0.0]
        addKnot sh k #corner #line [310257.941,512208.425,0.0]
        addKnot sh k #corner #line [309964.499,509717.507,0.0]
        addKnot sh k #corner #line [309761.782,507217.570,0.0]
        addKnot sh k #corner #line [309650.055,504711.917,0.0]
        addKnot sh k #corner #line [309629.468,502203.859,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [390280.174,458163.268,0.0]
        addKnot sh k #corner #line [387657.872,458006.984,0.0]
        addKnot sh k #corner #line [385042.481,457760.758,0.0]
        addKnot sh k #corner #line [382437.087,457424.879,0.0]
        addKnot sh k #corner #line [379844.760,456999.744,0.0]
        addKnot sh k #corner #line [377268.559,456485.855,0.0]
        addKnot sh k #corner #line [374711.521,455883.816,0.0]
        addKnot sh k #corner #line [372176.660,455194.339,0.0]
        addKnot sh k #corner #line [369666.967,454418.236,0.0]
        addKnot sh k #corner #line [367185.401,453556.421,0.0]
        addKnot sh k #corner #line [364734.887,452609.913,0.0]
        addKnot sh k #corner #line [362318.316,451579.825,0.0]
        addKnot sh k #corner #line [359938.537,450467.375,0.0]
        addKnot sh k #corner #line [357598.356,449273.872,0.0]
        addKnot sh k #corner #line [355300.533,448000.724,0.0]
        addKnot sh k #corner #line [353047.777,446649.433,0.0]
        addKnot sh k #corner #line [350842.745,445221.592,0.0]
        addKnot sh k #corner #line [348688.037,443718.885,0.0]
        addKnot sh k #corner #line [346586.194,442143.084,0.0]
        addKnot sh k #corner #line [344539.693,440496.047,0.0]
        addKnot sh k #corner #line [342550.949,438779.716,0.0]
        addKnot sh k #corner #line [340622.307,436996.114,0.0]
        addKnot sh k #corner #line [338756.040,435147.346,0.0]
        addKnot sh k #corner #line [336954.350,433235.591,0.0]
        addKnot sh k #corner #line [335219.360,431263.104,0.0]
        addKnot sh k #corner #line [333553.117,429232.210,0.0]
        addKnot sh k #corner #line [331957.586,427145.304,0.0]
        addKnot sh k #corner #line [330434.648,425004.847,0.0]
        addKnot sh k #corner #line [328986.099,422813.364,0.0]
        addKnot sh k #corner #line [327613.646,420573.437,0.0]
        addKnot sh k #corner #line [326318.909,418287.709,0.0]
        addKnot sh k #corner #line [325103.414,415958.875,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [320596.866,540222.764,0.0]
        addKnot sh k #corner #line [320858.461,540716.959,0.0]
        addKnot sh k #corner #line [321032.864,541248.225,0.0]
        addKnot sh k #corner #line [321115.068,541801.311,0.0]
        addKnot sh k #corner #line [321102.712,542360.335,0.0]
        addKnot sh k #corner #line [320996.152,542909.248,0.0]
        addKnot sh k #corner #line [320798.447,543432.290,0.0]
        addKnot sh k #corner #line [320515.273,543914.445,0.0]
        addKnot sh k #corner #line [320154.760,544341.869,0.0]
        addKnot sh k #corner #line [319727.259,544702.290,0.0]
        addKnot sh k #corner #line [319245.044,544985.361,0.0]
        addNewSpline sh
        k = numSplines sh
        addKnot sh k #corner #line [319245.044,544985.361,0.0]
        addKnot sh k #corner #line [277704.382,564847.204,0.0]
        addKnot sh k #corner #line [276520.237,562291.334,0.0]
        addKnot sh k #corner #line [275404.228,559720.655,0.0]
        addKnot sh k #corner #line [274356.017,557136.236,0.0]
        addKnot sh k #corner #line [273375.263,554539.145,0.0]
        addKnot sh k #corner #line [272461.624,551930.453,0.0]
        addKnot sh k #corner #line [271614.762,549311.227,0.0]
        addKnot sh k #corner #line [270834.335,546682.537,0.0]
        addKnot sh k #corner #line [270120.003,544045.453,0.0]
        addKnot sh k #corner #line [269471.426,541401.043,0.0]
        addKnot sh k #corner #line [268888.263,538750.376,0.0]
        addKnot sh k #corner #line [268370.175,536094.522,0.0]
        addKnot sh k #corner #line [267916.820,533434.549,0.0]
        addKnot sh k #corner #line [267527.859,530771.527,0.0]
        addKnot sh k #corner #line [267202.951,528106.525,0.0]
        addKnot sh k #corner #line [266941.755,525440.611,0.0]
        addKnot sh k #corner #line [266743.932,522774.856,0.0]
        addKnot sh k #corner #line [266609.141,520110.328,0.0]
        addKnot sh k #corner #line [266537.042,517448.096,0.0]
        addKnot sh k #corner #line [266527.294,514789.230,0.0]
        addKnot sh k #corner #line [266579.557,512134.798,0.0]
        addKnot sh k #corner #line [266693.490,509485.869,0.0]
        addKnot sh k #corner #line [266868.754,506843.513,0.0]
        addKnot sh k #corner #line [267105.007,504208.799,0.0]
        addKnot sh k #corner #line [267401.910,501582.796,0.0]
        addKnot sh k #corner #line [267759.123,498966.572,0.0]
        addKnot sh k #corner #line [268176.304,496361.198,0.0]
        addKnot sh k #corner #line [268653.113,493767.742,0.0]
        addKnot sh k #corner #line [269189.211,491187.273,0.0]
        addKnot sh k #corner #line [269784.257,488620.860,0.0]
        addKnot sh k #corner #line [270437.910,486069.573,0.0]
        addKnot sh k #corner #line [271149.830,483534.481,0.0]
        addKnot sh k #corner #line [271919.677,481016.652,0.0]
        addKnot sh k #corner #line [272747.110,478517.156,0.0]
        addKnot sh k #corner #line [273631.789,476037.062,0.0]
        addKnot sh k #corner #line [274573.374,473577.439,0.0]
        addKnot sh k #corner #line [275571.524,471139.356,0.0]
        addKnot sh k #corner #line [276625.899,468723.882,0.0]
        addKnot sh k #corner #line [277736.159,466332.087,0.0]
        addKnot sh k #corner #line [278901.963,463965.039,0.0]
        addKnot sh k #corner #line [280122.970,461623.807,0.0]
        addKnot sh k #corner #line [281398.842,459309.461,0.0]
        addKnot sh k #corner #line [282729.237,457023.070,0.0]
        addKnot sh k #corner #line [284113.814,454765.703,0.0]
        addKnot sh k #corner #line [285552.234,452538.428,0.0]
        addKnot sh k #corner #line [287044.156,450342.316,0.0]
        addKnot sh k #corner #line [288589.240,448178.434,0.0]
        addKnot sh k #corner #line [290187.145,446047.853,0.0]
        addKnot sh k #corner #line [291837.532,443951.642,0.0]
        addKnot sh k #corner #line [293540.059,441890.868,0.0]
        addKnot sh k #corner #line [295294.386,439866.603,0.0]
        addKnot sh k #corner #line [297100.174,437879.914,0.0]
        addKnot sh k #corner #line [298957.081,435931.871,0.0]
        addKnot sh k #corner #line [300864.768,434023.542,0.0]
        addKnot sh k #corner #line [302822.893,432155.998,0.0]
        addKnot sh k #corner #line [304831.117,430330.307,0.0]
        addKnot sh k #corner #line [306889.100,428547.537,0.0]
        addKnot sh k #corner #line [308996.500,426808.760,0.0]
        addKnot sh k #corner #line [311152.978,425115.042,0.0]
        addKnot sh k #corner #line [313358.193,423467.454,0.0]
        addKnot sh k #corner #line [315611.805,421867.065,0.0]
        addKnot sh k #corner #line [317913.473,420314.943,0.0]
        addKnot sh k #corner #line [320262.858,418812.158,0.0]
        addKnot sh k #corner #line [322659.618,417359.779,0.0]
        addKnot sh k #corner #line [325103.414,415958.875,0.0]
        updateShape sh
        sh.isHidden = true
        append made sh
      )
      select made
      format "DQ1F preview: created % scene nodes. Existing scene objects untouched.\n" made.count
      messageBox ("DQ-1F Preview created " + (made.count as string) + " separate objects.\n\nClosed footprints: wall/partition/glass/structure/columns.\nDoor and window strokes: 2D guides only (NO holes cut).\nREVIEW_* shapes: HIDDEN, unverified open edges.\nOriginal scene was NOT changed.\nIf overlapping existing WALL, hide one of the two sets.") title:"DQ-1F 3D Preview Created"
    )
  )
)