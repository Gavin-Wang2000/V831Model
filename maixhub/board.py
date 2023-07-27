import os
from .trans import tr

# TODO: get board name from maixpy3
def get_board_name():
    '''
        @return None or (series, cpu_name, board_name)
    '''
    try:
        with open("/sys/firmware/devicetree/base/soc@03000000/vind@0/sensor@0/sensor0_mname", "r") as f:
            sensor_name = f.read().strip()
        with open("/sys/firmware/devicetree/base/soc@03000000/lcd0@01c0c000/lcd_driver_name", "r") as f:
            lcd_driver_name = f.read().strip()
        if "sp2305_mipi" in sensor_name and "st7789v_cpu" in lcd_driver_name:
            return ("m2", "v831", "dock")
        if "ov9732_mipi" in sensor_name and "st7789v_cpu" in lcd_driver_name:
            return ("m2", "v831", "cam")
    except Exception:
        pass
    return None

def get_ip(ifname = "wlan0"):
    import socket
    import fcntl
    import struct
    ifname = ifname.encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
        return ip
    except Exception as e:
        pass
    return None

def connect_wifi(ssid, passwd):
    ok = False
    msg = tr("Connect failed !")
    conf = '''
    network={{
        ssid="{}"
        psk="{}"
    }}
'''.format(ssid, passwd)
    with open("/etc/wpa_supplicant.conf", "w") as f:
        f.write(conf)
    with open("/root/wpa_supplicant.conf", "w") as f:
        f.write(conf)
    try:
        os.system("/etc/init.d/S40network restart")
        # os.system("/sbin/ifconfig wlan0 down && killall wpa_supplicant && killall udhcpc")
        # os.system('/sbin/ifconfig wlan0 up && sleep 1 && sh -c "wpa_supplicant -c /root/wpa_supplicant.conf -iwlan0 -B >/dev/null 2>&1 &" && sleep 1 && sh -c "udhcpc -iwlan0 -b >/dev/null 2>&1 &" &')
    except Exception:
        return ok, msg
    return True, ""

def is_support_model_platform(platform):
    boards = {
        "awnn": [
            {
                "id": "m2-v831-dock",
                "name": {
                "zh": "MAIX-II-Dock",
                "en": "MAIX-II-Dock"
                }
            },
            {
                "id": "m2-v831-cam",
                "name": {
                "zh": "MaixCam V831",
                "en": "MaixCam V831"
                }
            },
        ],
        "nncase": [
            {
                "id": "m1-k210-any",
                "name": {
                "zh": "MAIX-I k210 系列开发板",
                "en": "MAIX-I k210 series boards"
                }
            }
        ],
        "ncnn": [],
        "aipu": [
            {
                "id": "m2-r329-sense",
                "name": {
                "zh": "MAIX-II 系列 MaixSense 开发板",
                "en": "MAIX-II series MaixSense board"
                }
            }
        ]
    }
    boards = boards.get(platform, [])
    series, cpu, board_name = get_board_name()
    for board in boards:
        s, c, b = board["id"].split("-")
        if s == series and c == cpu:
            if b == board_name or b == "any":
                return True
    return False

if __name__ == "__main__":
    print(get_board_name())

