"""Export house_run_*/N.jpg into NoMaD deployment topomap layout.



Official deploy expects:

  visualnav-transformer/deployment/topomaps/images/<name>/0.png, 1.png, ...



Run from repo root (or anywhere):

  python gazebo_sim/export_topomap.py --run house_run_00 --name house_00

"""



from __future__ import annotations



import argparse

import os

import shutil





def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--run", default="house_run_00", help="Folder under gazebo_sim/")

    parser.add_argument("--name", default="", help="Topomap folder name (default: run id)")

    parser.add_argument(

        "--root",

        default=os.path.join(os.path.dirname(os.path.abspath(__file__))),

        help="gazebo_sim directory",

    )

    parser.add_argument(

        "--deploy-images",

        default=os.path.normpath(

            os.path.join(

                os.path.dirname(os.path.abspath(__file__)),

                "..",

                "visualnav-transformer",

                "deployment",

                "topomaps",

                "images",

            )

        ),

        help="deployment topomaps/images path",

    )

    parser.add_argument("--stride", type=int, default=1, help="Keep every N-th frame")

    parser.add_argument("--ext", default="png", choices=("png", "jpg"))

    args = parser.parse_args()



    src = os.path.join(args.root, args.run)

    if not os.path.isdir(src):

        raise SystemExit(f"missing {src}")

    name = args.name or args.run

    dst = os.path.join(args.deploy_images, name)

    os.makedirs(dst, exist_ok=True)

    for f in os.listdir(dst):

        p = os.path.join(dst, f)

        if os.path.isfile(p):

            os.unlink(p)



    jpgs = sorted(

        int(f[:-4]) for f in os.listdir(src) if f.endswith(".jpg") and f[:-4].isdigit()

    )

    out_i = 0

    for t in jpgs[:: max(1, args.stride)]:

        from PIL import Image



        im = Image.open(os.path.join(src, f"{t}.jpg")).convert("RGB")

        out_path = os.path.join(dst, f"{out_i}.{args.ext}")

        im.save(out_path, quality=92)

        out_i += 1



    print(f"topomap {name}: {out_i} nodes -> {dst}")

    print(f"deploy: goal_node=-1 uses node {out_i - 1} as final goal")





if __name__ == "__main__":

    main()