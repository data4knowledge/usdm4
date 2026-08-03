"""Edge-branch coverage supplements for Expander.

The primary test_expander.py suite exercises the happy paths. These
tests hit the three low-traffic branches:

- _process_si receiving a ScheduleTimelineExit (lines 139-140: no-op)
- _process_si receiving an unrecognised instance type (141-145: logs error)
- _days_condition's broad except branch (157-163: logs exception)
"""

from simple_error_log import Errors

from usdm4.api.schedule_timeline_exit import ScheduleTimelineExit
from usdm4.expander.expander import Expander


def _minimal_expander():
    """An Expander stub that bypasses real study_design/timeline wiring.

    We only need `_errors` populated and a reference to self — the
    methods we exercise never read _study_design or _timeline.
    """
    errors = Errors()
    exp = Expander.__new__(Expander)
    exp._study_design = None
    exp._timeline = None
    exp._errors = errors
    exp._id = 1
    exp._nodes = []
    return exp


def test_process_si_with_schedule_timeline_exit_is_noop():
    exp = _minimal_expander()
    exit_node = ScheduleTimelineExit(id="x", instanceType="ScheduleTimelineExit")
    # Should return without adding nodes or errors.
    exp._process_si(timeline=None, si=exit_node, offset=0)
    assert exp._nodes == []
    assert exp._errors.count() == 0


def test_process_si_with_unknown_instance_type_logs_error():
    exp = _minimal_expander()

    class Bogus:
        def __str__(self):
            return "bogus-instance"

    exp._process_si(timeline=None, si=Bogus(), offset=0)
    assert exp._errors.count() == 1


def test_days_condition_exception_logged_and_returns_none_pair():
    exp = _minimal_expander()
    # re.search raises TypeError on non-string input; caught & logged.
    op, value = exp._days_condition(None)
    assert op is None
    assert value is None
    assert exp._errors.count() == 1
