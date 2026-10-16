---
title: "Coloured metalibraries"
lang: en
ru: /ru/math/libraries/
description: "R. Mikhailov's lecture “Coloured metalibraries. The mind of space” (2016) and our recomputation of its rapacious spectral sequence for the 3-torsion of the homotopy groups of S²."
---

# Coloured metalibraries

[Mathematics](/math/) · [Back to main page](/)

In the first lecture of his course “Coloured metalibraries. The mind of space”
(Chebyshev Laboratory, St. Petersburg State University, 2 September 2016,
[YouTube](https://www.youtube.com/watch?v=yE49kR_RA7o), in Russian) R. Mikhailov
describes a “rapacious spectral sequence”: take the E² page of a coloured
metalibrary and let it “eat itself as fast as possible, constrained only by
colour”. For the 3-torsion of the homotopy groups πₙ(S²) the lecture
predicts that π₄₈ has none and that every πₙ with 49 ≤ n ≤ 149 has some. In our
recomputation the metalibrary is a set of admissible words in the letters λᵢ
and μᵢ of the mod-3 lambda algebra of Ivanov, Mikhailov and Wu, and the colour
of a word is the number of μ's in it.

We computed the coloured E² page up to π₁₅₀. The colour turned out to be the
number of Bocksteins (the Q-weight) in the unstable Ext; this was checked cell
by cell against a direct computation in the lambda algebra up to π₇₅, and
selectively up to π₈₅. The rapacious rule with colour +1 agrees with Toda's
table for all n ≤ 48, including π₄₄ = 0, and reproduces the predictions of the
lecture. Beyond π₄₈ it disagrees with Toda's 2003 table in nineteen groups, from
π₄₉ to π₈₀, and leaves more classes in every one of them.

For the first five disagreements — π₄₉, π₅₀, π₅₁, π₅₉ and π₆₀ — the result does
not rest on trust in our program. The computation writes certificates; a
checker written from scratch, which does not use the code that computed E²,
verifies them; and Lean 4, a third independent implementation of the same
algebra, proves the number of surviving classes as a theorem by computation
(`native_decide`, that is, trusting the Lean compiler). What this does not
cover: Toda's values are quoted, not checked, and the rule itself is our reading
of the lecture.

Everything else — the comparison stem by stem, the E² classes, the
differentials, the method and the data — is on the site of the recomputation:
**[Coloured metalibrary: a recomputation](https://ispacex.github.io/metalibrary/)**.
