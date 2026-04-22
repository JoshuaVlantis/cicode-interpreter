#!/usr/bin/env python3
"""CiCode Debug Adapter — speaks Debug Adapter Protocol over stdin/stdout."""

import sys
import os
import json
import threading
import traceback

# Capture the real stdout/stdin buffers before anything can redirect them
_dap_out = sys.stdout.buffer
_dap_in  = sys.stdin.buffer

# Add interpreter directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── DAP I/O ──────────────────────────────────────────────────────────────────

def read_message():
    """Read one DAP message from stdin."""
    headers = {}
    while True:
        line = _dap_in.readline()
        if not line:
            return None
        line = line.rstrip(b'\r\n')
        if not line:
            break
        key, _, value = line.partition(b':')
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b'content-length', 0))
    body = _dap_in.read(length)
    return json.loads(body.decode('utf-8'))

_send_lock = threading.Lock()

def send_message(msg):
    """Send one DAP message to stdout."""
    body = json.dumps(msg).encode('utf-8')
    header = f'Content-Length: {len(body)}\r\n\r\n'.encode('utf-8')
    with _send_lock:
        _dap_out.write(header + body)
        _dap_out.flush()

def send_response(req, body=None, success=True, message=''):
    send_message({
        'seq': 0,
        'type': 'response',
        'request_seq': req['seq'],
        'command': req['command'],
        'success': success,
        'message': message,
        'body': body or {}
    })

def send_event(event, body=None):
    send_message({
        'seq': 0,
        'type': 'event',
        'event': event,
        'body': body or {}
    })

# ─── Debug Adapter State ───────────────────────────────────────────────────────

class DebugAdapter:
    def __init__(self):
        self.breakpoints = {}      # {normalized_path: set(line_numbers)}
        self.resume_event = threading.Event()
        self.step_mode = None      # None | 'continue' | 'next' | 'stepIn' | 'stepOut'
        self.step_depth = 0
        self.paused = False
        self.paused_file = ''
        self.paused_line = 0
        self.paused_local = {}
        self.paused_module = {}
        self.paused_reason = 'breakpoint'
        self.interpreter = None
        self.interp_thread = None
        self.var_refs = {}         # {ref_id: data} for variable expansion
        self.next_ref = 1
        self.launch_args = {}
        self._var_refs_lock = threading.Lock()

    def normalize_path(self, p):
        return os.path.normcase(os.path.abspath(p))

    def debug_hook(self, file_path, line, local_scope, module_scope):
        """Called by interpreter before each statement."""
        norm = self.normalize_path(file_path) if file_path else ''
        depth = len(self.interpreter._call_stack)

        should_pause = False
        reason = 'step'

        # Check breakpoints
        if norm in self.breakpoints and line in self.breakpoints[norm]:
            should_pause = True
            reason = 'breakpoint'

        # Check step mode
        if not should_pause and self.step_mode:
            if self.step_mode == 'stepIn':
                should_pause = True
                reason = 'step'
            elif self.step_mode == 'next' and depth <= self.step_depth:
                should_pause = True
                reason = 'step'
            elif self.step_mode == 'stepOut' and depth < self.step_depth:
                should_pause = True
                reason = 'step'

        if should_pause:
            self.step_mode = None
            self.paused = True
            self.paused_file = file_path or ''
            self.paused_line = line
            self.paused_local = dict(local_scope)
            self.paused_module = dict(module_scope)
            self.paused_reason = reason
            with self._var_refs_lock:
                self.var_refs = {}
                self.next_ref = 1
            send_event('stopped', {
                'reason': reason,
                'threadId': 1,
                'allThreadsStopped': True
            })
            # Block interpreter thread until resume
            self.resume_event.clear()
            self.resume_event.wait()
            self.paused = False

    def get_var_ref(self, data):
        """Register data for variable expansion, return ref id."""
        with self._var_refs_lock:
            ref = self.next_ref
            self.var_refs[ref] = data
            self.next_ref += 1
        return ref

    def serialize_value(self, val, name=''):
        """Convert a Python value to DAP variable dict."""
        try:
            from interpreter import CiCodeArray
            if isinstance(val, CiCodeArray):
                ref = self.get_var_ref(('array', val))
                return {
                    'name': name,
                    'value': f'Array[{",".join(str(d) for d in val.dims)}] ({len(val.data)} set)',
                    'type': 'array',
                    'variablesReference': ref
                }
        except ImportError:
            pass
        if isinstance(val, dict):
            ref = self.get_var_ref(('dict', val))
            return {
                'name': name,
                'value': f'{{...}} ({len(val)} keys)',
                'type': 'object',
                'variablesReference': ref
            }
        return {
            'name': name,
            'value': str(val),
            'type': type(val).__name__,
            'variablesReference': 0
        }

    def run_loop(self):
        """Main DAP message loop."""
        while True:
            msg = read_message()
            if msg is None:
                break
            try:
                self.handle(msg)
            except Exception:
                send_event('output', {
                    'category': 'stderr',
                    'output': traceback.format_exc()
                })

    def handle(self, msg):
        cmd = msg.get('command', '')
        args = msg.get('arguments', {})

        if cmd == 'initialize':
            send_response(msg, {
                'supportsConfigurationDoneRequest': True,
                'supportsStepBack': False,
                'supportsRestartRequest': False,
                'supportsTerminateRequest': True,
                'supportsSetVariable': False,
            })
            send_event('initialized')

        elif cmd == 'launch':
            self.launch_args = args
            send_response(msg)

        elif cmd == 'configurationDone':
            send_response(msg)
            # Start the interpreter in a background thread after config is done
            self.interp_thread = threading.Thread(target=self._run_interpreter, daemon=True)
            self.interp_thread.start()

        elif cmd == 'setBreakpoints':
            src = args.get('source', {}).get('path', '')
            norm = self.normalize_path(src)
            lines = {bp['line'] for bp in args.get('breakpoints', [])}
            self.breakpoints[norm] = lines
            bps = [{'verified': True, 'line': l} for l in lines]
            send_response(msg, {'breakpoints': bps})

        elif cmd == 'threads':
            send_response(msg, {'threads': [{'id': 1, 'name': 'Main Thread'}]})

        elif cmd == 'stackTrace':
            if not self.paused or not self.interpreter:
                send_response(msg, {'stackFrames': [], 'totalFrames': 0})
                return
            frames = []
            stack = list(self.interpreter._call_stack)
            for i, frame in enumerate(reversed(stack)):
                fname, ffile, fline = frame[0], frame[1], frame[2]
                frame_dict = {
                    'id': i,
                    'name': fname,
                    'line': fline if fline else 1,
                    'column': 1
                }
                if ffile:
                    frame_dict['source'] = {
                        'name': os.path.basename(ffile),
                        'path': ffile
                    }
                frames.append(frame_dict)
            send_response(msg, {'stackFrames': frames, 'totalFrames': len(frames)})

        elif cmd == 'scopes':
            scopes = []
            if self.paused and self.interpreter:
                local_ref = self.get_var_ref(('scope', dict(self.paused_local)))
                module_ref = self.get_var_ref(('scope', dict(self.interpreter.module_scopes.get(self.paused_file, {}))))
                global_ref = self.get_var_ref(('scope', dict(self.interpreter.global_scope)))
                scopes = [
                    {'name': 'Local', 'variablesReference': local_ref, 'expensive': False},
                    {'name': 'Module', 'variablesReference': module_ref, 'expensive': False},
                    {'name': 'Global', 'variablesReference': global_ref, 'expensive': True},
                ]
            send_response(msg, {'scopes': scopes})

        elif cmd == 'variables':
            ref = args.get('variablesReference', 0)
            with self._var_refs_lock:
                data = self.var_refs.get(ref)
            variables = []
            if data:
                kind, obj = data
                if kind in ('scope', 'dict'):
                    for k, v in obj.items():
                        var = self.serialize_value(v, str(k))
                        variables.append(var)
                elif kind == 'array':
                    arr = obj
                    for key, v in sorted(arr.data.items()):
                        idx = ','.join(str(i) for i in key)
                        var = self.serialize_value(v, f'[{idx}]')
                        variables.append(var)
            send_response(msg, {'variables': variables})

        elif cmd == 'continue':
            self.step_mode = None
            self.resume_event.set()
            send_response(msg, {'allThreadsContinued': True})

        elif cmd == 'next':
            self.step_mode = 'next'
            self.step_depth = len(self.interpreter._call_stack) if self.interpreter else 0
            self.resume_event.set()
            send_response(msg)

        elif cmd == 'stepIn':
            self.step_mode = 'stepIn'
            self.resume_event.set()
            send_response(msg)

        elif cmd == 'stepOut':
            self.step_mode = 'stepOut'
            self.step_depth = len(self.interpreter._call_stack) if self.interpreter else 0
            self.resume_event.set()
            send_response(msg)

        elif cmd == 'pause':
            self.step_mode = 'stepIn'  # pause at next statement
            send_response(msg)

        elif cmd == 'terminate' or cmd == 'disconnect':
            send_response(msg)
            send_event('terminated')
            os._exit(0)

        elif cmd == 'evaluate':
            expr = args.get('expression', '').lower()
            result = ''
            if self.paused and self.interpreter:
                try:
                    val = (self.paused_local.get(expr) or
                           self.interpreter.global_scope.get(expr, ''))
                    result = str(val)
                except Exception as e:
                    result = str(e)
            send_response(msg, {'result': result, 'variablesReference': 0})

        else:
            send_response(msg)

    def _run_interpreter(self):
        """Run the CiCode interpreter in a background thread."""

        class DAPStream:
            """Redirects Python print() output to the DAP debug console."""
            def __init__(self, category):
                self.category = category
                self._buf = ''
            def write(self, text):
                self._buf += text
                while '\n' in self._buf:
                    line, self._buf = self._buf.split('\n', 1)
                    send_event('output', {'category': self.category, 'output': line + '\n'})
            def flush(self):
                if self._buf:
                    send_event('output', {'category': self.category, 'output': self._buf})
                    self._buf = ''
            def fileno(self):
                raise OSError('no fileno')

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = DAPStream('stdout')
        sys.stderr = DAPStream('stderr')

        try:
            from interpreter import Interpreter, HaltException

            interp = Interpreter()
            self.interpreter = interp
            interp.debug_hook = self.debug_hook

            args = self.launch_args
            program = args.get('program', '')
            function = args.get('function', 'Main')
            additional = args.get('additionalFiles', []) or []

            files = [program] + additional

            for f in files:
                if f and os.path.exists(f):
                    send_event('output', {'category': 'console', 'output': f'Loading: {f}\n'})
                    interp.load_file(f)
                elif f:
                    send_event('output', {'category': 'stderr', 'output': f'File not found: {f}\n'})

            send_event('output', {'category': 'console', 'output': f'Running: {function}()\n'})
            interp.call_function(function, [])

        except SystemExit:
            pass
        except Exception as e:
            # Import lazily so it's available after sys.path is set up
            try:
                from parser import ParseError as _ParseError
            except ImportError:
                _ParseError = None
            if _ParseError and isinstance(e, _ParseError):
                fname = e.filename or program
                send_event('output', {
                    'category': 'stderr',
                    'output': f'Syntax Error ({fname}) Line [{e.line}]: {e.msg}\n'
                })
            else:
                send_event('output', {
                    'category': 'stderr',
                    'output': f'Error: {e}\n{traceback.format_exc()}'
                })
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            send_event('terminated')


if __name__ == '__main__':
    adapter = DebugAdapter()
    adapter.run_loop()
