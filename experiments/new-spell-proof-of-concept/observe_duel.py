"""Observe exceptions and exits from a disposable, pinned Etherlords II process."""

import argparse
import ctypes as ct
from ctypes import wintypes as wt
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import subprocess

from native_producers import PINNED_EXE
from prepare_duel_matrix import PROBE_HASHES, SOURCE_HASHES


class ExceptionRecord(ct.Structure):
    _fields_ = [
        ("code", wt.DWORD), ("flags", wt.DWORD), ("nested", ct.c_void_p),
        ("address", ct.c_void_p), ("count", wt.DWORD), ("info", ct.c_size_t * 15),
    ]


class ExceptionEvent(ct.Structure):
    _fields_ = [("record", ExceptionRecord), ("first_chance", wt.DWORD)]


class EventData(ct.Union):
    _fields_ = [
        ("exception", ExceptionEvent), ("exit_code", wt.DWORD),
        ("pointers", ct.c_void_p * 4),
    ]


class DebugEvent(ct.Structure):
    _fields_ = [("kind", wt.DWORD), ("pid", wt.DWORD), ("tid", wt.DWORD), ("data", EventData)]


REGISTER_INDEXES = dict(zip(
    ("edi", "esi", "ebx", "edx", "ecx", "eax", "ebp", "eip", "esp"),
    (39, 40, 41, 42, 43, 44, 45, 46, 49),
))


def winapi():
    api = ct.WinDLL("kernel32", use_last_error=True)
    size = ct.c_size_t
    signatures = {
        "DebugSetProcessKillOnExit": ((wt.BOOL,), wt.BOOL),
        "DebugActiveProcessStop": ((wt.DWORD,), wt.BOOL),
        "WaitForDebugEvent": ((ct.POINTER(DebugEvent), wt.DWORD), wt.BOOL),
        "ContinueDebugEvent": ((wt.DWORD, wt.DWORD, wt.DWORD), wt.BOOL),
        "CloseHandle": ((wt.HANDLE,), wt.BOOL),
        "OpenThread": ((wt.DWORD, wt.BOOL, wt.DWORD), wt.HANDLE),
        "Wow64GetThreadContext": ((wt.HANDLE, ct.c_void_p), wt.BOOL),
        "ReadProcessMemory": ((wt.HANDLE, ct.c_void_p, ct.c_void_p, size, ct.POINTER(size)), wt.BOOL),
    }
    for name, (parameters, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes = parameters
        function.restype = result
    return api


def memory(api, process, address, length):
    buffer = ct.create_string_buffer(length)
    read = ct.c_size_t()
    if api.ReadProcessMemory(process, address, buffer, length, ct.byref(read)):
        return buffer.raw[:read.value]
    return b""


def exception_context(api, process, thread_id, base):
    thread = api.OpenThread(0x0008 | 0x0040, False, thread_id)
    if not thread:
        return {"context_error": ct.get_last_error()}
    try:
        context = (wt.DWORD * 179)()
        context[0] = 0x10003  # WOW64_CONTROL | WOW64_INTEGER
        if not api.Wow64GetThreadContext(thread, context):
            return {"context_error": ct.get_last_error()}
        registers = {name: context[index] for name, index in REGISTER_INDEXES.items()}
        stack = memory(api, process, registers["esp"], 64)
        evidence = {
            "registers": {name: f"{value:#010x}" for name, value in registers.items()},
            "stack_words": [f"{word:#010x}" for (word,) in struct.iter_unpack("<I", stack)],
        }
        if registers["eip"] == base + 0x346554 and len(stack) >= 0x1c:
            # This pinned factory's stack layout is documented in PRODUCER_ARCHITECTURE.md.
            evidence["factory_return_address"] = f"{struct.unpack_from('<I', stack, 0x14)[0]:#010x}"
            evidence["factory_spell_id"] = stack[0x18:0x1c].decode("ascii", errors="replace")
            if len(stack) >= 0x28 and evidence["factory_return_address"] == f"{base + 0x3332e2:#010x}":
                evidence["hand_caller_return_address"] = f"{struct.unpack_from('<I', stack, 0x24)[0]:#010x}"
        return evidence
    finally:
        api.CloseHandle(thread)


def observe(game, output):
    if os.name != "nt" or ct.sizeof(ct.c_void_p) != 8:
        raise ValueError("Use 64-bit Python on Windows to observe the 32-bit game")
    executable = game / "Etherlords2.exe"
    if not (game / ".duel-matrix-copy").is_file() or (game / ".git").exists():
        raise ValueError("Use a disposable game directory prepared by prepare_duel_matrix.py")
    if sha256(executable.read_bytes()).hexdigest() != PINNED_EXE:
        raise ValueError("Executable SHA-256 differs from the pinned game")
    hashes = {name: sha256((game / "Resources" / name).read_bytes()).hexdigest()
              for name in SOURCE_HASHES}
    if hashes not in (SOURCE_HASHES, PROBE_HASHES):
        raise ValueError("Game copy resources do not match either matrix variant")
    api = winapi()
    with output.open("x", encoding="utf-8") as log:
        def record(kind, **data):
            entry = {"utc": datetime.now(timezone.utc).isoformat(), "event": kind, **data}
            line = json.dumps(entry)
            print(line, flush=True)
            print(line, file=log, flush=True)

        process = subprocess.Popen([str(executable)], cwd=game, creationflags=0x00000002,
                                   env={**os.environ, "__COMPAT_LAYER": "WIN2000"})
        active = True
        base = 0
        process_handle = None
        startup_breakpoints = set()
        try:
            if not api.DebugSetProcessKillOnExit(False):
                raise ct.WinError(ct.get_last_error())
            record("launch", pid=process.pid, game_copy=game.name, executable_sha256=PINNED_EXE,
                   archive_sha256=hashes)
            while active:
                event = DebugEvent()
                if not api.WaitForDebugEvent(ct.byref(event), 250):
                    error = ct.get_last_error()
                    if error in (121, 258):  # Timeout
                        continue
                    raise ct.WinError(error)
                status = 0x00010002  # DBG_CONTINUE
                try:
                    if event.kind == 3:  # CREATE_PROCESS_DEBUG_EVENT
                        file_handle, process_handle, _, base = event.data.pointers
                        record("image", base=hex(base))
                        if file_handle:
                            api.CloseHandle(file_handle)
                    elif event.kind == 6:  # LOAD_DLL_DEBUG_EVENT
                        file_handle = event.data.pointers[0]
                        if file_handle:
                            api.CloseHandle(file_handle)
                    elif event.kind == 1:  # EXCEPTION_DEBUG_EVENT
                        detail = event.data.exception
                        fault = detail.record
                        if (detail.first_chance and fault.code in (0x80000003, 0x4000001f)
                                and fault.code not in startup_breakpoints):
                            startup_breakpoints.add(fault.code)
                            continue
                        status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED
                        details = {
                            "code": f"{fault.code:#010x}", "address": hex(fault.address or 0),
                            "first_chance": bool(detail.first_chance), "thread": event.tid,
                        }
                        if fault.code == 0xc0000005 and fault.count >= 2:
                            details.update(access_kind=fault.info[0], accessed_address=hex(fault.info[1]))
                            if process_handle and base:
                                details.update(exception_context(api, process_handle, event.tid, base))
                        record("exception", **details)
                    elif event.kind == 5:  # EXIT_PROCESS_DEBUG_EVENT
                        record("exit", code=f"{event.data.exit_code:#010x}")
                        active = False
                finally:
                    if not api.ContinueDebugEvent(event.pid, event.tid, status):
                        raise ct.WinError(ct.get_last_error())
        except KeyboardInterrupt:
            record("observer_interrupted")
        finally:
            if active and not api.DebugActiveProcessStop(process.pid):
                record("detach_failed", error=ct.get_last_error())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_copy", type=Path)
    parser.add_argument("log", type=Path, help="New local JSON Lines file")
    args = parser.parse_args()
    try:
        observe(args.game_copy.resolve(strict=True), args.log)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
