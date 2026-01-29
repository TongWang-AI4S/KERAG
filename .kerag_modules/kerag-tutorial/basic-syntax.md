# Basic Syntax [@basic-syntax]

## Case Stage 2: Adding Labels and Links to the Knowledge Base [@case-stage-2]

To establish connections between knowledge points, we need to use KERAG's extended syntax. Let's upgrade the `linear-algebra/index.md` now.

**index.md (v2)**
```markdown
# Linear Algebra [@linear-algebra]

Linear algebra is a branch of mathematics concerning vector spaces and linear mappings.

## Definitions [@definition]
Linear algebra mainly deals with vector spaces.

## Matrices [@matrix]
Matrices can be seen as collections of vectors. See (@vector).

## Vectors [@vector]
Vectors are the basic units of linear algebra. Usually represented by (@matrix) for linear transformations.

### See Also
(@matrix): Introduction to matrices
<!-- Reference to nodes in external modules -->
(@/calculus/multivariate::gradient)
```

## Labels [@labels]

Sometimes we need to reference certain sections or content elsewhere. **Labels** provide a way to reference sections.

- **Syntax**: Add `[@label_name]` at the end of the heading line.
- **Purpose**: Specifies the unique identifier suffix for the node.
- **Example**: `## Matrices [@matrix]` has the node label `matrix`.

## Inline Links [@inline-links]

Reference other nodes in the body text to build a knowledge network.

- **Syntax**: `(@node_id)` or `(@label)` (can be abbreviated within the same file).
- **Example**: `See (@vector)` creates a hyperlink pointing to the vector node.

## See Also Blocks [@see-also]

Explicitly listing related knowledge points at the end of a section is not only reader-friendly but also enhances RAG retrieval relevance.

- **Syntax**: Use `See Also` or `参见` as a subsection heading. This section will not be parsed as a section node but as the parent node's See Also block.
- **Format**: One link per line, optionally adding a description `(@node_id): description text`.
