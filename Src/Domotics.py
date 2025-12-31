from phue import Bridge  # pyright: ignore[reportMissingImports]

def Bridge_hue():
    """
    Attempts to connect to the Philips Hue Bridge.
    If the connection fails (timeout or network issue), returns a Mock object for debugging.
    """
    bridge_ip = "192.168.1.122"
    try:
        b = Bridge(bridge_ip)
        b.connect()
        print("✅ Successfully connected to Hue Bridge")
        return b
    except Exception as e:
        print(f"⚠️ Simulation Mode: Could not connect to Bridge ({e})")
        
        # This Mock class prevents the rest of your app from crashing
        class HueBridgeMock:
            def set_light(self, *args, **kwargs):
                print(f"[MOCK HUE] Light command received: {args} {kwargs}")
                return True
            def get_api(self):
                # Returns a basic structure if your code checks light status
                return {"lights": {"1": {"state": {"on": True}}}}
        
        return HueBridgeMock()

# The variable name 'pont' or 'bridge' used in your other files
bridge = Bridge_hue()