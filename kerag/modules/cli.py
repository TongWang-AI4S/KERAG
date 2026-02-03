import argparse
import sys
from pathlib import Path
from .manager import ModuleManager

def handle_install(manager: ModuleManager, args):
    success, result = manager.install(args.source, global_scope=args.global_scope, force=args.force)

    if success:
        print(f"Successfully installed module: {result}")
    else:
        if result.startswith("CONFLICT:"):
            module_name = result.split(":")[1]
            print(f"Error: Module '{module_name}' already exists.")
            print("Use -f to force overwrite or choose a different source.")
        else:
            print(f"Error: {result}")
            sys.exit(1)

def handle_remove(manager: ModuleManager, args):
    scope = "both"
    if args.global_scope and args.local_scope:
        scope = "both"
    elif args.global_scope:
        scope = "global"
    elif args.local_scope:
        scope = "local"
    elif not args.global_scope and not args.local_scope:
        # Check if exists in both
        modules = manager.get_modules()
        global_module_names = [name for name, _ in modules.get("global", [])]
        local_module_names = [name for name, _ in modules.get("local", [])]

        in_global = args.module_name in global_module_names
        in_local = args.module_name in local_module_names

        if in_global and in_local:
            print(f"Module '{args.module_name}' found in both global and local scopes.")
            print("Options: [g]lobal, [l]ocal, [b]oth, [c]ancel")
            choice = input("Choice: ").lower()
            if choice == 'g': scope = "global"
            elif choice == 'l': scope = "local"
            elif choice == 'b': scope = "both"
            else:
                print("Cancelled.")
                return
        elif in_global:
            scope = "global"
        elif in_local:
            scope = "local"
        else:
            print(f"Module '{args.module_name}' not found in any scope.")
            return

    results = manager.remove(args.module_name, scope=scope)
    for s_name, success, msg in results:
        status = "Success" if success else "Failed"
        # print(f"[{s_name}] {status}: {msg}")

def handle_list(manager: ModuleManager, args):
    scope = "both"
    if args.global_scope and args.local_scope:
        scope = "both"
    elif args.global_scope:
        scope = "global"
    elif args.local_scope:
        scope = "local"

    modules = manager.get_modules(scope=scope)

    def print_module_list(module_dict, title):
        if not module_dict:
            print("  (None)")
            return

        # 计算最大名称长度（用于对齐）
        max_name_len = max(len(name) for name in module_dict.keys())
        name_col_width = max(max_name_len + 2, 15)
        version_col_width = 15

        # 表头
        header = f"  {'Name':<{name_col_width}}{'Version':<{version_col_width}}Description"
        print(header)
        print("  " + "-" * (name_col_width + version_col_width + 30))

        for name in sorted(module_dict.keys()):
            info = module_dict[name]
            version = info.get("version", "")
            description = info.get("description", "")

            # 截断描述至50个字符
            if len(description) > 50:
                description = description[:47] + " ... ... "

            print(f"  {name:<{name_col_width}}{version:<{version_col_width}}{description}")

    if "global" in modules:
        print(f"Global Modules ({manager.global_root}):")
        print_module_list(modules["global"], "Global")

    if "local" in modules:
        if "global" in modules:
            print()
        print(f"Local Modules ({manager.local_root}):")
        print_module_list(modules["local"], "Local")

def handle_scan(manager: ModuleManager, args):
    scope = "global" if args.global_scope else "local"
    to_update, to_remove, path = manager.scan(scope=scope)

    if not to_update and not to_remove:
        # print(f"[{scope}] No changes detected. {path.name} is up to date.")
        return

    # print(f"[{scope}] Changes detected in {path.parent}:")
    if to_update:
        print("  To update:")
        for name, version, desc in to_update:
            display = f"{name}"
            if version: display += f", version={version}"
            if desc:
                d_short = desc[:30] + " ... ... " if len(desc) > 30 else desc
                display += f", desc={d_short}"
            print(f"    * {display}")
    if to_remove:
        print("  To remove:")
        for m in to_remove:
            print(f"    - {m}")

    if not args.force:
        confirm = input(f"\nUpdate {path.name}? [Y/n]: ").lower()
        if confirm != '' and confirm != 'y':
            print("Aborted.")
            return

    manager.update_modules_yml(path, to_update, to_remove)
    print(f"{path.name} updated successfully.")

def main(argv=None):
    parser = argparse.ArgumentParser(prog="kerag", description="KERAG Module Manager")

    # 全局参数（适用于所有子命令）
    parser.add_argument("--local-root", help="Set local knowledge base root path (overrides KERAG_LOCAL env var)")
    parser.add_argument("--global-root", help="Set global knowledge base root path (overrides KERAG_HOME env var)")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Install
    install_parser = subparsers.add_parser("install", help="Install a module")
    install_parser.add_argument("source", help="Git URL, Archive URL, or Local Path")
    install_parser.add_argument("-g", "--global", action="store_true", dest="global_scope", help="Install to global KERAG_HOME")
    install_parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing module")

    # Remove
    remove_parser = subparsers.add_parser("remove", help="Remove a module")
    remove_parser.add_argument("module_name", help="Name of the module to remove")
    remove_parser.add_argument("-g", "--global", action="store_true", dest="global_scope", help="Remove from global scope")
    remove_parser.add_argument("-l", "--local", action="store_true", dest="local_scope", help="Remove from local scope")

    # List
    list_parser = subparsers.add_parser("list", help="List installed modules")
    list_parser.add_argument("-g", "--global", action="store_true", dest="global_scope", help="List global modules")
    list_parser.add_argument("-l", "--local", action="store_true", dest="local_scope", help="List local modules")

    # Scan
    scan_parser = subparsers.add_parser("scan", help="Scan and update modules.txt")
    scan_parser.add_argument("-g", "--global", action="store_true", dest="global_scope", help="Scan global scope")
    scan_parser.add_argument("-l", "--local", action="store_true", dest="local_scope", help="Scan local scope (default)")
    scan_parser.add_argument("-f", "--force", action="store_true", help="Update without confirmation")

    args = parser.parse_args(argv)

    # 创建 ModuleManager 实例，传入可选的路径参数
    manager = ModuleManager(local_root=args.local_root, global_root=args.global_root)

    if args.command == "install":
        handle_install(manager, args)
    elif args.command == "remove":
        handle_remove(manager, args)
    elif args.command == "list":
        handle_list(manager, args)
    elif args.command == "scan":
        handle_scan(manager, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
