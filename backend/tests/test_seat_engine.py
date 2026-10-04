from app.services.seat_engine import (SeatAssign, chebyshev, find_violations, manhattan,
                                      neighbors8, place_candidates)

def test_manhattan():
    assert manhattan((0, 0), (2, 1)) == 3

def test_chebyshev_diagonal_is_one():
    assert chebyshev((0, 0), (1, 1)) == 1
    assert chebyshev((0, 0), (0, 1)) == 1
    assert chebyshev((0, 0), (1, 2)) == 2

def test_neighbors8_includes_diagonals():
    assert set(neighbors8(1, 1, 3, 3)) == {
        (0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}

def test_min_distance_placement():
    cands = [{"id": i, "name": f"C{i}", "ticket_no": f"T{i}", "paper_id": 1 + (i % 2)} for i in range(4)]
    assigns, unplaced = place_candidates(4, 4, 2, cands)
    assert len(assigns) + len(unplaced) == 4
    for i, a in enumerate(assigns):
        for b in assigns[i+1:]:
            assert manhattan((a.row, a.col), (b.row, b.col)) >= 2

def test_same_paper_not_8adjacent_in_result():
    # Force same paper — engine must avoid 8-neighborhood, diagonals included
    cands = [
        {"id": 1, "name": "A", "ticket_no": "T1", "paper_id": 1},
        {"id": 2, "name": "B", "ticket_no": "T2", "paper_id": 1},
        {"id": 3, "name": "C", "ticket_no": "T3", "paper_id": 2},
    ]
    assigns, _ = place_candidates(3, 3, 1, cands)
    viols = find_violations(3, 3, 1, assigns)
    assert not any(v.kind == "same_paper_adjacent8" for v in viols)

def test_passing_only_one_rule_still_fails():
    # 2x2, min_dist 2: (1,1) passes manhattan vs (0,0) but is a same-set diagonal;
    # (0,1)/(1,0) pass nothing. Second same-set candidate must stay unplaced.
    cands = [
        {"id": 1, "name": "A", "ticket_no": "T1", "paper_id": 1},
        {"id": 2, "name": "B", "ticket_no": "T2", "paper_id": 1},
    ]
    assigns, unplaced = place_candidates(2, 2, 2, cands)
    assert len(assigns) == 1
    assert [u["id"] for u in unplaced] == [2]

def test_diagonal_same_set_yields_single_8neigh_violation():
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 1, 1),
    ]
    viols = find_violations(2, 2, 1, assigns)
    adj = [v for v in viols if v.kind.startswith("same_paper")]
    assert len(adj) == 1
    assert adj[0].kind == "same_paper_adjacent8"
    assert "八邻" in adj[0].detail

def test_orthogonal_same_set_not_double_counted():
    # 4-neigh is inside 8-neigh: exactly one entry, the 8-neigh one — never two hanging together
    assigns = [
        SeatAssign(1, "A", "T1", 1, 0, 0),
        SeatAssign(2, "B", "T2", 1, 0, 1),
    ]
    viols = find_violations(2, 2, 2, assigns)
    adj = [v for v in viols if v.kind.startswith("same_paper")]
    assert len(adj) == 1
    assert adj[0].kind == "same_paper_adjacent8"
    assert any(v.kind == "distance" for v in viols)

def test_seed_same_set_never_diagonal_together():
    # Seed-shaped data: 12 candidates over 3 paper sets, 5x6 hall, min_manhattan 2.
    # Two same-set candidates at diagonal seats must not coexist in the graph.
    names = ["陈一", "李二", "张三", "赵四", "钱五", "孙六", "周七", "吴八", "郑九", "王十", "冯十一", "陈十二"]
    cands = [{"id": i + 1, "name": n, "ticket_no": f"T{2026001 + i}", "paper_id": 1 + (i % 3)}
             for i, n in enumerate(names)]
    assigns, _ = place_candidates(5, 6, 2, cands)
    for i, a in enumerate(assigns):
        for b in assigns[i + 1:]:
            if a.paper_id == b.paper_id:
                assert chebyshev((a.row, a.col), (b.row, b.col)) > 1
    assert not any(v.kind == "same_paper_adjacent8"
                   for v in find_violations(5, 6, 2, assigns))
