"""Verify S[h,c] indexing, mutual pairs, and draw coordinates on a small asymmetric matrix."""

import numpy as np

from turn_match_viz import (
    curr_to_hist_nn,
    hist_to_curr_nn,
    mutual_consistent_pairs,
    patch_center_xy,
)


def test_asymmetric_mutual_pairs_and_cos():
    # 4 hist x 5 curr — non-square, non-symmetric
    sim = np.array(
        [
            [0.1, 0.9, 0.2, 0.0, 0.0],  # h0 -> c1
            [0.3, 0.2, 0.8, 0.1, 0.0],  # h1 -> c2
            [0.0, 0.4, 0.1, 0.95, 0.2],  # h2 -> c3
            [0.5, 0.1, 0.0, 0.2, 0.7],  # h3 -> c0
        ],
        dtype=np.float32,
    )
    h2c = hist_to_curr_nn(sim)
    c2h = curr_to_hist_nn(sim)
    assert h2c.tolist() == [1, 2, 3, 4]
    assert c2h.tolist() == [3, 0, 1, 2, 3]

    pairs = mutual_consistent_pairs(sim)
    assert set(pairs) == {(0, 1, sim[0, 1]), (1, 2, sim[1, 2]), (2, 3, sim[2, 3]), (3, 4, sim[3, 4])}
    for h, c, cos in pairs:
        assert int(hist_to_curr_nn(sim)[h]) == c
        assert int(curr_to_hist_nn(sim)[c]) == h
        assert cos == float(sim[h, c])



def test_draw_endpoints_left_hist_right_curr():
    w, h = 224, 168
    h_idx, c_idx = 10, 25
    x_h, y_h = patch_center_xy(h_idx, w, h, x_offset=0.0)
    x_c, y_c = patch_center_xy(c_idx, w, h, x_offset=w)
    assert 0 < x_h < w
    assert w < x_c < 2 * w
    assert x_c - x_h >= w * 0.5


if __name__ == "__main__":
    test_asymmetric_mutual_pairs_and_cos()
    test_draw_endpoints_left_hist_right_curr()
    print("ok")
