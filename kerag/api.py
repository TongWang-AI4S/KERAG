#!/usr/bin/env python3
"""
KERAG API Module

提供对KERAG知识库的编程接口，封装了所有操作函数。
其他应用（如Web后端、CLI）可以通过导入此模块来操作KERAG。
"""

import sys
import os
import warnings
from pathlib import Path
from typing import Dict, Optional, Any

# 将父目录添加到路径，以便导入kerag包
sys.path.insert(0, str(Path(__file__).parent.parent))

from kerag.core.knowledge_manager import KnowledgeManager
from kerag.core.knowledge_explorer import ExplorerOptions, KnowledgeExplorer
from kerag.front.formatters import (
    TreeFormatter, MarkdownFormatter,
    SearchFormatter, ListFormatter
)
from kerag.modules.manager import ModuleManager


class KERAGAPI:
    """KERAG API 主类，提供所有操作接口"""

    def __init__(self, local_root: Optional[str] = None, global_root: Optional[str] = None, lang: Optional[str] = None, verbose: bool = False):
        """
        初始化KERAG API

        Args:
            local_root: 本地知识库根目录路径
            global_root: 全局知识库根目录路径
            lang: 语言偏好
            verbose: 是否开启详细模式
        """
        if lang is not None:
            self.lang = lang
        else:
            self.lang = os.getenv("KERAG_LANG", "")

        self.local_root = local_root
        self.global_root = global_root
        self.km = KnowledgeManager(local_root=local_root, global_root=global_root, lang=self.lang)
        options = ExplorerOptions(verbose=verbose or True, language=lang)
        self.explorer = KnowledgeExplorer(self.km, options=options)

        self.module_manager = ModuleManager(local_root=local_root, global_root=global_root)

        # 初始化格式化器
        self.tree_formatter = TreeFormatter(show_metadata=True)
        self.md_formatter = MarkdownFormatter(display_mode="label")
        self.search_formatter = SearchFormatter()
        self.list_formatter = ListFormatter()

    def _build_response(self, success: bool, data: Any = None, error: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """统一构建 API 响应结构"""
        return {
            "success": success,
            "data": data,
            "error": error,
            "metadata": metadata or {}
        }

    # 模块管理
    def get_all_modules(self) -> Dict[str, Any]:
        """获取所有模块信息"""
        try:
            available = sorted(list(self.km.available_modules))
            loaded = self.km.loaded_modules

            modules = []
            for name in available:
                file_count = 0
                if name in loaded:
                    module_nodes = self.km.get_nodes_from_module(name)
                    file_ids = set(node["file_id"] for node in module_nodes.values())
                    file_count = len(file_ids)

                modules.append({
                    "name": name,
                    "loaded": name in loaded,
                    "file_count": file_count
                })

            data = {
                "modules": modules,
                "available_modules": available,
                "loaded_modules": list(loaded)
            }
            return self._build_response(True, data=data)
        except Exception as e:
            return self._build_response(False, error=str(e))

    def load_module(self, module_name: str) -> Dict[str, Any]:
        """加载模块"""
        try:
            if module_name in self.km.loaded_modules:
                return self._build_response(True, data={
                    "name": module_name,
                    "loaded": True,
                    "file_count": 0
                }, metadata={"message": f"Module '{module_name}' already loaded"})

            nodes_before = len(self.km.nodes)
            result = self.explorer.load_module(module_name)
            if not result.get("success"):
                raise Exception(result.get("error", "Failed to load module via explorer"))

            module_nodes = self.km.get_nodes_from_module(module_name)
            file_ids = set(node["file_id"] for node in module_nodes.values())
            nodes_loaded = len(self.km.nodes) - nodes_before

            data = {
                "name": module_name,
                "loaded": True,
                "file_count": len(file_ids)
            }
            return self._build_response(True, data=data, metadata={"loaded_nodes": nodes_loaded})
        except Exception as e:
            return self._build_response(False, error=str(e))

    def unload_module(self, module_name: str) -> Dict[str, Any]:
        """卸载模块"""
        warnings.warn("unload_module() 已弃用。", DeprecationWarning, stacklevel=2)
        try:
            if not module_name:
                return self._build_response(False, error="No module specified")

            result = self.explorer.unload_module(module_name)
            if not result.get("success"):
                return self._build_response(False, error=result.get("error", "Unload failed"))

            return self._build_response(True, data={"name": module_name, "loaded": False})
        except Exception as e:
            return self._build_response(False, error=str(e))

    def purge(self) -> Dict[str, Any]:
        """卸载所有模块"""
        warnings.warn("purge() 已弃用。", DeprecationWarning, stacklevel=2)
        try:
            res = self.explorer.purge()
            return self._build_response(True, data={"unloaded_modules": res.get("unloaded", [])})
        except Exception as e:
            return self._build_response(False, error=str(e))

    # 节点导航
    def get_current_node(self) -> Dict[str, Any]:
        """获取当前节点信息"""
        res = self.explorer.get_current_node()
        if "error" in res:
            return self._build_response(False, error=res["error"].get("message", "Unknown error"))

        return self._build_response(True, data=res.get("current_node_info"), metadata={
            "breadcrumb": res.get("breadcrumb"),
            "history_state": {
                "position": res.get("history_position"),
                "size": res.get("history_size"),
                "can_go_back": res.get("can_go_back"),
                "can_go_forward": res.get("can_go_forward")
            }
        })

    def navigate_to(self, target: str) -> Dict[str, Any]:
        """导航到指定节点"""
        try:
            result = self.explorer.navigate_to(target)
            if "error" in result:
                return self._build_response(False, error=str(result["error"]))

            if result.get("type") == "ambiguous_navigation":
                return self._build_response(False, error="Ambiguous target", metadata={"candidates": result.get("candidates")})

            if result.get("type") == "already_at_target":
                return self._build_response(True, data={"already_at_target": True}, metadata={"node_id": result.get("node_id")})

            node_id = self.explorer.current_node_id
            node_detail = self.explorer.get_node_view(node_id, depth=1)
            breadcrumb = self.explorer.get_breadcrumb()

            return self._build_response(True, data=node_detail, metadata={"breadcrumb": breadcrumb})
        except Exception as e:
            return self._build_response(False, error=str(e))

    def navigate_back(self, steps: int = 1) -> Dict[str, Any]:
        """后退导航"""
        self.explorer.navigate_back(steps)
        return self.get_current_node()

    def navigate_forward(self, steps: int = 1) -> Dict[str, Any]:
        """前进导航"""
        self.explorer.navigate_forward(steps)
        return self.get_current_node()

    def resolve_target_id(self, target: str) -> Dict[str, Any]:
        """解析目标 ID"""
        res = self.explorer._resolve_target_id(target)
        if "error" in res:
            return self._build_response(False, error=res["error"])
        return self._build_response(True, data=res)

    def up(self, levels: int = 1) -> Dict[str, Any]:
        """向上导航"""
        result = self.explorer.up(levels)
        if "error" in result:
            return self._build_response(False, error=str(result["error"]))
        return self.get_current_node()

    def get_history(self) -> Dict[str, Any]:
        """获取导航历史"""
        history_data = self.explorer.get_history()
        return self._build_response(True, data=history_data)

    # 节点信息
    def get_node_detail(self, node_id: str) -> Dict[str, Any]:
        """获取节点详细信息"""
        detail = self.explorer.get_node_view(node_id, depth=1)
        if "error" in detail:
            return self._build_response(False, error=str(detail["error"]))
        return self._build_response(True, data=detail)

    def get_parent(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """获取父节点信息"""
        if not node_id:
            node_id = self.explorer.current_node_id

        # 1. 获取当前节点以找到 parent_id
        node = self.km.get_node(node_id)
        if not node:
             return self._build_response(False, error=f"Node not found: {node_id}")

        parent_id = node.get("parent_id")
        if not parent_id or parent_id == "::ROOT":
             # 已经是根节点或其父节点是ROOT
             pass

        if not parent_id:
            return self._build_response(False, error="No parent node (is root?)")

        # 2. 获取父节点详细信息
        parent = self.km.get_node(parent_id)
        if not parent:
             return self._build_response(False, error=f"Parent node not found: {parent_id}")

        data = {
            "node_id": parent["node_id"],
            "label": parent.get("label"),
            "title": parent.get("title", ""),
            "type": parent.get("node_type", "section")
        }
        return self._build_response(True, data=data)

    def get_children(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """获取子节点 ID 列表"""
        ids = self.explorer.get_children(node_id)
        return self._build_response(True, data=ids)

    def preview_children(self, node_id: Optional[str] = None, node_type: str = "all", sort_by: str = "order") -> Dict[str, Any]:
        """获取子节点预览信息"""
        res = self.explorer.preview_children(node_id, node_type, sort_by)
        if "error" in res:
            return self._build_response(False, error=str(res["error"]))
        return self._build_response(True, data=res.get("items", []), metadata=res.get("metadata", {}))

    def get_breadcrumb(self) -> Dict[str, Any]:
        """获取面包屑路径"""
        return self._build_response(True, data=self.explorer.get_breadcrumb())

    # 内容展示
    def get_node_view(
        self,
        node_id: Optional[str] = None,
        depth: int = 1,
        include_content: bool = True,
        include_see_also: bool = True,
        format: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """获取节点视图（包含格式化内容）"""
        if not node_id:
            node_id = self.explorer.current_node_id

        self.explorer.set_filter({
            "include_content": include_content,
            "include_see_also": include_see_also,
            "max_depth": depth
        })

        node = self.km.get_node(node_id)
        if not node:
            return self._build_response(False, error=f"Node not found: {node_id}")

        view_data = self.explorer.get_node_view(node_id, depth, include_content)

        formatted_content = {}
        if format == "markdown":
            formatted_content["markdown"] = self.md_formatter.format(view_data, **kwargs)
        elif format == "tree":
            formatted_content["tree"] = self.tree_formatter.format(view_data, **kwargs)
        elif format == "json":
            formatted_content["json_data"] = view_data
        else:
            formatted_content["text"] = str(view_data)

        return self._build_response(True, data={
            "node": view_data,
            "formatted_content": formatted_content
        })

    # 搜索
    def search(self, keyword: str, scope: str = "all", max_results: int = 50,
               whole_word: bool = False, case_sensitive: bool = False, use_regex: bool = False) -> Dict[str, Any]:
        """搜索节点"""
        try:
            res = self.explorer.search_nodes(
                keyword,
                scope=scope,
                max_results=max_results,
                whole_word=whole_word,
                case_sensitive=case_sensitive,
                use_regex=use_regex
            )
            if "error" in res:
                return self._build_response(False, error=str(res["error"]))

            results = res.get("results", [])
            return self._build_response(True, data=results, metadata={
                "total": res.get("total_count"),
                "query": keyword,
                "scope": scope,
                "has_more": res.get("has_more")
            })
        except Exception as e:
            return self._build_response(False, error=str(e))

    # 系统状态
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        data = {
            "local_root": str(self.km.local_root),
            "global_root": str(self.km.global_root),
            "lang": self.km.lang,
            "available_modules": len(self.km.available_modules),
            "loaded_modules": len(self.km.loaded_modules),
            "total_nodes": len(self.km.nodes),
            "current_node": self.explorer.current_node_id
        }
        return self._build_response(True, data=data)

    def get_loaded_roots(self) -> Dict[str, Any]:
        """获取所有已加载模块的根节点"""
        roots = self.explorer.get_loaded_roots()
        return self._build_response(True, data=roots)

    def list_modules(self, scope: str = "both") -> Dict[str, Any]:
        """获取所有模块信息，包括版本"""
        try:
            modules = self.module_manager.get_modules(scope=scope)
            data = {
                "scope": scope,
                "modules": modules,
                "local_root": str(self.module_manager.local_root),
                "global_root": str(self.module_manager.global_root),
                "loaded_modules": list(self.km.loaded_modules)
            }
            return self._build_response(True, data=data)
        except Exception as e:
            return self._build_response(False, error=str(e))


# 全局API实例
_api_instance = None

def init_api(local_root: Optional[str] = None, global_root: Optional[str] = None, lang: Optional[str] = None, verbose: bool = False) -> KERAGAPI:
    """初始化全局KERAG API实例"""
    global _api_instance
    _api_instance = KERAGAPI(local_root=local_root, global_root=global_root, lang=lang, verbose=verbose)
    return _api_instance

def get_api() -> KERAGAPI:
    """获取全局KERAG API实例"""
    if _api_instance is None:
        raise RuntimeError("KERAG API not initialized. Call init_api() first.")
    return _api_instance
