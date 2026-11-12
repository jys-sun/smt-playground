# Assigning peer reviews with backtracking and Z3

I had 21 project groups in a class and needed to assign peer reviews across three days of presentations. The presentation order was already fixed. I used the assignment as a way to learn Z3: first I wrote a search in Python, then I worked out how to give the same problem to a solver.

| Day | Presentation order |
| --- | --- |
| 1 | Group1 through Group7 |
| 2 | Group8 through Group14 |
| 3 | Group15 through Group21 |

A valid schedule follows four rules:

1. Every group gives **exactly two reviews per day**, including on the day it presents.
2. Every talk receives **exactly six reviews from different groups**. Each day has 21 × 2 = 42 reviews to split evenly among seven talks.
3. A presenting group skips its own talk and the talks immediately before and after it on the same day. On Day 1, Group4 cannot review Group3, Group4, or Group5.
4. No group reviews two consecutive talks on the same day. On Day 1, Group8 can review Group1 and Group3, but it cannot review Group1 and Group2.

All four rules apply within a day, so we can solve each day independently. Any schedule that satisfies the rules is a valid solution.

## Solve it with backtracking

For each group, use a list to store every legal pair of talks. For a presenter, first remove its own talk and its neighbors. For every group, discard pairs of consecutive talks. Choosing a pair then gives that group exactly two legal reviews.

Keep an array of seven counters, one for each talk, initialized to six available review slots. Visit the groups one at a time, starting with those that have the fewest legal pairs. Try a pair if both talks have slots left, decrement their counters, and move on. If the rest of the groups cannot be assigned, go back and try a different pair. When all groups are assigned and all counters are zero, the schedule is complete. If every choice fails, there is no valid schedule.

The implementation remembers each search state by the next group and the tuple of remaining slots. Earlier choices only affect those slot counts, so the same state does not need to be searched twice.

## Express it as an SMT problem

SMT stands for *satisfiability modulo theories*. An SMT solver checks whether logical constraints can all hold together, including constraints involving theories such as integer arithmetic. If they can, the solver can return a *model*: values for the variables that satisfy every constraint.

What does one decision look like? For a given talk and a given group, we need to decide whether that group reviews the talk. Put the seven talks in rows and the 21 groups in columns. We need all 21 columns because everyone reviews each day, including groups that are not presenting. That gives us a 7 × 21 matrix of Boolean variables.

| Scheduling rule | Constraint in Z3 |
| --- | --- |
| Each group gives two reviews | Exactly two true cells per column. |
| Each talk receives six reviews | Exactly six true cells per row. |
| Presenters skip their own and neighboring talks | Set each forbidden cell to false. |
| No group reviews consecutive talks | For each column, forbid adjacent cells from both being true with `Or(Not(a), Not(b))`. |

The counts can be written as integer sums by counting true as 1 and false as 0. The Python code uses Z3's `PbEq` to express those counts directly, with weight 1 for each Boolean. Call `solver.check()`. If Z3 returns `sat`, read the true cells from its model to get the reviewers for each talk. If it returns `unsat`, no schedule satisfies the constraints. With backtracking we wrote the search ourselves. With Z3 we describe the rules and let the solver search.

## Run both solutions

From the repository root, run the [Python script](assign_reviews.py). Backtracking uses only the Python standard library (Python 3.9 or later).

```sh
python assign_reviews.py --method backtracking
python -m pip install -r requirements.txt
python assign_reviews.py --method z3
```

Both methods print JSON and may find different valid schedules. Add `--output-dir review_output` to write `day1.json`, `day2.json`, and `day3.json` instead. Each schedule maps a presenting group to its six reviewers.

The [notebook walkthrough](z3_practice_assigning_reviews.ipynb) includes a worked example, formulas for all four constraints, and the full code for both solutions. It runs on its own. Install JupyterLab in the same Python environment as Z3 to follow along.

```sh
python -m pip install jupyterlab
jupyter lab z3_practice_assigning_reviews.ipynb
```
