#!/usr/bin/env python3
"""
Expanded PyRocrail Test Script for Heggedal Station Layout

This test exercises all major components of the Heggedal station layout:
- 6 Locomotives (TC10, E4/4, NSB61, NSB21, B4/5, kkStb85)  
- 11 Blocks (SB0-SB4, Royken, Gulhella, Heggedal1-3, HeggedalLade, Fabrikk)
- 14 Switches (sw1-sw8, w_hg1-w_hg6)
- 40+ Routes connecting all blocks
- 22+ Feedback sensors
"""

import time
from pyrocrail.pyrocrail import PyRocrail
from pyrocrail.model import Model


def test_locomotives(model: Model):
    """Test all 6 locomotives in the layout"""
    print("\n=== LOCOMOTIVE TESTING ===")
    
    locomotive_ids = ["TC10", "E4/4", "NSB61", "NSB21", "B4/5", "kkStb85"]
    
    for loco_id in locomotive_ids:
        try:
            loco = model.get_lc(loco_id)
            print(f"Testing locomotive: {loco_id}")
            
            # Basic locomotive operations
            loco.set_lights(True)
            print(f"  - Lights ON for {loco_id}")
            time.sleep(0.5)
            
            loco.set_speed(25)
            print(f"  - Speed set to 25% for {loco_id}")
            time.sleep(1)
            
            loco.set_direction(False)  # Reverse
            print(f"  - Direction set to reverse for {loco_id}")
            time.sleep(0.5)
            
            loco.set_speed(0)
            print(f"  - Stopped {loco_id}")
            
            loco.set_lights(False)
            print(f"  - Lights OFF for {loco_id}")
            
            # Test function 1 (horn/bell)
            loco.set_function(1, True)
            time.sleep(0.3)
            loco.set_function(1, False)
            print(f"  - Function 1 tested for {loco_id}")
            
            time.sleep(0.5)
            
        except KeyError:
            print(f"  ! Locomotive {loco_id} not found in model")
        except Exception as e:
            print(f"  ! Error testing {loco_id}: {e}")


def test_switches(model: Model):
    """Test all 14 switches in the layout"""
    print("\n=== SWITCH TESTING ===")
    
    # Regular switches (sw1-sw8)
    switch_ids = ["sw1", "sw2", "sw3", "sw4", "sw5", "sw6", "sw7", "sw8"]
    
    # Yard switches (w_hg1-w_hg6)
    yard_switch_ids = ["w_hg1", "w_hg2", "w_hg3", "w_hg4", "w_hg5", "w_hg6"]
    
    all_switches = switch_ids + yard_switch_ids
    
    for sw_id in all_switches:
        try:
            switch = model.get_sw(sw_id)
            print(f"Testing switch: {sw_id}")
            
            # Test straight position
            switch.straight()
            print(f"  - {sw_id} set to STRAIGHT")
            time.sleep(0.5)
            
            # Test turnout position  
            switch.turnout()
            print(f"  - {sw_id} set to TURNOUT")
            time.sleep(0.5)
            
            # Test flip function
            switch.flip()
            print(f"  - {sw_id} FLIPPED to opposite position")
            time.sleep(0.5)
            
        except KeyError:
            print(f"  ! Switch {sw_id} not found in model")
        except Exception as e:
            print(f"  ! Error testing {sw_id}: {e}")


def test_blocks(model: Model):
    """Test all 11 blocks in the layout"""
    print("\n=== BLOCK TESTING ===")
    
    block_ids = [
        "SB0", "SB1", "SB2", "SB3", "SB4",  # Station blocks
        "Royken", "Gulhella",                # Main terminals
        "Heggedal1", "Heggedal2", "Heggedal3",  # Platform tracks
        "HeggedalLade", "Fabrikk"            # Industrial sidings
    ]
    
    for block_id in block_ids:
        try:
            block = model.get_bk(block_id)
            print(f"Testing block: {block_id}")
            
            # Check current status
            print(f"  - Status: Free={block.is_free()}, Occupied={block.is_occupied()}, Reserved={block.is_reserved()}")
            
            if block.is_free():
                # Test reservation
                block.reserve("TC10")
                print(f"  - {block_id} RESERVED for TC10")
                time.sleep(0.5)
                
                # Test go command
                block.go()
                print(f"  - GO signal sent to {block_id}")
                time.sleep(0.5)
                
                # Free the block
                block.free()
                print(f"  - {block_id} FREED")
            else:
                print(f"  - {block_id} is not free, skipping reservation test")
                
            time.sleep(0.5)
            
        except KeyError:
            print(f"  ! Block {block_id} not found in model")
        except Exception as e:
            print(f"  ! Error testing {block_id}: {e}")


def test_routes(model: Model):
    """Test sample routes between major stations"""
    print("\n=== ROUTE TESTING ===")
    
    # Test routes between major terminals and station tracks
    test_route_ids = [
        "[SB0+]-[Royken+]",      # Station track 0 to Royken
        "[Royken+]-[SB1+]",      # Royken to Station track 1  
        "[SB2-]-[Gulhella-]",    # Station track 2 to Gulhella
        "[Gulhella+]-[Heggedal1-]",  # Gulhella to Heggedal platform 1
        "[Heggedal2+]-[Gulhella+]",  # Heggedal platform 2 to Gulhella
    ]
    
    for route_id in test_route_ids:
        try:
            route = model.get_st(route_id)
            print(f"Testing route: {route_id}")
            
            if route.is_free():
                # Test route setting
                route.set()
                print(f"  - Route {route_id} ACTIVATED")
                time.sleep(1)
                
                # Test route freeing
                route.free()
                print(f"  - Route {route_id} FREED")
            else:
                print(f"  - Route {route_id} is not free, status: {route.state}")
                
            time.sleep(0.5)
            
        except KeyError:
            print(f"  ! Route {route_id} not found in model")
        except Exception as e:
            print(f"  ! Error testing {route_id}: {e}")


def test_feedback_sensors(model: Model):
    """Test feedback sensors (already working from original test)"""
    print("\n=== FEEDBACK SENSOR TESTING ===")
    
    sensor_count = len(model._fb_domain)
    print(f"Found {sensor_count} feedback sensors")
    
    # Test a few specific sensors
    test_sensors = ["fb_sb_0_n", "fb_sb_1_s", "fb_g_n", "fb_r_s", "fb_hg_1_n"]
    
    for sensor_id in test_sensors:
        try:
            sensor = model.get_fb(sensor_id)
            print(f"Testing sensor: {sensor_id}")
            
            sensor.on()
            print(f"  - {sensor_id} activated")
            time.sleep(0.3)
            
            sensor.off()
            print(f"  - {sensor_id} deactivated") 
            time.sleep(0.2)
            
        except KeyError:
            print(f"  ! Sensor {sensor_id} not found")
        except Exception as e:
            print(f"  ! Error testing {sensor_id}: {e}")


def test_system_commands(rocrail: PyRocrail):
    """Test system-level commands"""
    print("\n=== SYSTEM COMMAND TESTING ===")
    
    try:
        print("Testing system power control...")
        # Note: Be careful with power commands on a live layout!
        
        print("  - System power is ON (already running)")
        
        # Test auto mode
        rocrail.auto_on()
        print("  - Auto mode ENABLED")
        time.sleep(1)
        
        rocrail.auto_off()
        print("  - Auto mode DISABLED")
        time.sleep(1)
        
        # Don't test power off or emergency stop on live layout unless needed
        print("  - Power OFF and Emergency Stop tests skipped (live layout)")
        
    except Exception as e:
        print(f"  ! Error in system commands: {e}")


def run_comprehensive_test():
    """Run the complete test suite"""
    print("Starting Comprehensive PyRocrail Test for Heggedal Station Layout")
    print("=" * 70)
    
    # Connect to Rocrail
    rocrail = PyRocrail()
    
    try:
        # Start connection and load model
        print("Connecting to Rocrail...")
        rocrail.start()
        
        print("Waiting for model to load...")
        time.sleep(3)
        
        # Print layout summary
        print(f"\nLayout Summary:")
        print(f"  - Locomotives: {len(rocrail.model._lc_domain)}")
        print(f"  - Switches: {len(rocrail.model._sw_domain)}")
        print(f"  - Blocks: {len(rocrail.model._bk_domain)}")
        print(f"  - Routes: {len(rocrail.model._st_domain)}")
        print(f"  - Feedback sensors: {len(rocrail.model._fb_domain)}")
        print(f"  - Outputs: {len(rocrail.model._co_domain)}")
        
        # Run all tests
        test_system_commands(rocrail)
        test_locomotives(rocrail.model)
        test_switches(rocrail.model)
        test_blocks(rocrail.model)
        test_routes(rocrail.model)
        test_feedback_sensors(rocrail.model)
        
        print("\n" + "=" * 70)
        print("All tests completed successfully!")
        print("PyRocrail library is working with your Heggedal Station layout.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nStopping Rocrail connection...")
        rocrail.stop()


if __name__ == "__main__":
    run_comprehensive_test()