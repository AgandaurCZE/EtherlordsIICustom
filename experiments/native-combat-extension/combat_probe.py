"""Run a pinned Etherlords II gameplay experiment in a newly launched test process."""

import argparse
import ctypes as ct
from ctypes import wintypes as wt
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "new-spell-proof-of-concept"))
from native_producers import IMAGE_BASE, PINNED_EXE
from observe_duel import DebugEvent, REGISTER_INDEXES, exception_context, memory, winapi
from prepare_duel_matrix import PROBE_HASHES, SOURCE_HASHES, check_hashes
from zap_chain import chain_code


INITIALIZER_TAIL = 0x744D80
INITIALIZER_BYTES = bytes.fromhex("8b 4c 24 30 89 38")
PRODUCER_MAP = 0x9CD998
PRODUCER_VTABLE = 0x8C22B4
PRODUCER_COUNT = 363
INITIALIZER_RETURN = 0x73E27A
CAST_DEBIT = 0x6CCCD9
SURCHARGE_CHECK = 0x6CCCB1
SURCHARGE_DEBIT = 0x6CCCD7
ZAP_SITES = (0x6F229F, 0x6F22ED)
ZAP_FACTORY_SLOT = 0x8C1D78
ZAP_CAST_SLOT = 0x8BFF30
STINK_RAT_SUMMON_SLOT = 0x8C2C24
RAT_HASHES = SOURCE_HASHES | {
    "regs.res": "1c86758929e6dde3ab5dd72f8695322d5f1f9b0b98f2a5e31a7e60c6174e9aba"
}
PROFILE_ARCHIVES = {
    "alias": PROBE_HASHES,
    "alias-flat": PROBE_HASHES,
    "zap-three": SOURCE_HASHES,
    "zap-mass": SOURCE_HASHES,
    "zap-chain": SOURCE_HASHES,
    "rat-brotherhood": RAT_HASHES,
}
DEBUG_CONTINUE = 0x00010002
DEBUG_PASS = 0x80010001
BREAKPOINT_CODES = (0x80000003, 0x4000001F)


def p32(number):
    return struct.pack("<I", number)


def branch(opcode, at, destination):
    return bytes([opcode]) + p32((destination - at - 5) & 0xFFFFFFFF)


def producer_instructions(address, ident, constructor):
    """Insert one engine-owned object, skipping its key if allocation fails."""
    if len(ident) != 4:
        raise ValueError("Producer ID must occupy four bytes")
    code = bytearray()
    code += b"\x6a\x04"  # push 4 — a producer instance contains only its vptr
    code += branch(0xE8, address + len(code), 0x82B410)  # engine operator new
    code += bytes.fromhex("83 c4 04 85 c0")  # add esp,4; test eax,eax
    no_allocation = len(code)
    code += b"\x74\x00"
    code += bytes.fromhex("8b c8")  # mov ecx,eax
    code += branch(0xE8, address + len(code), constructor)
    code += b"\x50"  # retain the new producer across map insertion
    code += b"\x68" + ident  # local key on the stack
    code += bytes.fromhex("8b c4 50 8b ce")  # mov eax,esp; push eax; mov ecx,esi
    code += branch(0xE8, address + len(code), 0x746580)  # thiscall map slot(key*)
    code += bytes.fromhex("83 c4 04 5a 89 10")  # remove key; pop edx; mov [eax],edx
    code[no_allocation + 1] = len(code) - no_allocation - 2
    return code


def initializer_stub(address, ident=b"E3TC", constructor=0x745CA0):
    """Finish stock registration, then install a separately owned producer."""
    code = bytearray.fromhex("89 38")  # mov [eax],edi — stock final slot
    code += bytes.fromhex("81 7e 04") + p32(PRODUCER_COUNT)
    code += b"\x75\x00"
    wrong_count = len(code) - 1
    code += producer_instructions(address + len(code), ident, constructor)
    code[wrong_count] = len(code) - wrong_count - 1
    code += INITIALIZER_BYTES[:4]  # restore stock exception-frame input to epilogue
    code += branch(0xE9, address + len(code), INITIALIZER_TAIL + len(INITIALIZER_BYTES))
    return bytes(code)


def flat_check_stub(address):
    code = bytearray.fromhex("8b 57 14")  # stock caster load
    code += b"\x81\x7f\x04E3TC"       # cmp dword [edi+4], E3TC
    code += b"\x74\x05"                # E3TC skips the surcharge affordability check
    code += bytes.fromhex("39 6a 20 7c 05")
    code += branch(0xE9, address + len(code), 0x6CCCC0)  # accepted
    code += branch(0xE9, address + len(code), 0x6CCCB9)  # stock unaffordable path
    return bytes(code)


def flat_debit_stub(address):
    code = b"\x81\x7f\x04E3TC"         # cmp dword [edi+4], E3TC
    code += bytes.fromhex("75 04 6a 00 eb 01 55 50")  # push 0 or original EBP; push EAX
    call_at = address + len(code)
    code += branch(0xE8, call_at, 0x7542B0)
    code += branch(0xE9, address + len(code), 0x6CCCDE)
    return code, call_at


def patch_api():
    api = winapi()
    size = ct.c_size_t
    ptr = ct.c_void_p
    dwordp = ct.POINTER(wt.DWORD)
    signatures = {
        "VirtualAllocEx": ((wt.HANDLE, ptr, size, wt.DWORD, wt.DWORD), ptr),
        "VirtualProtectEx": ((wt.HANDLE, ptr, size, wt.DWORD, dwordp), wt.BOOL),
        "WriteProcessMemory": ((wt.HANDLE, ptr, ptr, size, ct.POINTER(size)), wt.BOOL),
        "FlushInstructionCache": ((wt.HANDLE, ptr, size), wt.BOOL),
        "Wow64SetThreadContext": ((wt.HANDLE, ptr), wt.BOOL),
    }
    for name, (parameters, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = parameters, result
    return api


def require(result):
    if not result:
        raise ct.WinError(ct.get_last_error())
    return result


def protect(api, process, address, length, permissions):
    old = wt.DWORD()
    require(api.VirtualProtectEx(process, address, length, permissions, ct.byref(old)))
    return old.value


def write(api, process, address, data):
    count = ct.c_size_t()
    require(api.WriteProcessMemory(process, address, ct.create_string_buffer(data),
                                   len(data), ct.byref(count)))
    if count.value != len(data):
        raise OSError(f"Short write at {address:#x}")


def replace(api, process, address, original, updated):
    if len(original) != len(updated) or memory(api, process, address, len(original)) != original:
        raise ValueError(f"Unexpected in-memory bytes at {address:#x}")
    old = protect(api, process, address, len(original), 0x04)  # PAGE_READWRITE
    try:
        write(api, process, address, updated)
        if memory(api, process, address, len(updated)) != updated:
            raise OSError(f"Verification failed at {address:#x}")
    finally:
        protect(api, process, address, len(original), old)
    require(api.FlushInstructionCache(process, address, len(updated)))


def executable_buffer(api, process, generator):
    length = len(generator(0))
    stub = require(api.VirtualAllocEx(process, None, length, 0x3000, 0x04))
    code = generator(stub)
    write(api, process, stub, code)
    if memory(api, process, stub, len(code)) != code:
        raise OSError("Trampoline write did not verify")
    protect(api, process, stub, len(code), 0x20)  # PAGE_EXECUTE_READ
    require(api.FlushInstructionCache(process, stub, len(code)))
    return stub


def register_producer(api, process, record, ident=b"E3TC", constructor=0x745CA0):
    stub = executable_buffer(api, process, lambda address: initializer_stub(address, ident, constructor))
    jump = branch(0xE9, INITIALIZER_TAIL, stub) + b"\x90"
    replace(api, process, INITIALIZER_TAIL, INITIALIZER_BYTES, jump)
    record("patch", address=hex(INITIALIZER_TAIL), original=INITIALIZER_BYTES.hex(),
           updated=jump.hex(), trampoline=hex(stub))


def stage(api, process, profile, traces, record):
    if profile == "zap-three":
        for site in ZAP_SITES:
            replace(api, process, site, b"\x6a\x01", b"\x6a\x03")
            record("patch", address=hex(site), original="6a01", updated="6a03")
        return
    if profile in ("zap-mass", "rat-brotherhood"):
        site, original, replacement = {
            "zap-mass": (ZAP_FACTORY_SLOT, 0x749A30, 0x748F90),
            "rat-brotherhood": (STINK_RAT_SUMMON_SLOT, 0x7380B0, 0x6F0480),
        }[profile]
        replace(api, process, site, p32(original), p32(replacement))
        record("patch", address=hex(site), original=p32(original).hex(), updated=p32(replacement).hex())
        return
    if profile == "zap-chain":
        stub = executable_buffer(api, process, lambda address: chain_code(address)[0])
        _, call_site = chain_code(stub)
        traces[call_site] = (b"\xe8", "zap-survivor-unsummon")
        replace(api, process, ZAP_CAST_SLOT, p32(0x6F2160), p32(stub))
        record("patch", address=hex(ZAP_CAST_SLOT), original=p32(0x6F2160).hex(), updated=p32(stub).hex())
        return
    register_producer(api, process, record)
    if profile == "alias-flat":
        check = executable_buffer(api, process, flat_check_stub)
        debit = executable_buffer(api, process, lambda address: flat_debit_stub(address)[0])
        for site, original, target in (
            (SURCHARGE_CHECK, bytes.fromhex("8b 57 14 39 6a 20 7d 07"), check),
            (SURCHARGE_DEBIT, bytes.fromhex("55 50 e8 d2 75 08 00"), debit),
        ):
            jump = branch(0xE9, site, target) + b"\x90" * (len(original) - 5)
            replace(api, process, site, original, jump)
            record("patch", address=hex(site), original=original.hex(), updated=jump.hex(),
                   trampoline=hex(target))
        _, debit_call = flat_debit_stub(debit)
        traces[debit_call] = (b"\xe8", "grun-debit")


def words(api, process, at, count):
    data = memory(api, process, at, count * 4)
    if len(data) != count * 4:
        raise OSError(f"Short read at {at:#x}")
    return struct.unpack(f"<{count}I", data)


def registry_node(api, process, sentinel, ident):
    key = int.from_bytes(ident, "little")
    node, = words(api, process, sentinel + 4, 1)
    for _ in range(32):
        if not node or node == sentinel:
            break
        left, right, node_key = words(api, process, node + 8, 3)
        if node_key == key:
            return node
        node = left if key < node_key else right
    raise ValueError(f"No initialized node for {ident!r}")


def producer(api, process, sentinel, ident):
    node = registry_node(api, process, sentinel, ident)
    return words(api, process, node + 0x14, 1)[0]


def report_producers(api, process, record):
    sentinel, count = words(api, process, PRODUCER_MAP, 2)
    if count != PRODUCER_COUNT + 1:
        raise ValueError(f"Expected {PRODUCER_COUNT + 1} live map entries, found {count}")
    entries = [producer(api, process, sentinel, ident) for ident in (b"E3TC", b"GRUN")]
    vtables = [words(api, process, entry, 1)[0] for entry in entries]
    if entries[0] == entries[1] or vtables != [PRODUCER_VTABLE] * 2:
        raise ValueError("Unexpected producer ownership or vtable")
    record("producers", count=count, E3TC=hex(entries[0]), GRUN=hex(entries[1]),
           vtable=hex(PRODUCER_VTABLE))


def trace_once(api, process, event, traces, record, extension=None):
    """Capture one execution of a selected gameplay site, then remove its breakpoint."""
    address = event.data.exception.record.address
    original, kind = traces.pop(address)
    thread = require(api.OpenThread(0x0008 | 0x0010 | 0x0040, False, event.tid))
    try:
        context = (wt.DWORD * 179)()
        context[0] = 0x10003
        require(api.Wow64GetThreadContext(thread, context))
        index = REGISTER_INDEXES
        details = {"address": hex(address)}
        if extension:
            registers = {name: context[offset] for name, offset in index.items()}
            details.update(extension.trace(api, process, kind, registers))
        elif kind == "registry-ready":
            report_producers(api, process, record)
        elif kind == "grun-debit":
            spell = context[index["edi"]]
            details.update(spell_object=hex(spell),
                           spell_id=memory(api, process, spell + 4, 4).decode("ascii", errors="replace"),
                           affected_count=context[index["ebp"]],
                           surcharge=words(api, process, context[index["esp"]] + 4, 1)[0])
        elif kind == "brotherhood-attach":
            spell = context[index["ebp"]]
            details["spell_id"] = memory(api, process, spell + 4, 4).decode("ascii", errors="replace")
        elif kind == "brotherhood-activate":
            ability = context[index["ecx"]]
            details["ability_vtable"] = hex(words(api, process, ability, 1)[0])
        elif kind in ("zap-hero", "zap-creature", "lightning-damage"):
            details["damage_argument"] = words(api, process, context[index["esp"]] + 4, 1)[0]
        elif kind == "zap-survivor-unsummon":
            creature = context[index["edi"]]
            details["target_card"] = memory(api, process, creature + 0x20, 4).decode(
                "ascii", errors="replace"
            )
            details["damage_on_creature"] = words(api, process, creature + 0x28, 1)[0]
        replace(api, process, address, b"\xcc", original)
        context[index["eip"]] = address
        require(api.Wow64SetThreadContext(thread, context))
        record(kind, **details)
    finally:
        api.CloseHandle(thread)


def run(game, profile, log_path, *, extension=None):
    if os.name != "nt" or ct.sizeof(ct.c_void_p) != 8:
        raise ValueError("Use 64-bit Python on Windows for this 32-bit game")
    local = (extension.local if extension else HERE / "local").resolve()
    if (game.parent != local or not (game / ".native-combat-test").is_file()
            or (game / ".git").exists() or not log_path.is_relative_to(local)):
        raise ValueError("Use a marked direct child of this experiment's local directory and a local log")
    executable = game / "Etherlords2.exe"
    check_hashes(game, {"Etherlords2.exe": PINNED_EXE})
    archives = extension.archives if extension else PROFILE_ARCHIVES[profile]
    check_hashes(game / "Resources", archives)
    api = patch_api()
    with log_path.open("x", encoding="utf-8") as log:
        def record(kind, **fields):
            line = json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "event": kind, **fields})
            print(line, flush=True)
            print(line, file=log, flush=True)

        process = subprocess.Popen([str(executable)], cwd=game, creationflags=0x00000002,
                                   env={**os.environ, "__COMPAT_LAYER": "WIN2000"})
        record("launch", mode=profile, pid=process.pid, executable_sha256=PINNED_EXE,
               archive_sha256=archives)
        handle, base = None, None
        startup = set()
        traced = False
        traces = {}
        if profile in ("alias", "alias-flat"):
            traces[INITIALIZER_RETURN] = (b"\x68", "registry-ready")
            if profile == "alias":
                traces[CAST_DEBIT] = (b"\xe8", "grun-debit")
        elif profile == "zap-three":
            traces = {site + 3: (b"\xe8", label)
                      for site, label in zip(ZAP_SITES, ("zap-hero", "zap-creature"), strict=True)}
        elif profile == "zap-mass":
            traces[0x6F4C2D] = (b"\xe8", "lightning-damage")
        elif profile == "zap-chain":
            traces[ZAP_SITES[1] + 3] = (b"\xe8", "zap-creature")
        elif profile == "rat-brotherhood":
            traces[0x6F0572] = (b"\xe8", "brotherhood-attach")
            traces[0x6F06F0] = (b"\x64", "brotherhood-activate")
        try:
            while True:
                event = DebugEvent()
                if not api.WaitForDebugEvent(ct.byref(event), 250):
                    error = ct.get_last_error()
                    if error not in (121, 258):
                        raise ct.WinError(error)
                    continue
                status = DEBUG_CONTINUE
                try:
                    if event.kind == 3:
                        file_handle, handle, _, base = event.data.pointers
                        if file_handle:
                            api.CloseHandle(file_handle)
                        if base != IMAGE_BASE:
                            raise ValueError(f"Image base differs from the pinned map: {base:#x}")
                        record("image", base=hex(base))
                        if extension:
                            extension.stage(api, handle, traces, record)
                        else:
                            stage(api, handle, profile, traces, record)
                        for at, (original, _) in traces.items():
                            replace(api, handle, at, original, b"\xcc")
                        traced = True
                    elif event.kind == 6 and event.data.pointers[0]:
                        api.CloseHandle(event.data.pointers[0])
                    elif event.kind == 1:
                        detail = event.data.exception
                        fault = detail.record
                        if detail.first_chance and fault.code in BREAKPOINT_CODES:
                            if traced and fault.address in traces:
                                trace_once(api, handle, event, traces, record, extension)
                                continue
                            if fault.code not in startup:
                                startup.add(fault.code)
                                continue
                        status = DEBUG_PASS
                        evidence = {"code": hex(fault.code), "address": hex(fault.address or 0),
                                    "first_chance": bool(detail.first_chance)}
                        if fault.code == 0xC0000005 and fault.count >= 2:
                            evidence.update(access_kind=fault.info[0], accessed_address=hex(fault.info[1]))
                            evidence.update(exception_context(api, handle, event.tid, base))
                        record("exception", **evidence)
                    elif event.kind == 5:
                        record("exit", code=hex(event.data.exit_code))
                        break
                except BaseException:
                    process.kill()
                    raise
                finally:
                    require(api.ContinueDebugEvent(event.pid, event.tid, status))
        finally:
            if process.poll() is None:
                process.kill()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILE_ARCHIVES)
    parser.add_argument("game", type=Path)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    try:
        run(args.game.resolve(strict=True), args.profile, args.log.resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
