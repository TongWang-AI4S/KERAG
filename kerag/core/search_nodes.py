"""NodeSearcher for searching nodes in the knowledge graph."""

import re
from typing import Dict, List, Optional, Any, Union

from .knowledge_manager import KnowledgeManager

class NodeSearcher:
    """Searcher for finding nodes based on text matching."""

    def __init__(self, knowledge_manager: KnowledgeManager):
        self.km = knowledge_manager
        # Cache for search results: (query_tuple, scope, max_results, whole_word, case_sensitive) -> results
        self._search_cache: Dict[tuple, Dict[str, Any]] = {}

    def _matches_query(self, text: str, q: str, whole_word: bool, case_sensitive: bool, use_regex: bool = False) -> bool:
        """Check if text matches the query string with given options."""
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(q, text, flags=flags))
            except re.error:
                return False # Invalid regex, fallback to no match

        if not case_sensitive:
            text = text.lower()
            q = q.lower()

        if whole_word:
            # Use word boundary matching for whole word match
            pattern = r'\b' + re.escape(q) + r'\b'
            return bool(re.search(pattern, text, flags=0 if case_sensitive else re.IGNORECASE))
        return q in text

    def search(self, query: Union[str, List[str]], search_under: Optional[str] = None,
               max_results: int = 50, whole_word: bool = False,
               case_sensitive: bool = False, use_regex: bool = False,
               order: str = "priority") -> Dict[str, Any]:
        """Search for nodes containing the query text(s).

        Args:
            query: Search query text or list of query texts
            search_under: Optional root node ID to restrict search scope
            max_results: Maximum number of results to return
            whole_word: Whether to match whole words only
            case_sensitive: Whether the search is case sensitive
            use_regex: Whether to treat query as a regular expression
            order: "priority" (sort by relevance) or "dfs" (sort by document order)

        Returns:
            Dictionary containing search results
        """
        if not query:
            return {
                "error": {
                    "type": "invalid_query",
                    "message": "Search query cannot be empty"
                }
            }

        # Normalize query to list and then tuple for caching
        queries = [query] if isinstance(query, str) else query
        if not all(isinstance(q, str) for q in queries):
            return {"error": {"type": "invalid_query", "message": "Queries must be strings"}}

        query_key = (tuple(sorted(queries)), search_under, max_results, whole_word, case_sensitive, use_regex, order)

        # Check cache
        if query_key in self._search_cache:
            return self._search_cache[query_key]

        results = []
        seen_ids = set()

        # Determine nodes to search
        if search_under:
            candidate_nodes = self.km.get_subtree_nodes(search_under)
        else:
            # Iterating km.nodes keys. Note: order is insertion order.
            candidate_nodes = list(self.km.nodes.keys())

        scored_results = []

        # Iterate through all nodes
        for node_id in candidate_nodes:
            # Optimization: If we have enough results and order is DFS, we could stop.
            if order == "dfs" and len(scored_results) >= max_results:
                break

            if node_id in seen_ids:
                continue

            node = self.km.get_node(node_id)
            if node is None:
                continue

            # Check match and calculate score
            max_score = 0
            matched = False

            is_section = node.get("node_type") == "section"
            title = node.get("title", "") if is_section else ""
            content = node.get("content", "") if not is_section else ""
            label = node.get("label", "")

            for q in queries:
                q_score = 0

                # Check title (Score: 3)
                if title and self._matches_query(title, q, whole_word, case_sensitive, use_regex):
                    q_score = max(q_score, 3)

                # Check content (Score: 2)
                if content and self._matches_query(content, q, whole_word, case_sensitive, use_regex):
                    q_score = max(q_score, 2)

                # Check label (Score: 1)
                if label and self._matches_query(label, q, whole_word, case_sensitive, use_regex):
                    q_score = max(q_score, 1)

                if q_score > 0:
                    matched = True
                    max_score = max(max_score, q_score)

            if matched:
                # Build result info
                result = {
                    "node_id": node_id,
                    "label": label or node_id.split("::")[-1],
                    "title": title,
                    "type": "section" if is_section else "content",
                    "file_id": node["file_id"],
                    "score": max_score
                }

                # Provide excerpt and preview
                if not is_section:
                    # Content preview
                    if len(content) > 100:
                        result["content_preview"] = content[:92] + " ... ... " + content[-5:]
                    else:
                        result["content_preview"] = content

                    # Excerpt is the context around the match
                    excerpt_q = queries[0]
                    if use_regex:
                        result["excerpt"] = result["content_preview"]
                    else:
                        search_text = content.lower() if not case_sensitive else content
                        search_q = excerpt_q.lower() if not case_sensitive else excerpt_q
                        pos = search_text.find(search_q)

                        if pos != -1:
                            start = max(0, pos - 40)
                            end = min(len(content), pos + len(excerpt_q) + 60)
                            excerpt = content[start:end].strip()
                            if start > 0: excerpt = "... " + excerpt
                            if end < len(content): excerpt = excerpt + " ..."
                            result["excerpt"] = excerpt
                        else:
                            result["excerpt"] = result["content_preview"]
                else:
                    # For sections, excerpt could be the title or label
                    result["excerpt"] = result["title"] or result["label"]
                    result["content_preview"] = ""

                scored_results.append(result)
                seen_ids.add(node_id)

        # Sort results if priority
        if order == "priority":
            scored_results.sort(key=lambda x: x["score"], reverse=True)

        final_results = scored_results[:max_results]

        response = {
            "query": query,
            "search_under": search_under,
            "results": final_results,
            "total_count": len(scored_results),
            "has_more": len(scored_results) > max_results,
            "searched_modules": len(self.km.loaded_modules),
            "total_modules": len(self.km.available_modules),
            "options": {
                "whole_word": whole_word,
                "case_sensitive": case_sensitive,
                "use_regex": use_regex,
                "order": order
            }
        }

        # Cache the result
        self._search_cache[query_key] = response
        return response

    def clear_cache(self) -> None:
        """Clear the search results cache."""
        self._search_cache.clear()
