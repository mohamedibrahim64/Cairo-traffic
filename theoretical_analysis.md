# Theoretical Analysis - Algorithms, Math, and Complexity

**Course:** Design and Analysis of Algorithms (CSE112)

**Authors:** Mohamed Ibrahim

**Date:** May 2026

---

## Abstract

This report consolidates the theoretical foundations, mathematical models, proofs of correctness, and complexity analysis for all algorithms used in the Cairo Transportation project. It covers shortest-path methods (Dijkstra and A*), minimum spanning tree construction (Kruskal and Prim), dynamic programming formulations (scheduling and resource allocation), and greedy strategies (traffic signals and emergency preemption). It also clarifies the guarantees that hold under the exact implementation choices, including traffic-aware weights and heuristic biasing.

---

## 1. Notation and Model

We model the transportation network as a weighted graph $G=(V,E)$ with $|V|=n$ nodes and $|E|=m$ edges.

- A path $P = (v_0, v_1, ..., v_k)$ has cost $C(P) = \sum_{i=0}^{k-1} w(v_i, v_{i+1})$.
- Shortest-path queries are defined by $(s,t)$ with non-negative edge weights.

### 1.1 Traffic-weighted edge model

In the shortest-path code path, the edge weight is derived from base distance and a congestion penalty. Let $d(e)$ be road distance, $c(e)$ be capacity, and $v_t(e)$ be traffic volume at hour $t$. Define congestion factor:

$$\rho(e,t) = \frac{v_t(e)}{c(e)}$$

The implemented weight function is piecewise:

$$w(e,t) = d(e) \cdot \gamma(\rho(e,t))$$

$$\gamma(\rho) =
\begin{cases}
1.5, & \rho > 0.8 \\
1.2, & 0.5 < \rho \le 0.8 \\
1.0, & \rho \le 0.5
\end{cases}$$

Thus $w(e,t) \ge d(e) \ge 0$ and standard shortest-path assumptions hold for a fixed time snapshot $t$.

### 1.2 Emergency priority scaling (A* module)

In the emergency A* module, edge weights are uniformly scaled by a priority factor $\beta$:

$$w'(e) = \beta \cdot w(e), \quad \beta \in \{1.0, 0.75, 0.5\}$$

Uniform scaling does not change which path is optimal (the argmin is preserved), but it can affect heuristic admissibility unless the heuristic is scaled by the same $\beta$.

---

## 2. Dijkstra's Algorithm (Shortest Path)

### 2.1 Correctness

Dijkstra's algorithm maintains a set $S$ of nodes whose shortest distance from $s$ is finalized. The key invariant is: when a node $u$ is extracted from the priority queue, $\text{dist}[u]$ equals the true shortest-path cost from $s$ to $u$ as long as all edge weights are non-negative.

Proof sketch:
- The algorithm always extracts the smallest tentative distance.
- Any alternative path to $u$ must pass through a node $x$ with tentative distance at least $\text{dist}[u]$.
- Therefore no cheaper path to $u$ exists when it is extracted.

### 2.2 Complexity

- Binary heap: $O((n + m) \log n)$ time, $O(n)$ space.
- With a Fibonacci heap: $O(m + n \log n)$ time (amortized), $O(n)$ space.

Because the graph is sparse, $O(m \log n)$ is the typical bound.

---

## 3. A* Search (Emergency Routing)

### 3.1 Definitions

For each node $x$:

- $g(x)$ is the best-known cost from $s$ to $x$.
- $h(x)$ is a heuristic estimate of cost from $x$ to $t$.
- $f(x) = g(x) + h(x)$.

A* expands nodes in non-decreasing $f$ order.

### 3.2 Heuristics used

Let $(x_1,y_1)$ and $(x_2,y_2)$ be coordinates:

- Euclidean: $h_E = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}$
- Manhattan: $h_M = |x_2-x_1| + |y_2-y_1|$
- Chebyshev: $h_C = \max(|x_2-x_1|, |y_2-y_1|)$
- Traffic-aware: $h_T = h_E \cdot (1 + \tau)$ where $\tau$ is a local traffic penalty

### 3.3 Optimality and admissibility

**Admissibility:** A heuristic is admissible if $h(x) \le h^*(x)$ for all $x$.

**Consistency:** A heuristic is consistent if $h(u) \le w(u,v) + h(v)$ for all edges $(u,v)$.

If $h$ is admissible and costs are non-negative, A* is optimal. If $h$ is consistent, each node needs to be expanded at most once.

**Important implementation note:**

- The traffic-aware heuristic can overestimate actual costs, which breaks admissibility and can lead to suboptimal paths.
- The medical-facility bonus in the implementation modifies $f$ by multiplying it by $0.8$ for certain nodes. This is a biasing heuristic and removes optimality guarantees.
- Emergency priority scaling reduces edge costs by a constant factor $\beta < 1$. If the heuristic is not scaled by $\beta$, admissibility can be violated.

Therefore, strict optimality is guaranteed only when an admissible heuristic is used and no heuristic biasing is applied.

### 3.4 Completeness

For finite graphs with non-negative edge costs, A* is complete as long as $h$ is finite for all nodes. Completeness still holds even if $h$ is inadmissible, but optimality does not.

### 3.5 Complexity

- Binary heap: $O((n + m) \log n)$ time, $O(n)$ space.
- In terms of branching factor $b$ and depth $d$, worst-case node expansions are $O(b^d)$ when the heuristic provides no guidance.

The effective branching factor $b^*$ satisfies:

$$N = 1 + b^* + (b^*)^2 + \dots + (b^*)^d = \frac{(b^*)^{d+1}-1}{b^*-1}$$

Smaller $b^*$ indicates a more informative heuristic.

---

## 4. Heuristic Theory (What can be asked)

### 4.1 Dominance

If two admissible heuristics satisfy $h_1(x) \ge h_2(x)$ for all $x$, then $h_1$ dominates $h_2$ and A* with $h_1$ expands no more nodes than A* with $h_2$.

### 4.2 Relation to Dijkstra

A* with $h \equiv 0$ is identical to Dijkstra, so all Dijkstra guarantees are a special case of A*.

### 4.3 Tie-breaking

Stable tie-breaking does not change correctness. It only affects which optimal path is returned when multiple shortest paths exist.

---

## 5. Minimum Spanning Tree (Kruskal and Prim)

### 5.1 Kruskal (with critical facility bias)

Kruskal sorts edges and adds them if they do not create a cycle (Union-Find). The cut property guarantees correctness: the lightest edge crossing any cut is safe to include.

The implementation modifies edge weights for critical facilities. The algorithm therefore computes the MST of the modified weight function, which intentionally biases connectivity toward critical nodes. This is not necessarily the MST of the original graph.

Complexity:

- Sorting: $O(m \log m)$
- Union-Find operations: $O(m \alpha(n))$ (almost constant)
- Total: $O(m \log m)$ time, $O(n + m)$ space

### 5.2 Prim (alternative)

Prim grows a tree from a start node using a priority queue of boundary edges.

- Binary heap: $O(m \log n)$ time, $O(n + m)$ space

---

## 6. Dynamic Programming Formulations

### 6.1 Bus scheduling

Let $i$ be the number of buses used and $h$ be total hours. The recurrence:

$$dp[i][h] = \max\left(dp[i-1][h], \max_{r: t_r \le h}\{dp[i-1][h-t_r] + demand_r\}\right)$$

Time complexity in the implementation is $O(B \cdot H \cdot R)$ where $B$ is number of buses, $H$ is max hours, and $R$ is number of routes.

### 6.2 Road maintenance (knapsack)

For each road $i$ with improvement value $val_i$ and cost $cost_i$:

$$dp[i][b] = \max(dp[i-1][b], dp[i-1][b-cost_i] + val_i)$$

Complexity: $O(N \cdot B)$ time and space, where $B$ is budget.

### 6.3 Metro-bus integration

Let $m$ be metro lines and $b$ be bus routes. The recurrence:

$$dp[i][j] = \max(dp[i][j-1], dp[i-1][j-1] + transfer(i,j))$$

Complexity: $O(m \cdot b)$ time and space.

### 6.4 Memoized route planning

The memoized depth-first planner explores paths with a visited set. Without memoization over subsets, the worst-case time is exponential in $n$ (similar to DFS on all simple paths). It is suitable only for small graphs or constrained time budgets.

---

## 7. Greedy Algorithms and Guarantees

### 7.1 Traffic signal optimization

The greedy policy assigns green time proportional to observed flow. This is locally optimal per intersection but has no global optimality guarantee for network-wide delay.

Let $I$ be the number of intersections and $R$ be the number of roads. The observed complexity is approximately $O(I \cdot R)$ for flow extraction plus $O(I \cdot D)$ for direction allocation, where $D$ is the average degree.

### 7.2 Emergency vehicle preemption

Emergencies are sorted by priority, then each route is granted a clear corridor. Complexity is $O(K \log K + \sum |P_k|)$ where $K$ is the number of active emergencies and $|P_k|$ is path length.

### 7.3 Greedy route recommendation

At each step, the neighbor with minimum local congestion score is chosen. This can be suboptimal because greedy choices ignore downstream structure. The implementation uses a Dijkstra fallback if greedy gets stuck, ensuring completeness.

Worst-case complexity: $O(L \cdot d_{avg})$ for the greedy pass plus $O(m \log n)$ for the fallback shortest-path.

---

## 8. Complexity Summary (Big-O)

| Algorithm | Time | Space | Optimality |
| --- | --- | --- | --- |
| Dijkstra (binary heap) | $O((n+m) \log n)$ | $O(n)$ | Yes, for $w \ge 0$ |
| A* (binary heap) | $O((n+m) \log n)$ worst-case | $O(n)$ | Yes, if $h$ admissible and no bias |
| Kruskal | $O(m \log m)$ | $O(n+m)$ | Yes, for given weights |
| Prim (binary heap) | $O(m \log n)$ | $O(n+m)$ | Yes, for given weights |
| Bus scheduling DP | $O(B \cdot H \cdot R)$ | $O(B \cdot H)$ | Yes, optimal for model |
| Road maintenance DP | $O(N \cdot B)$ | $O(N \cdot B)$ | Yes, optimal for model |
| Integration DP | $O(m \cdot b)$ | $O(m \cdot b)$ | Yes, optimal for model |
| Greedy signals | $O(I \cdot R)$ | $O(I)$ | No global guarantee |
| Greedy route + fallback | $O(L \cdot d_{avg} + m \log n)$ | $O(n)$ | Complete; optimal only with fallback |

---

## 9. Assumptions and Limitations

- Shortest-path results are computed for a fixed traffic snapshot. The algorithm does not solve the full time-dependent shortest-path problem.
- Heuristic biasing (traffic-aware heuristic and facility bonus) trades optimality for speed and prioritization.
- Critical-facility weighting in MST changes the optimization objective; it is a policy choice.

---

## 10. References

1. Hart, P., Nilsson, N., and Raphael, B. (1968). A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics.
2. Cormen, T., Leiserson, C., Rivest, R., and Stein, C. (2009). Introduction to Algorithms.
3. Russell, S., and Norvig, P. (2016). Artificial Intelligence: A Modern Approach.
4. Stentz, A. (1994). Optimal and efficient path planning for partially-known environments. ICRA.


