"""Interactive Command Line Interface for KERAG."""

import cmd
import sys
import argparse
import shlex
import os
from pathlib import Path
from typing import List, Optional, Any, Dict

# Add parent directory to path to allow importing kerag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from kerag.api import KERAGAPI
from kerag.tools.cli import cmd_split


class KERAGShell(cmd.Cmd):
    intro = "Welcome to KERAG CLI. Type help or ? to list commands.\n"

    def __init__(self, root_path: str, lang: str = ""):
        super().__init__()
        self.api = KERAGAPI(root_path, lang=lang)
        self.update_prompt()

    def update_prompt(self):
        res = self.api.get_current_node()
        if res.get("success"):
            node_id = res["data"].get("node_id") if res["data"] else "Unknown"
        else:
            node_id = "Unknown"
        self.prompt = f"KERAG [{node_id}]> "

    def do_exit(self, arg):
        """Exit the CLI."""
        print("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the CLI."""
        return self.do_exit(arg)

    def do_load(self, arg):
        """Load a module. If no name provided, list available modules.
        Usage: load [module_name]
        """
        if not arg:
            res = self.api.get_all_modules()
            if not res.get("success"):
                print(f"Error: {res.get('error')}")
                return
            info = res["data"]
            available = info["available_modules"]
            loaded = info["loaded_modules"]
            print("Available modules:")
            for m in available:
                status = "[LOADED]" if m in loaded else "[ ]"
                print(f"  {status} {m}")
            return

        res = self.api.load_module(arg)
        if res.get("success"):
            print(f"Module '{arg}' loaded successfully ({res.get('metadata', {}).get('loaded_nodes')} nodes).")
        else:
            print(f"Error loading module: {res.get('error')}")

    def do_unload(self, arg):
        """Unload a module.
        Usage: unload <module_name>
        """
        if not arg:
            print("Usage: unload <module_name>")
            return
        res = self.api.unload_module(arg)
        if res.get("success"):
            print(f"Module '{arg}' unloaded.")
            self.update_prompt()
        else:
            print(f"Error unloading module: {res.get('error')}")

    def do_purge(self, arg):
        """Unload all modules and clear caches."""
        res = self.api.purge()
        if res.get("success"):
            print(f"Purged modules: {', '.join(res['data'].get('unloaded_modules', []))}")
        else:
            print(f"Error purging: {res.get('error')}")
        self.update_prompt()

    def do_to(self, arg):
        """Navigate to a node.
        Usage: to [node_id | index | label]
        """
        if not arg:
            print("Usage: to [target]")
            return

        res = self.api.navigate_to(arg)
        if not res.get("success"):
            metadata = res.get("metadata", {})
            if "candidates" in metadata:
                print(f"Ambiguous target '{arg}'. Candidates:")
                for c in metadata["candidates"]:
                    print(f"  - {c['id']} ({c.get('title', '')})")
            else:
                print(f"Error: {res.get('error')}")
        else:
            self.update_prompt()

    def do_back(self, arg):
        """Go back in history.
        Usage: back [steps]
        """
        steps = int(arg) if arg.isdigit() else 1
        self.api.navigate_back(steps)
        self.update_prompt()

    def do_forward(self, arg):
        """Go forward in history.
        Usage: forward [steps]
        """
        steps = int(arg) if arg.isdigit() else 1
        self.api.navigate_forward(steps)
        self.update_prompt()

    def do_up(self, arg):
        """Move up in hierarchy.
        Usage: up [levels]
        """
        levels = int(arg) if arg.isdigit() else 1
        res = self.api.up(levels)
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
        self.update_prompt()

    def do_ls(self, arg):
        """List children of a node.
        Usage: ls [node_id]
        """
        node_id = arg if arg else None
        res = self.api.preview_children(node_id)

        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return

        children = res["data"]
        if not children:
            print("No children.")
            return

        print(f"Children of {node_id or 'current node'}:")
        for i, child in enumerate(children):
            node_type = child.get("type", "unknown")
            label = child.get("label", "no-label")
            title = child.get("title", "")
            prefix = "[D]" if node_type == "section" else "[F]"
            suffix = f" - {title}" if title else ""
            print(f"  {i+1}. {prefix} {label} ({child['id']}){suffix}")

    def do_view(self, arg):
        """View node details.
        Usage: view [node_id] [-d DEPTH] [-c] [-f FORMAT]
        """
        parser = argparse.ArgumentParser(prog="view")
        parser.add_argument("node_id", nargs="?", default=None)
        parser.add_argument("-d", "--depth", type=int, default=1)
        parser.add_argument("-c", "--content", action="store_true")
        parser.add_argument("-f", "--format", choices=["text", "markdown", "tree"], default="text")

        try:
            args = parser.parse_args(shlex.split(arg))
        except SystemExit:
            return

        res = self.api.get_node_view(
            node_id=args.node_id,
            depth=args.depth,
            include_content=args.content,
            format=args.format if args.format != "text" else "tree"
        )

        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return

        formatted = res["data"]["formatted_content"]
        fmt = args.format
        if fmt == "markdown":
            print(formatted.get("markdown", ""))
        elif fmt == "tree" or fmt == "text":
            print(formatted.get("tree", formatted.get("text", "")))

    def do_search(self, arg):
        """Search for keywords.
        Usage: search <keyword> [search_under] [-r] [--order {priority,dfs}]
        """
        parser = argparse.ArgumentParser(prog="search")
        parser.add_argument("keyword")
        parser.add_argument("search_under", nargs="?", help="Optional node ID to search under")
        parser.add_argument("-r", "--regex", action="store_true")
        parser.add_argument("-o", "--order", choices=["priority", "dfs"], default="priority", help="Sort order")

        try:
            args = parser.parse_args(shlex.split(arg))
        except SystemExit:
            return
        except Exception:
            print("Usage: search <keyword> [search_under] [-r] [-o order]")
            return

        res = self.api.search(args.keyword, search_under=args.search_under, use_regex=args.regex, order=args.order)
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return

        results = res["data"]
        total = res.get("metadata", {}).get("total", len(results))
        scope_msg = f" in subtree '{args.search_under}'" if args.search_under else " globally"
        print(f"Found {total} results for '{args.keyword}'{scope_msg} (order: {args.order}):")
        for i, r in enumerate(results):
            score_info = f" [Score: {r['score']}]" if 'score' in r and args.order == "priority" else ""
            print(f"  {i+1}. [{r['type']}] {r['label']} ({r['node_id']}) - {r.get('title', '')}{score_info}")
            if 'excerpt' in r:
                print(f"     {r['excerpt']}")

    def do_grep(self, arg):
        """Alias for search."""
        return self.do_search(arg)

    def do_pwd(self, arg):
        """Show current breadcrumb path."""
        res = self.api.get_breadcrumb()
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return
        crumbs = res["data"]
        path = " > ".join([f"{c['label']} ({c['id']})" for c in crumbs])
        print(f"Current Path: {path}")

    def do_roots(self, arg):
        """List root nodes of all loaded modules."""
        res = self.api.get_loaded_roots()
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return
        roots = res["data"]
        if not roots:
            print("No modules loaded.")
            return
        print("Loaded Module Roots:")
        for r in roots:
            print(f"  - {r['id']} ({r.get('title', 'No Title')})")

    def do_status(self, arg):
        """Show system status."""
        res = self.api.get_status()
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return
        status = res["data"]
        print("KERAG System Status:")
        print(f"  Local Root:     {status['local_root']}")
        print(f"  Global Root:    {status['global_root']}")
        print(f"  Language:       {status['lang'] or 'Default'}")
        print(f"  Available Mods: {status['available_modules']}")
        print(f"  Loaded Mods:    {status['loaded_modules']}")
        print(f"  Total Nodes:    {status['total_nodes']}")
        print(f"  Current Node:   {status['current_node']}")

    def do_list(self, arg):
        """List modules based on scope and status.
        Usage: list [scope] [status]
        scope: local/global/all (default: all)
        status: loaded/all (default: all)
        """
        parts = shlex.split(arg) if arg else []
        scope_req = parts[0] if len(parts) > 0 else "all"
        status_req = parts[1] if len(parts) > 1 else "all"

        if scope_req not in ["local", "global", "all"]:
            print(f"Invalid scope '{scope_req}'. Use: local/global/all")
            return
        if status_req not in ["loaded", "all"]:
            print(f"Invalid status '{status_req}'. Use: loaded/all")
            return

        res = self.api.get_all_modules()
        if not res.get("success"):
            print(f"Error: {res.get('error')}")
            return
        info = res["data"]

        if scope_req == "local":
            modules_to_check = [m for m in info["modules"] if not m["name"].startswith("/")]
        elif scope_req == "global":
            modules_to_check = [m for m in info["modules"] if m["name"].startswith("/")]
        else:
            modules_to_check = info["modules"]

        if status_req in ["all", "loaded"]:
            loaded_modules = [m for m in modules_to_check if m["loaded"]]
            if loaded_modules:
                print(f"Loaded Modules ({scope_req}):")
                for m in loaded_modules:
                    print(f"  - {m['name']} ({m['file_count']} files)")
            elif status_req == "loaded":
                print(f"No loaded modules ({scope_req}).")

        if status_req == "all":
            available_modules = [m for m in modules_to_check if not m["loaded"]]
            if available_modules:
                if 'loaded_modules' in locals() and loaded_modules: print()
                print(f"Available Modules ({scope_req}):")
                for m in available_modules:
                    print(f"  - {m['name']}")

    # Aliases
    do_v = do_view
    do_s = do_search
    do_g = do_grep
    do_l = do_list


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["install", "remove", "list", "scan"]:
        from kerag.modules.cli import main as modules_main
        modules_main(sys.argv[1:])
        return

    if len(sys.argv) > 1 and sys.argv[1] == "tool":
        if len(sys.argv) > 2 and sys.argv[2] not in ['-h', '--help']:
            tool_command = sys.argv[2]
            if tool_command == "split":
                from kerag.tools.cli import add_split_parser_args
                import argparse
                parser = argparse.ArgumentParser(prog='kerag tool split', description='Split Markdown documents')
                add_split_parser_args(parser)
                try:
                    args = parser.parse_args(sys.argv[3:])
                    cmd_split(args)
                except SystemExit: pass
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)
                    sys.exit(1)
                return
            elif tool_command == "pack":
                from kerag.tools.cli import add_pack_parser_args, cmd_pack
                import argparse
                parser = argparse.ArgumentParser(prog='kerag tool pack', description='Pack knowledge modules')
                add_pack_parser_args(parser)
                try:
                    args = parser.parse_args(sys.argv[3:])
                    cmd_pack(args)
                except SystemExit: pass
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)
                    sys.exit(1)
                return
            else:
                print(f"Unknown tool command: {tool_command}")
                sys.exit(1)
        else:
            print("Usage: kerag tool <command>\n\nAvailable tool commands:\n  split    Split Markdown documents\n  pack     Pack knowledge modules")
            sys.exit(0)

    parser = argparse.ArgumentParser(description="KERAG Interactive CLI")
    parser.add_argument("local_root", nargs="?", help="Local root directory of knowledge base (optional)")
    parser.add_argument("--lang", default="", help="Language preference")
    args = parser.parse_args()

    try:
        shell = KERAGShell(args.local_root, lang=args.lang)
        shell.cmdloop()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
