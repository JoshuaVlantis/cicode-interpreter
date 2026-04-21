#!/usr/bin/env python3
"""CiCode interpreter CLI entry point."""
import sys
import os
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)


def main():
    # Support both subcommand and legacy positional usage
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-') and sys.argv[1] != 'run':
        # Legacy: cicode.py file1.ci [file2.ci ...] => validate mode
        files = [a for a in sys.argv[1:] if not a.startswith('-')]
        _cmd_validate(files)
        return

    parser = argparse.ArgumentParser(
        prog='cicode',
        description='CiCode interpreter for AVEVA Plant SCADA .ci files',
    )
    subparsers = parser.add_subparsers(dest='command')

    run_parser = subparsers.add_parser('run', help='Run CiCode files')
    run_parser.add_argument('files', nargs='+', help='.ci files to load')
    run_parser.add_argument('-c', '--call', metavar='FUNCTION',
                            help='Function to call after loading')
    run_parser.add_argument('func_args', nargs='*', help='Arguments for the called function')

    args = parser.parse_args()

    if args.command == 'run':
        _cmd_run(args.files, args.call, getattr(args, 'func_args', []))
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_run(files, func_name, func_args):
    from interpreter import Interpreter, HaltException

    interp = Interpreter()

    for fpath in files:
        fpath = _resolve_path(fpath)
        if fpath is None:
            sys.exit(1)
        print(f"Loading: {fpath}", file=sys.stderr)
        try:
            interp.load_file(fpath)
        except Exception as e:
            print(f"Error loading {fpath}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

    if not func_name:
        print("Files loaded successfully. Use -c FUNCTION to call a function.",
              file=sys.stderr)
        return

    coerced_args = []
    for a in (func_args or []):
        try:
            coerced_args.append(int(a))
        except ValueError:
            try:
                coerced_args.append(float(a))
            except ValueError:
                coerced_args.append(a)

    try:
        result = interp.call_function(func_name, coerced_args)
        if result is not None and result != 0 and result != "":
            print(f"Return value: {result}")
    except HaltException:
        pass
    except SystemExit:
        raise
    except Exception as e:
        print(f"Runtime error in {func_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _cmd_validate(files):
    from lexer import tokenize
    from parser import Parser

    ok = True
    for fpath in files:
        fpath_resolved = _resolve_path(fpath, quiet=True) or os.path.abspath(fpath)
        if not os.path.exists(fpath_resolved):
            print(f"Error: file not found: {fpath}", file=sys.stderr)
            ok = False
            continue

        try:
            with open(fpath_resolved, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            tokens = tokenize(source, fpath_resolved)
            p = Parser(tokens, fpath_resolved)
            program = p.parse()
            n_funcs = sum(1 for d in program.decls if d.__class__.__name__ == 'FunctionDecl')
            n_globals = sum(1 for d in program.decls if d.__class__.__name__ == 'ScopeDecl')
            print(f"OK: {fpath_resolved} ({n_funcs} functions, {n_globals} scope declarations)")
        except Exception as e:
            print(f"Error: {fpath_resolved}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            ok = False

    sys.exit(0 if ok else 1)


def _resolve_path(fpath, quiet=False):
    if os.path.isabs(fpath):
        if os.path.exists(fpath):
            return fpath
        if not quiet:
            print(f"Error: file not found: {fpath}", file=sys.stderr)
        return None
    # Try CWD first, then script dir
    for base in (os.getcwd(), _SCRIPT_DIR):
        full = os.path.join(base, fpath)
        if os.path.exists(full):
            return os.path.abspath(full)
    if not quiet:
        print(f"Error: file not found: {fpath}", file=sys.stderr)
    return None


if __name__ == '__main__':
    main()
