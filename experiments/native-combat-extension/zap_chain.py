"""Emit the x86 wrapper for the isolated damage-then-return experiment."""

import struct


def chain_code(address):
    code = bytearray()
    labels = {}
    fixups = []

    def emit(hex_bytes):
        code.extend(bytes.fromhex(hex_bytes))

    def label(name):
        labels[name] = address + len(code)

    def jump(opcode, target):
        emit(opcode)
        fixups.append((len(code), target))
        code.extend(b"\0" * 4)

    emit("55 8b ec 53 56 57 83 ec 10")  # EBP frame, save EBX/ESI/EDI, four locals
    emit("8b f1 33 ff")                 # ESI=this; EDI=optional initial creature
    emit("8b 45 08 8b 10 85 d2")        # first argument is the parameter vector
    jump("0f 84", "zap")
    emit("3b 50 04")
    jump("0f 83", "zap")                # empty vector
    emit("8b 1a")                       # EBX = selected target index
    jump("e8", "candidate")
    emit("8b f8 85 ff")
    jump("0f 84", "zap")
    emit("8b 47 10 89 45 f0")           # save encounter identity
    emit("8b 47 18 89 45 ec")           # save controller
    emit("8b 47 20 89 45 e8")           # save card identity

    label("zap")
    emit("ff 75 0c ff 75 08 8b ce")
    jump("e8", 0x6F2160)                # original Zap, same this and two arguments
    emit("89 45 e4 84 c0")
    jump("0f 84", "return")
    emit("85 ff")
    jump("0f 84", "return")
    jump("e8", "candidate")             # resolve the index again after native damage
    emit("3b c7")
    jump("0f 85", "return")
    emit("8b 50 10 3b 55 f0")
    jump("0f 85", "return")
    emit("8b 50 18 3b 55 ec")
    jump("0f 85", "return")
    emit("8b 50 20 3b 55 e8")
    jump("0f 85", "return")
    emit("ff 75 0c ff 75 08 8b ce")
    label("unsummon")
    jump("e8", 0x6CC9C0)                # original Unsummon effect, no second card cast

    label("return")
    emit("8b 45 e4 83 c4 10 5f 5e 5b 5d c2 08 00")

    label("candidate")
    emit("83 fb 02")
    jump("0f 82", "invalid")            # indices 0 and 1 are heroes
    emit("8b 4e 0c 8b 41 0c 8b 51 10")  # battle's index vector begin/end
    emit("2b d0 c1 ea 02 3b da")
    jump("0f 83", "invalid")
    emit("8b 04 98 85 c0")
    jump("0f 84", "invalid")
    emit("80 78 30 00")
    jump("0f 85", "invalid")            # native removal flag
    emit("8b 50 18 3b 56 14")
    jump("0f 84", "invalid")            # friendly current controller
    emit("3b 50 1c")
    jump("0f 85", "invalid")            # owner and controller must agree
    emit("8b 50 28 8b 48 3c 3b 51 04")
    jump("0f 8d", "invalid")            # accumulated damage >= current toughness
    emit("c3")
    label("invalid")
    emit("33 c0 c3")

    for operand, target in fixups:
        destination = labels[target] if isinstance(target, str) else target
        struct.pack_into("<I", code, operand, (destination - (address + operand + 4)) & 0xFFFFFFFF)
    return bytes(code), labels["unsummon"]
