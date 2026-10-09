"""The drawing rules of the diagram that do not need Qt (core/routing.py)."""

from harness_design_studio.core import routing
from harness_design_studio.core.samples import new_project, sat15


def test_a_link_leaves_on_the_edge_that_faces_the_other_end() -> None:
    assert routing.side_toward(1, 2, "right") == "right"
    assert routing.side_toward(2, 1, "right") == "left"
    assert routing.side_toward(0, 3, "left") == "right"
    assert routing.side_toward(3, 0, "right") == "left"
    assert routing.side_toward(2, 2, "left") == "left"  # inside a lane: the default edge
    assert routing.side_toward(2, 2, "right") == "right"


def test_a_link_inside_a_lane_leaves_away_from_the_middle_when_there_is_room() -> None:
    assert routing.same_lane_side(1, 4, "right") == "left"  # the gap on its left is free
    assert routing.same_lane_side(2, 4, "left") == "right"
    assert routing.same_lane_side(0, 4, "right") == "right"  # nothing on its left: stay
    assert routing.same_lane_side(3, 4, "left") == "left"
    assert routing.same_lane_side(0, 1, "right") == "right"


def test_links_inside_a_lane_bulge_the_more_the_longer_they_are() -> None:
    assert routing.loop_reach(0) == 36.0 and routing.loop_reach(100) < routing.loop_reach(400)
    assert (
        routing.loop_reach(-400) == routing.loop_reach(400) and routing.loop_reach(10_000) == 150.0
    )


def test_the_turning_point_of_a_link_stays_inside_its_way_and_spreads() -> None:
    shares = [routing.channel_share(k) for k in range(40)]
    assert all(0.25 <= x <= 0.75 for x in shares)
    assert len({round(x, 3) for x in shares}) == 40
    assert shares == [routing.channel_share(k) for k in range(40)]  # deterministic


def test_links_are_ordered_by_the_height_of_their_other_end() -> None:
    links = [("IF-3", 300.0), ("IF-1", 500.0), ("IF-2", 300.0), ("IF-4", 40.0)]
    assert routing.order_links(links) == ["IF-4", "IF-2", "IF-3", "IF-1"]
    assert routing.order_links([]) == []


def test_focus_of_an_interface_and_of_a_unit() -> None:
    p = sat15()
    iid = sorted(p.interfaces)[0]
    links, units = routing.focus(p, "interface", iid)
    assert links == {iid} and units == {e.unit_id for e in p.interfaces[iid].endpoints}
    uid = sorted(p.units)[0]
    links, units = routing.focus(p, "unit", uid)
    assert links and uid in units
    assert all(any(e.unit_id == uid for e in p.interfaces[i].endpoints) for i in links)
    assert routing.focus(p, "unit", "NOPE") == (set(), set())
    assert routing.focus(p, "interface", "NOPE") == (set(), set())
    assert routing.focus(new_project(), "unit", "X") == (set(), set())


def test_partner_is_the_unit_at_the_other_end() -> None:
    p = sat15()
    i = p.interfaces[sorted(p.interfaces)[0]]
    a, b = (e.unit_id for e in i.endpoints)
    assert routing.partner(p, i.id, a) == b and routing.partner(p, i.id, b) == a
    assert routing.partner(p, "NOPE", a) is None
