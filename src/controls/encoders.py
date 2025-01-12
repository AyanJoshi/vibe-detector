"""
Rotary encoder interface for volume and track control
"""
import RPi.GPIO as GPIO
import time
from threading import Thread, Event

class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin, sw_pin, callback=None):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.callback = callback
        self.last_counter = 0
        self.counter = 0
        self.last_clk_state = None
        self.button_pressed = False
        self.setup_gpio()
        
    def setup_gpio(self):
        """Setup GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Add event detection
        GPIO.add_event_detect(self.clk_pin, GPIO.BOTH, callback=self._rotation_decode)
        GPIO.add_event_detect(self.sw_pin, GPIO.FALLING, callback=self._button_callback, bouncetime=300)
        
    def _rotation_decode(self, channel):
        """Decode rotation direction"""
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        
        if clk_state != self.last_clk_state:
            if dt_state != clk_state:
                self.counter += 1
            else:
                self.counter -= 1
                
            if self.callback:
                direction = 'clockwise' if self.counter > self.last_counter else 'counterclockwise'
                self.callback(direction, False)
                
            self.last_counter = self.counter
        self.last_clk_state = clk_state
        
    def _button_callback(self, channel):
        """Handle button press"""
        if self.callback:
            self.callback(None, True)
            
    def cleanup(self):
        """Cleanup GPIO"""
        GPIO.remove_event_detect(self.clk_pin)
        GPIO.remove_event_detect(self.sw_pin)
        GPIO.cleanup([self.clk_pin, self.dt_pin, self.sw_pin])