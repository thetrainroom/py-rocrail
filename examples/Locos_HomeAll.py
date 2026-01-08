#!/usr/bin/env python3
# ruff: noqa: N806

import sys
import os
import time
import msvcrt  # Windows only

print("🔍 DEBUG: Starting Locos_HomeAll.py")

# Absolute path of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("📂 Script location:", BASE_DIR)

# Path to py-rocrail/src
PY_ROCRAIL_SRC = os.path.abspath(os.path.join(BASE_DIR, "..", "py-rocrail", "src"))
print("📦 Expected py-rocrail/src path:", PY_ROCRAIL_SRC)

# Validate directory structure
if not os.path.isdir(PY_ROCRAIL_SRC):
    print("❌ py-rocrail/src directory NOT found!")
else:
    print("✅ py-rocrail/src directory exists")

# Check pyrocrail package
PYROCRAIL_PKG = os.path.join(PY_ROCRAIL_SRC, "pyrocrail")
if not os.path.isdir(PYROCRAIL_PKG):
    print("❌ 'pyrocrail' package NOT found in src!")
else:
    print("✅ 'pyrocrail' package found")

# Add src to sys.path
if PY_ROCRAIL_SRC not in sys.path:
    sys.path.insert(0, PY_ROCRAIL_SRC)
    print("➕ Added src to sys.path")
else:
    print("ℹ️ src already in sys.path")

print("\n📜 sys.path:")
for p in sys.path:
    print("   ", p)

# Try importing
try:
    from pyrocrail import PyRocrail

    print("\n✅ SUCCESS: PyRocrail imported correctly\n")
except ImportError as e:
    print("\n❌ FAILED to import PyRocrail")
    print("Reason:", e)
    print("\n🔧 CHECK:")
    print("  - py-rocrail/src/pyrocrail/__init__.py exists")
    print("  - No typo in folder names")
    print("  - Correct Python interpreter")
    sys.exit(1)

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ----------------------------
# Terminal helpers
# ----------------------------
def clear_screen():
    print("\033[2J\033[H", end="")  # clear + move cursor home


def color(text, code):
    return f"{code}{text}{RESET}"


# ----------------------------
# Utility functions
# ----------------------------
def kb_hit():
    """Return pressed key if available, else None"""
    if msvcrt.kbhit():
        return msvcrt.getwch().lower()
    return None


def send_train_to_block(lc_id, lc, bk, block, goto_done, entry, delay=0.3):
    print(color(f"→ {lc_id}: sending gotoblock -> {block}", RED))

    # Ensure abort_reason is cleared unless we set it now
    entry["abort_reason"] = entry.get("abort_reason", None)

    # read current state
    is_free = bk.is_free()
    is_reserved = bk.is_reserved()
    res_by = str(getattr(bk, "locid", None) or "-")
    is_occupied = bk.is_occupied()

    print(f"Block status -> Free: {is_free}, Reserved: {is_reserved}, Reserved by: {res_by}, Occupied: {is_occupied}")

    # ----------------------------
    # ABORT CONDITIONS
    # ----------------------------
    if is_occupied and res_by not in ["-", "None", lc_id]:
        msg = f"BLOCKED by {res_by}"
        entry["abort_reason"] = msg
        print(color(f"✖ {block}: {msg}. Aborting send of {lc_id}.", RED))
        goto_done[lc_id] = False
        return

    if is_reserved and res_by not in ["-", "None", lc_id]:
        msg = f"RESERVED by {res_by}"
        entry["abort_reason"] = msg
        print(color(f"✖ {block}: {msg}. Aborting send of {lc_id}.", RED))
        goto_done[lc_id] = False
        return

    # If we reach here, block is not reserved/occupied by another loco
    entry["abort_reason"] = None

    # ----------------------------
    # NORMAL SEND PROCESS
    # ----------------------------
    # release possible reservations for this loco
    try:
        bk.free_override()
    except Exception:
        # ignore; continue with fresh state check
        pass

    time.sleep(1.0)

    # refresh state AFTER attempting free_override
    is_free = bk.is_free()
    is_reserved = bk.is_reserved()
    res_by = str(getattr(bk, "locid", None) or "-")
    is_occupied = bk.is_occupied()

    print(f"Block status -> Free: {is_free}, Reserved: {is_reserved}, Reserved by: {res_by}, Occupied: {is_occupied}")

    # final safety: if another loco appeared in the short window, abort and set reason
    if is_occupied and res_by not in ["-", "None", lc_id]:
        msg = f"BLOCKED by {res_by}"
        entry["abort_reason"] = msg
        print(color(f"✖ {block}: {msg} (appeared). Aborting send of {lc_id}.", RED))
        goto_done[lc_id] = False
        return

    if is_reserved and res_by not in ["-", "None", lc_id]:
        msg = f"RESERVED by {res_by}"
        entry["abort_reason"] = msg
        print(color(f"✖ {block}: {msg} (appeared). Aborting send of {lc_id}.", RED))
        goto_done[lc_id] = False
        return

    # proceed to request route and start
    print(color(f"✓ {lc_id}: block is usable, sending goto {block}", GREEN))
    try:
        lc.gotoblock(block)
        time.sleep(0.08)
        lc.go()
    except Exception:
        try:
            lc.command("go", {"block": block})
        except Exception:
            pass

    # mark that we attempted a goto for this loco during this homing run
    goto_done[lc_id] = True

    # mark HOME_ONCE blocks as sent
    if block in ("BN9", "BN10", "BN11"):
        entry["home_sent"] = True

    time.sleep(delay)
    return


# ----------------------------
# Dashboard rendering
# ----------------------------
def render_status_table(trains_to_process, lc_state, goto_done, pr):
    model = pr.model
    clear_screen()
    print(BOLD + "CURRENT LOCOMOTIVE STATUS" + RESET)
    print()

    # Column widths
    W_LOCO = 16
    W_BLOCK = 7
    W_SPD = 4
    W_HOME = 7
    W_TARGET = 7
    W_STAGE = 6
    W_STATUS = 30

    # Top border
    print(
        "╔"
        + "═" * (W_LOCO + 2)
        + "╦"
        + "═" * (W_BLOCK + 2)
        + "╦"
        + "═" * (W_SPD + 2)
        + "╦"
        + "═" * (W_HOME + 2)
        + "╦"
        + "═" * (W_TARGET + 2)
        + "╦"
        + "═" * (W_STAGE + 2)
        + "╦"
        + "═" * (W_STATUS + 2)
        + "╗"
    )

    # Header
    print(
        f"║ {'Loco':<{W_LOCO}} ║"
        f" {'Block':<{W_BLOCK}} ║"
        f" {'Spd':>{W_SPD}} ║"
        f" {'Home':<{W_HOME}} ║"
        f" {'Target':<{W_TARGET}} ║"
        f" {'Stage':<{W_STAGE}} ║"
        f" {'Status':<{W_STATUS}} ║"
    )

    # Header separator
    print(
        "╠"
        + "═" * (W_LOCO + 2)
        + "╬"
        + "═" * (W_BLOCK + 2)
        + "╬"
        + "═" * (W_SPD + 2)
        + "╬"
        + "═" * (W_HOME + 2)
        + "╬"
        + "═" * (W_TARGET + 2)
        + "╬"
        + "═" * (W_STAGE + 2)
        + "╬"
        + "═" * (W_STATUS + 2)
        + "╣"
    )

    rows = list(trains_to_process.items())
    for i, (lc_id, entry) in enumerate(rows):
        lc = entry["lc"]
        home = entry["home"]

        # Target / Stage
        target = entry.get("target", home)
        stage = entry.get("stage", "HOME").upper()

        # Locomotive state
        state = lc_state.get(lc_id, {})
        cur = state.get("blockid") or getattr(lc, "blockid", "-") or "-"
        spd = getattr(lc, "V", 0)
        nxt = state.get("dest") or state.get("last_dest") or "-"

        # Block info
        try:
            bk = model.get_bk(home)
            is_res = bk.is_reserved()
            is_occ = bk.is_occupied()
            res_by = getattr(bk, "locid", "-") or "-"
        except Exception as e:
            print(f"render_status_table: Block Info Error: {repr(e)}")
            is_res = False
            is_occ = False
            res_by = "-"

        # Build status
        if entry.get("arrived"):
            raw_status = "ARRIVED"
            status = color(raw_status, GREEN)
        elif entry.get("abort_reason"):
            raw_status = entry["abort_reason"]
            status = color(raw_status, RED)
        elif entry.get("home_sent") and entry.get("stage") == "HOME":
            raw_status = "HOME SENT (once)"
            status = color(raw_status, CYAN)
        elif cur == home and spd > 0:
            raw_status = "IN HOME (moving)"
            status = color(raw_status, YELLOW)
        elif is_res and res_by == lc_id and not goto_done.get(lc_id, False):
            # reserved by this loco but not yet marked as sent
            raw_status = "RESERVED (now)"
            status = color(raw_status, GREEN)
        elif goto_done.get(lc_id, False) and is_res and res_by == lc_id:
            raw_status = "SENT (reserved)"
            status = color(raw_status, GREEN)
        elif goto_done.get(lc_id, False) and is_res and res_by != lc_id:
            raw_status = f"SENT (reserved by {res_by})"
            status = color(raw_status, YELLOW)
        elif is_res and res_by != lc_id:
            raw_status = f"WAIT (reserved {res_by})"
            status = color(raw_status, YELLOW)
        elif is_occ:
            raw_status = "WAIT (occupied)"
            status = color(raw_status, YELLOW)
        elif nxt != "-" and not goto_done.get(lc_id, False):
            raw_status = "PENDING (will send)"
            status = color(raw_status, CYAN)
        else:
            raw_status = "PENDING"
            status = color(raw_status, CYAN)

        # Pad raw text before coloring
        padded_raw = f"{raw_status:<{W_STATUS}}"
        status_colored = status.replace(raw_status, padded_raw)

        # Print row
        print(f"║ {lc_id:<{W_LOCO}} ║ {cur:<{W_BLOCK}} ║ {spd:>{W_SPD}} ║ {home:<{W_HOME}} ║ {target:<{W_TARGET}} ║ {stage:<{W_STAGE}} ║ {status_colored} ║")

        # Row separator or bottom border
        if i < len(rows) - 1:
            print(
                "╠"
                + "═" * (W_LOCO + 2)
                + "╬"
                + "═" * (W_BLOCK + 2)
                + "╬"
                + "═" * (W_SPD + 2)
                + "╬"
                + "═" * (W_HOME + 2)
                + "╬"
                + "═" * (W_TARGET + 2)
                + "╬"
                + "═" * (W_STAGE + 2)
                + "╬"
                + "═" * (W_STATUS + 2)
                + "╣"
            )
        else:
            print(
                "╚"
                + "═" * (W_LOCO + 2)
                + "╩"
                + "═" * (W_BLOCK + 2)
                + "╩"
                + "═" * (W_SPD + 2)
                + "╩"
                + "═" * (W_HOME + 2)
                + "╩"
                + "═" * (W_TARGET + 2)
                + "╩"
                + "═" * (W_STAGE + 2)
                + "╩"
                + "═" * (W_STATUS + 2)
                + "╝"
            )
    print()


# ----------------------------
# Main homing routine
# ----------------------------
def send_locomotives_home(pr: PyRocrail, lc_state, goto_done, max_cycles: int = 40, stop_flag=lambda: False):
    """Send all locomotives to their home blocks."""
    model = pr.model
    model.get_blocks()
    cycletime = 5.0

    locos = model.get_locomotives()
    trains_to_process = {}
    for lc_id, lc in locos.items():
        # skip any specific loco if you want
        # if lc_id == "Ce6/8-II-14282":
        #    continue

        home = lc.home
        speed = getattr(lc, "V", 0)
        cur = getattr(lc, "blockid", "unknown")

        if not home:
            continue

        is_at_home = cur == home and speed == 0
        if not is_at_home:
            trains_to_process[lc_id] = {"lc": lc, "home": home, "arrived": False, "abort_reason": None, "target": home, "stage": "HOME", "home_sent": False}

    nb_trains = len(trains_to_process)
    if nb_trains == 0:
        print("No trains need to return home.")
        return

    # main cycle loop
    for cycle in range(1, max_cycles + 1):
        # check for 'q' press to abort
        key = kb_hit()
        if key == "q":
            print(color("⏹ Homing aborted by user.", YELLOW))
            break

        # Update target / stage for BN8 pre-home logic
        for lc_id, entry in trains_to_process.items():
            lc = entry["lc"]
            home = entry["home"]
            cur_block = getattr(lc, "blockid", "-")
            state = lc_state.get(lc_id, {})
            dest_block = state.get("dest") or state.get("last_dest")

            if home in ["BN9", "BN10", "BN11"]:
                if dest_block == home:
                    entry["target"] = home
                    entry["stage"] = "HOME"
                elif cur_block == "BN8":
                    entry["target"] = home
                    entry["stage"] = "HOME"
                elif not entry["home_sent"] and dest_block not in ("BN8", home):
                    entry["target"] = "BN8"
                    entry["stage"] = "PRE"
            else:
                entry["target"] = home
                entry["stage"] = "HOME"

        render_status_table(trains_to_process, lc_state, goto_done, pr)
        print(f"Locos_Home - Cycle {cycle}/{max_cycles} - trains: {nb_trains}")

        # Inspect and decide actions
        for lc_id, entry in trains_to_process.items():
            lc = entry["lc"]
            home = entry["home"]
            target = entry.get("target", home)

            if entry["arrived"]:
                continue

            cur = getattr(lc, "blockid", "unknown")
            speed = getattr(lc, "V", 0)

            # get fresh block object
            try:
                bk = model.get_bk(target)
                is_free = bk.is_free()
                is_reserved = bk.is_reserved()
                is_occupied = bk.is_occupied()
            except Exception as e:
                print(f"send_locomotives_home: Refresh Error: {repr(e)}")
                is_free = False
                is_reserved = False
                is_occupied = False

            # Arrival checks
            if cur == home and speed == 0:
                entry["arrived"] = True
                entry["home_sent"] = False
                entry["abort_reason"] = None
                continue

            # --------------------------------------------------
            # Skip resend for HOME_ONCE blocks
            # --------------------------------------------------
            if target in ("BN9", "BN10", "BN11") and entry["home_sent"]:
                continue

            # --------------------------------------------------
            # Normal resend logic
            # --------------------------------------------------
            if speed == 0 and cur != target:
                print(f"send gotoblock to {target} once more for {lc_id}")
                lc.gotoblock(target)

            if cur == target and speed > 0:
                continue

            if is_free:
                send_train_to_block(lc_id, lc, bk, target, goto_done, entry)
                continue

            if is_reserved:
                if goto_done.get(lc_id, False):
                    continue
                else:
                    send_train_to_block(lc_id, lc, bk, target, goto_done, entry)
                    continue

            if is_occupied:
                continue

            send_train_to_block(lc_id, lc, bk, target, goto_done, entry)

        time.sleep(cycletime)

        # check arrivals
        arrival_changed = False
        for lc_id, entry in trains_to_process.items():
            if entry["arrived"]:
                continue
            lc = entry["lc"]
            cur = getattr(lc, "blockid", "")
            speed = getattr(lc, "V", 0)
            home = entry["home"]
            if cur == home and speed == 0:
                entry["arrived"] = True
                entry["home_sent"] = False
                entry["abort_reason"] = None
                arrival_changed = True

        # redraw table immediately if any loco arrived
        if arrival_changed:
            render_status_table(trains_to_process, lc_state, goto_done, pr)

        arrived_count = sum(1 for e in trains_to_process.values() if e["arrived"])

        # stop early if all arrived
        if arrived_count == nb_trains:
            render_status_table(trains_to_process, lc_state, goto_done, pr)
            print(color("🎉 All trains have arrived at home.", GREEN))
            break

    print()
    for lc_id, entry in trains_to_process.items():
        if not entry["arrived"]:
            lc = entry["lc"]
            print(color(f"⚠️ Train not arrived: {lc_id} (current: {getattr(lc,'blockid','?')} home: {entry['home']})", YELLOW))


# ----------------------------
# Controller class
# ----------------------------
class HomeController:
    def __init__(self, host="localhost", port=8051):
        self.pr = PyRocrail(host, port, "verbose")
        self.lc_state = {}
        self.bk_state = {}
        self.running = False
        self.goto_done = {}

    def start_connection(self):
        self.pr.start()
        self.running = True

        def rr_update(kind, obj_id, obj):
            if kind == "lc":
                cur = getattr(obj, "blockid", None)
                dest = getattr(obj, "destblockid", None)
                if obj_id not in self.lc_state:
                    self.lc_state[obj_id] = {"blockid": None, "dest": None, "last_dest": None}
                self.lc_state[obj_id]["blockid"] = cur
                self.lc_state[obj_id]["dest"] = dest
                if dest:
                    self.lc_state[obj_id]["last_dest"] = dest
            elif kind == "bk":
                reserved_by = getattr(obj, "locid", None) or getattr(obj, "res", None) or getattr(obj, "resid", None)
                occ_attr = getattr(obj, "occ", None)
                try:
                    is_occupied = obj.is_occupied()
                except Exception:
                    is_occupied = bool(occ_attr)
                try:
                    is_reserved = obj.is_reserved()
                except Exception:
                    is_reserved = reserved_by is not None
                try:
                    is_free = obj.is_free()
                except Exception:
                    is_free = not is_occupied and not is_reserved
                self.bk_state[obj_id] = {
                    "reserved_by": reserved_by,
                    "is_occupied": is_occupied,
                    "is_reserved": is_reserved,
                    "is_free": is_free,
                }

        self.pr.model.change_callback = rr_update
        print(color("✅ Rocrail connection established.", GREEN))

    def start_homing(self, max_cycles=100):
        if not self.running:
            print(color("❌ Connection not started yet!", RED))
            return
        self.goto_done = {}
        send_locomotives_home(self.pr, self.lc_state, self.goto_done, max_cycles=max_cycles)

    def stop(self):
        try:
            self.pr.stop()
        except Exception:
            pass
        self.running = False
        print(color("🛑 Rocrail connection stopped.", YELLOW))


# ----------------------------
# Script entry point
# ----------------------------
if __name__ == "__main__":
    controller = HomeController()
    controller.start_connection()

    print("\nReady. Type 'h' + Enter to start homing, 'q' + Enter to quit.")

    while True:
        cmd = input("> ").strip().lower()
        if cmd == "h":
            controller.start_homing()
            print("\nReady. Type 'h' + Enter to start homing, 'q' + Enter to quit.")
        elif cmd == "q":
            controller.stop()
            break
        else:
            print("Commands: h=start homing, q=quit")
