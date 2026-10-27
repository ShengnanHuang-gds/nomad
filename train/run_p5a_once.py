import csv, json, os
import cv2  # noqa: F401
import numpy as np
from adaptive_blend import angle_between_deg
from eval_testtime import DINO_TEST_PREDICTIONS
ORACLE="logs/revalidation/oracle_factorial/per_frame.npz"
ATTR="logs/revalidation/wp_oracle_attribution/attribution_per_frame.npz"
WP_CACHE="logs/nomad_d/nomad_dino_wp_hist_ctx2_2026_10_24_20_53_44/eval_waypoint/locked_per_frame.npz"
OUT="logs/revalidation/p5a_kappa_miscalibration"
def cohen_d(x,y):
 x,y=np.asarray(x,float),np.asarray(y,float)
 if len(x)<2 or len(y)<2: return float("nan")
 vx,vy=x.var(ddof=1),y.var(ddof=1)
 p=np.sqrt(((len(x)-1)*vx+(len(y)-1)*vy)/max(len(x)+len(y)-2,1))
 return float((x.mean()-y.mean())/p) if p>1e-9 else 0.0
def pearson(a,b):
 a,b=np.asarray(a,float),np.asarray(b,float)
 return float(np.corrcoef(a,b)[0,1]) if a.std()>1e-9 and b.std()>1e-9 else float("nan")
os.makedirs(OUT,exist_ok=True)
o,a=np.load(ORACLE),np.load(ATTR)
pred=dict(np.load(DINO_TEST_PREDICTIONS))
fm=pred["group"]=="20-40"
order=np.argsort(pred["frame_index"][fm],kind="stable")
take=lambda k: pred[k][fm][order]
ade_b=o["ade_Db_d_blend"].astype(float)
ade_g=o["ade_Db_dg_pred"].astype(float)
gk=take("dino_kappa").astype(float)
wk=a["wp_kappa"].astype(float)
gd=take("dino_dir").astype(np.float32)
wd=np.load(WP_CACHE)["wp_dir"].astype(np.float32)
rw=wk/np.maximum(wk+gk,1e-6)
th=angle_between_deg(gd,wd).astype(float)
wpe=a["wp_bearing_err_deg"].astype(float)
d_ade=ade_b-ade_g
du=100*(ade_g-ade_b)
harm = d_ade > 0
benef = d_ade < 0
h45=wpe>=45
lines=["=== P5a (locked n=%d) ==="%len(ade_b),"beneficial %d harmful %d mean du %+.2fcm"%(benef.sum(),harm.sum(),du.mean()),
 "pearson wp_err,du %+.3f rw %+.3f theta %+.3f"%(pearson(wpe,du),pearson(rw,du),pearson(th,du)),
 "Cohen d harm vs ben: rw %+.2f theta %+.2f wp_err %+.2f kw %+.2f kg %+.2f"%(cohen_d(rw[harm],rw[benef]),cohen_d(th[harm],th[benef]),cohen_d(wpe[harm],wpe[benef]),cohen_d(wk[harm],wk[benef]),cohen_d(gk[harm],gk[benef]))]
for lab,m in [("benef",benef),("harm",harm),("hard45",h45),("h45&harm",h45&harm)]:
 if m.sum()<3: continue
 lines.append(" %s n=%d rw_med=%.3f th_med=%.1f wpe_med=%.1f du %+.2f"%(lab,m.sum(),np.median(rw[m]),np.median(th[m]),np.median(wpe[m]),du[m].mean()))
for wl,wm in [("wp<45",wpe<45),("wp>=45",wpe>=45)]:
 for ol,om in [("ben",benef),("harm",harm)]:
  m=wm&om
  if m.sum(): lines.append(" %s %s n=%d rw=%.3f du %+.2f"%(wl,ol,m.sum(),np.median(rw[m]),du[m].mean()))
drw=cohen_d(rw[harm],rw[benef])
lines.append("Hypothesis: "+("rw high on harm => miscalib" if drw>0.15 else "rw not higher on harm => bad WP dir dominates"))
text="\n".join(lines)+"\n"
print(text)
open(os.path.join(OUT,"summary.txt"),"w",encoding="utf-8").write(text)
json.dump({"cohen_d_rw":drw},open(os.path.join(OUT,"summary.json"),"w"),indent=2)
np.savez_compressed(os.path.join(OUT,"per_frame.npz"),rw=rw,theta=th,wp_err=wpe,delta_use=du,harmful=harm,hard45=h45)
print("Saved",os.path.abspath(OUT))