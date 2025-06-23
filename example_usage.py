#!/usr/bin/env python3
"""
PyRocrail Library Usage Examples

This file demonstrates how to use the various Rocrail control objects.
All commands marked with TODO comments need verification against actual Rocrail XML protocol.
"""

import time
from pyrocrail import PyRocrail, Action, Trigger


def locomotive_example(model):
    """Example of locomotive control"""
    try:
        # Get a locomotive by ID (replace 'loco1' with actual ID from your layout)
        loco = model.get_lc('loco1')
        
        # Basic locomotive control
        loco.set_speed(50)  # Set speed to 50%
        loco.set_lights(True)  # Turn on lights
        loco.go_forward(30)  # Go forward at 30% speed
        
        time.sleep(3)
        
        loco.set_speed(0)  # Stop
        loco.set_direction(False)  # Reverse direction
        loco.go_reverse(20)  # Go reverse at 20% speed
        
        time.sleep(2)
        loco.stop()  # Emergency stop
        
        # Function control
        loco.set_function(1, True)  # Turn on function 1 (horn, bell, etc.)
        time.sleep(1)
        loco.set_function(1, False)  # Turn off function 1
        
    except KeyError:
        print("Locomotive 'loco1' not found in model")


def switch_example(model):
    """Example of switch control"""
    try:
        # Get a switch by ID
        switch = model.get_sw('sw1')
        
        # Switch control
        switch.straight()  # Set to straight position
        time.sleep(1)
        switch.turnout()   # Set to turnout position
        time.sleep(1)
        switch.flip()      # Flip to opposite position
        
        # State checking
        print(f"Switch state: {switch.state}")
        
    except KeyError:
        print("Switch 'sw1' not found in model")


def signal_example(model):
    """Example of signal control"""
    try:
        # Get a signal by ID
        signal = model.get_sg('sig1')
        
        # Signal aspects
        signal.red()     # Stop
        time.sleep(1)
        signal.yellow()  # Caution
        time.sleep(1)
        signal.green()   # Go
        
        # Set aspect by name or number
        signal.set_aspect('red')
        signal.set_aspect(1)  # Green
        
        print(f"Signal aspect: {signal.state}")
        
    except KeyError:
        print("Signal 'sig1' not found in model")


def route_example(model):
    """Example of route control"""
    try:
        # Get a route by ID
        route = model.get_st('route1')
        
        # Route control
        if route.is_free():
            route.set()  # Activate the route
            print("Route activated")
        
        time.sleep(2)
        
        route.free()  # Free the route
        print("Route freed")
        
    except KeyError:
        print("Route 'route1' not found in model")


def block_example(model):
    """Example of block control"""
    try:
        # Get a block by ID
        block = model.get_bk('block1')
        
        # Block control
        if block.is_free():
            block.reserve('loco1')  # Reserve for locomotive
            print("Block reserved")
        
        # Check block status
        print(f"Block occupied: {block.is_occupied()}")
        print(f"Block reserved: {block.is_reserved()}")
        print(f"Locomotive in block: {block.get_locomotive()}")
        
        # Free the block
        block.free()
        
    except KeyError:
        print("Block 'block1' not found in model")


def feedback_example(model):
    """Example of feedback sensor control"""
    try:
        # Get feedback sensors
        sensor = model.get_fb('sensor1')
        
        # Feedback control (for testing/simulation)
        sensor.on()   # Simulate sensor activation
        time.sleep(1)
        sensor.off()  # Simulate sensor deactivation
        sensor.flip() # Toggle sensor state
        
        print(f"Sensor state: {sensor.state}")
        
    except KeyError:
        print("Sensor 'sensor1' not found in model")


def output_example(model):
    """Example of output control"""
    try:
        # Get an output by ID
        output = model.get_co('output1')
        
        # Output control
        output.on()   # Turn output on
        time.sleep(1)
        output.off()  # Turn output off
        
    except KeyError:
        print("Output 'output1' not found in model")


def automation_example():
    """Example of automated script execution"""
    def my_automation_script(model):
        """Custom automation script"""
        print("Running automation script...")
        
        # Example: Turn on all feedback sensors sequentially
        for fb_id, fb in model._fb_domain.items():
            fb.on()
            time.sleep(0.1)
            fb.off()
            
        print("Automation script completed")
    
    # Create action with time trigger
    action = Action(my_automation_script, Trigger.TIME)
    return action


def main():
    """Main example function"""
    # Connect to Rocrail (default: localhost:8051)
    rocrail = PyRocrail()
    
    try:
        # Start connection and load model
        rocrail.start()
        
        # System control
        rocrail.power_on()   # Turn power on
        rocrail.auto_on()    # Enable automatic mode
        
        # Wait for model to load
        time.sleep(2)
        
        print("Running control examples...")
        
        # Run examples (uncomment as needed)
        locomotive_example(rocrail.model)
        switch_example(rocrail.model)
        signal_example(rocrail.model)
        route_example(rocrail.model)
        block_example(rocrail.model)
        feedback_example(rocrail.model)
        output_example(rocrail.model)
        
        # Add automation
        automation = automation_example()
        rocrail.add(automation)
        
        # Run for a while
        print("System running... Press Ctrl+C to stop")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Clean shutdown
        rocrail.power_off()
        rocrail.stop()


if __name__ == "__main__":
    main()