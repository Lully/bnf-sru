# coding: utf-8
"""
tests sur le retournement au lieu pour les vedettes pré-construites

Specs :
N°
1. a x --> a y
2. a g x --> a y g
3. a o g x g --> a y o g g
4. a g g x g --> a y g g g
5. a x y --> a y y
6. a x g --> a y g
7. a x z --> a y z
8. a x1 x2 --> a y x
Si Forces armées ou colonies :
$a {Sujet 1} $y {Lieu} $x {Sujet 2}
Sinon
$a {Sujet 2} $y {Lieu} $x {Sujet 1}

9. a g x1 x2 --> a y g x1
10. a x1 x2 g --> a y x1 g
11. a o g g x g --> a y o g g g
12. a z g x --> a y z g
13. a g x g --> a y g g
14. a x g g --> a y g g 
15. a o g x --> a y o g
16. a g x z --> a y g z 
17. a g g x z --> a y g g z
18. a x z g --> a y z g
"""

