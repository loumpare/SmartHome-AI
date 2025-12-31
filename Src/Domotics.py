from phue import Bridge  # pyright: ignore[reportMissingImports]

def obtenir_pont():
    BRIDGE_IP = "192.168.1.122"
    b = Bridge(BRIDGE_IP)
    try:
        b.connect()
        return b
    except Exception as e:
        print(f"Erreur Pont : {e}")
        return None

pont = obtenir_pont()