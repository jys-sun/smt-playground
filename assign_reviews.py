"""Find a feasible peer review schedule for three presentation days."""

import argparse
import json
from functools import cache
from itertools import combinations
from pathlib import Path

GROUPS = [f"Group{i}" for i in range(1, 22)]
PRESENTATION_DAYS = [GROUPS[start:start + 7] for start in (0, 7, 14)]
REVIEWS_PER_GROUP = 2
REVIEWS_PER_TALK = 6


def solve_with_backtracking(presenters, reviewers, forbidden_reviews=()):
    """Assign review pairs, optionally excluding (reviewer, presenter) pairs."""
    forbidden = set(forbidden_reviews)
    positions = {talk: i for i, talk in enumerate(presenters)}
    choices = {}
    for group in reviewers:
        own_talk = positions.get(group)
        eligible = [
            i for i in range(len(presenters))
            if (group, presenters[i]) not in forbidden
            and (own_talk is None or abs(i - own_talk) > 1)
        ]
        choices[group] = [(a, b) for a, b in combinations(eligible, 2) if b - a > 1]

    # Try the groups with the fewest choices first.
    ordered_groups = sorted(reviewers, key=lambda group: len(choices[group]))

    @cache
    def search(group_index, remaining):
        if group_index == len(ordered_groups):
            return () if not any(remaining) else None

        group = ordered_groups[group_index]
        # Prefer talks that still need the most reviews.
        pairs = sorted(choices[group], key=lambda pair: -sum(remaining[i] for i in pair))
        for a, b in pairs:
            if remaining[a] == 0 or remaining[b] == 0:
                continue
            next_remaining = list(remaining)
            next_remaining[a] -= 1
            next_remaining[b] -= 1
            rest = search(group_index + 1, tuple(next_remaining))
            if rest is not None:
                return ((a, b),) + rest
        return None

    pairs = search(0, (REVIEWS_PER_TALK,) * len(presenters))
    if pairs is None:
        raise RuntimeError("the constraints have no solution")

    assignments = {talk: [] for talk in presenters}
    for group, pair in zip(ordered_groups, pairs):
        for i in pair:
            assignments[presenters[i]].append(group)
    return assignments


def build_problem(presenters, reviewers):
    """Return a Z3 solver and a matrix indexed by talk, then reviewer."""
    from z3 import Bool, Not, Or, PbEq, Solver

    review = [
        [Bool(f"review_{talk}_{group}") for group in reviewers]
        for talk in presenters
    ]
    solver = Solver()

    # Rule 1. Each reviewer column has exactly two true cells.
    for column in zip(*review):
        solver.add(PbEq([(entry, 1) for entry in column], REVIEWS_PER_GROUP))

    # Rule 2. Each talk row has exactly six true cells.
    for row in review:
        solver.add(PbEq([(entry, 1) for entry in row], REVIEWS_PER_TALK))

    # Rule 3. Block the presenting group and its neighbors as reviewers.
    for i, row in enumerate(review):
        blocked = presenters[max(0, i - 1):i + 2]
        for group, entry in zip(reviewers, row):
            if group in blocked:
                solver.add(Not(entry))

    # Rule 4. One reviewer cannot take both talks in an adjacent pair.
    for earlier_row, later_row in zip(review, review[1:]):
        for earlier_review, later_review in zip(earlier_row, later_row):
            solver.add(Or(Not(earlier_review), Not(later_review)))

    return solver, review


def read_assignments(model, review, presenters, reviewers):
    """Convert the true cells in a satisfying model to reviewer names."""
    from z3 import is_true

    return {
        talk: [
            group
            for group, entry in zip(reviewers, row)
            if is_true(model.eval(entry))
        ]
        for talk, row in zip(presenters, review)
    }


def solve_with_z3(presenters, reviewers):
    """Build the constraints, ask Z3 for a model, and decode it."""
    from z3 import sat, unsat

    solver, review = build_problem(presenters, reviewers)
    status = solver.check()
    if status == unsat:
        raise RuntimeError("the constraints have no solution")
    if status != sat:
        raise RuntimeError(f"Z3 returned {status}: {solver.reason_unknown()}")
    return read_assignments(solver.model(), review, presenters, reviewers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--method",
        choices=("z3", "backtracking"),
        default="z3",
        help="Choose a solution method (default: z3).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write day1.json through day3.json here. By default, print the schedule.",
    )
    args = parser.parse_args()

    solve = solve_with_backtracking if args.method == "backtracking" else solve_with_z3
    schedules = {}
    for day, presenters in enumerate(PRESENTATION_DAYS, 1):
        try:
            schedules[f"day{day}"] = solve(presenters, GROUPS)
        except RuntimeError as error:
            parser.exit(1, f"Day {day}: {error}\n")

    if args.output_dir is None:
        print(json.dumps(schedules, indent=2))
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for day, assignments in schedules.items():
            path = args.output_dir / f"{day}.json"
            path.write_text(json.dumps(assignments, indent=2) + "\n", encoding="utf-8")
            print(path)


if __name__ == "__main__":
    main()
