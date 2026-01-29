# 矩阵-矩阵乘法 [@matmul]

矩阵-矩阵乘法将两个矩阵相乘，产生第三个矩阵。

## 定义

给定矩阵 $A \in \mathbb{R}^{m \times n}$ 和 $B \in \mathbb{R}^{n \times p}$，乘积 $AB$ 是一个矩阵 $C \in \mathbb{R}^{m \times p}$，其中：

$$c_{ij} = \sum_{k=1}^{n} a_{ik} b_{kj}$$

## 示例

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

## 复杂度

朴素的矩阵乘法对于 $n \times n$ 矩阵具有 $O(n^3)$ 的时间复杂度。

## 参见
(@matvec::matvec): 矩阵-向量乘法（一种特殊情况）
