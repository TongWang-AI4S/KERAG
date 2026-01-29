# Matrix-Vector Multiplication [@matvec]

Matrix-vector multiplication combines a matrix with a vector to produce another vector.

## Definition

Given a matrix $A \in \mathbb{R}^{m \times n}$ and a vector $x \in \mathbb{R}^n$, the product $Ax$ is a vector $y \in \mathbb{R}^m$ where:

$$y_i = \sum_{j=1}^{n} a_{ij} x_j$$

## Example

$$
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
\begin{bmatrix}
3 \\
4
\end{bmatrix}
=
\begin{bmatrix}
1 \cdot 3 + 2 \cdot 4 \\
3 \cdot 3 + 4 \cdot 4
\end{bmatrix}
=
\begin{bmatrix}
11 \\
25
\end{bmatrix}
$$

## Applications
- Linear transformations
- Neural network forward passes
- Solving linear systems
