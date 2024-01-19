1.Ilmin Cho
2.All of the reference from textBook and slides on some Pseudocode
3.
802356174 all
solving puzzle 802356174 with bfs
solving puzzle 802356174 with ucost
solving puzzle 802356174 with greedy-h1
solving puzzle 802356174 with greedy-h2
solving puzzle 802356174 with greedy-h3
solving puzzle 802356174 with astar-h1
solving puzzle 802356174 with astar-h2
solving puzzle 802356174 with astar-h3

flavor      astar-h1    astar-h2    astar-h3         bfs   greedy-h1   greedy-h2   greedy-h3       ucost
--------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------
length            30          30          30          26          36          70          64          30
cost             692         692         692         728         966       2,080       1,610         692
frontier     179,887     179,322      56,032     159,580       4,272         566       1,564     180,220
expanded     176,764     175,552      43,460     140,495       2,698         344       1,050     177,573

This is my test case, and there seems to be an error in the solve part of my heuristic #3 (h3) 
 and the overall greedy algorithm (GreedySolver_solve) in particular.