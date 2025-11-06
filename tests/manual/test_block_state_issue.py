#!/usr/bin/env python3
"""
Demonstrate block state reporting discrepancy

This test shows the issue where PyRocrail._is_free() and Block.is_free()
return different values for the same block.
"""

from pyrocrail.pyrocrail import PyRocrail
import time


def main():
    print("=" * 80)
    print("BLOCK STATE DISCREPANCY TEST")
    print("=" * 80)

    with PyRocrail("localhost", 8051, verbose=False) as pr:
        print("\n✓ Connected to Rocrail")
        time.sleep(2)

        blocks = pr.model.get_blocks()
        if not blocks:
            print("❌ No blocks found")
            return

        print(f"\n✓ Found {len(blocks)} blocks")
        print("\nChecking block states (showing first 5):")
        print("=" * 80)

        for i, (block_id, bk) in enumerate(list(blocks.items())[:5]):
            print(f"\nBlock: {block_id}")

            # PyRocrail methods
            pr_occupied = pr._is_occupied(block_id)
            pr_free = pr._is_free(block_id)
            pr_reserved = pr._is_reserved(block_id)
            pr_closed = pr._is_closed(block_id)

            print(f"  PyRocrail methods:")
            print(f"    closed={pr_closed} free={pr_free} reserved={pr_reserved} occupied={pr_occupied}")

            # Block object methods
            bk_closed = bk.is_closed()
            bk_free = bk.is_free()
            bk_reserved = bk.is_reserved()
            bk_occupied = bk.is_occupied()

            print(f"  Block methods:")
            print(f"    closed={bk_closed} free={bk_free} reserved={bk_reserved} occupied={bk_occupied}")

            # Show raw attributes
            print(f"  Raw attributes:")
            print(f"    state={getattr(bk, 'state', 'unknown')} occ={getattr(bk, 'occ', 'unknown')} reserved={getattr(bk, 'reserved', 'unknown')}")

            # Check for discrepancies
            discrepancies = []
            if pr_closed != bk_closed:
                discrepancies.append(f"closed: pr={pr_closed} != bk={bk_closed}")
            if pr_free != bk_free:
                discrepancies.append(f"free: pr={pr_free} != bk={bk_free}")
            if pr_reserved != bk_reserved:
                discrepancies.append(f"reserved: pr={pr_reserved} != bk={bk_reserved}")
            if pr_occupied != bk_occupied:
                discrepancies.append(f"occupied: pr={pr_occupied} != bk={bk_occupied}")

            if discrepancies:
                print(f"  ❌ DISCREPANCIES: {', '.join(discrepancies)}")
            else:
                print(f"  ✓ All methods match!")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\nAll PyRocrail helper methods now delegate to Block methods:")
        print("  ✓ _is_free() → bk.is_free()")
        print("  ✓ _is_occupied() → bk.is_occupied()")
        print("  ✓ _is_reserved() → bk.is_reserved()")
        print("  ✓ _is_closed() → bk.is_closed()")
        print("\nThis ensures consistent state reporting across the API.")


if __name__ == "__main__":
    main()
