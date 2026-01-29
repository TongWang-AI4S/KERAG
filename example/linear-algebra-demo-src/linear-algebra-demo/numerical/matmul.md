# Matrix-Matrix Multiplication [@matmul]

Matrix-matrix multiplication combines two matrices to produce a third matrix.

## Definition

Given matrices $A \in \mathbb{R}^{m \times n}$ and $B \in \mathbb{R}^{n \times p}$, the product $AB$ is a matrix $C \in \mathbb{R}^{m \times p}$ where:

$$c_{ij} = \sum_{k=1}^{n} a_{ik} b_{kj}$$

## Example

$$
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
\begin{bmatrix}
5 & 6 \\
7 & 8
\end{bmatrix}
=
\begin{bmatrix}
1 \cdot 5 + 2 \cdot 7 & 1 \cdot 6 + 2 \cdot 8 \\
3 \cdot 5 + 4 \cdot 7 & 3 \cdot 6 + 4 \cdot 8
\end{bmatrix}
=
\begin{bmatrix}
19 & 22 \\
43 & 50
\end{bmatrix}
$$

## Complexity

Naive matrix multiplication has $O(n^3)$ time complexity for $n \times n$ matrices.

## See Also
(@matvec::matvec): Matrix-vector multiplication (a special case)
