# 矩阵-向量乘法 [@matvec]

矩阵-向量乘法将矩阵与向量相乘，产生另一个向量。

## 定义

给定矩阵 $A \in \mathbb{R}^{m \times n}$ 和向量 $x \in \mathbb{R}^n$，乘积 $Ax$ 是一个向量 $y \in \mathbb{R}^m$，其中：

$$y_i = \sum_{j=1}^{n} a_{ij} x_j$$

## 示例

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

## 应用
- 线性变换
- 神经网络前向传播
- 求解线性方程组
