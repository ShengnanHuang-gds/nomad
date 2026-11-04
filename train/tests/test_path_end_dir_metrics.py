import numpy as np
from path_end_dir_metrics import end_dir_err_deg, frac_above

def test_end_dir():
    a = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]])
    b = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    ang, v = end_dir_err_deg(a, b)
    assert v.all()
    assert abs(ang[0]) < 1e-6
    assert abs(ang[1] - 90.0) < 1e-5
    assert abs(ang[2] - 180.0) < 1e-5
    f45, _, n = frac_above(ang, 45.0, v)
    f90, _, _ = frac_above(ang, 90.0, v)
    assert n == 3
    assert abs(f45 - 2/3) < 1e-6
    assert abs(f90 - 1/3) < 1e-6

if __name__ == "__main__":
    test_end_dir()
    print("ok")