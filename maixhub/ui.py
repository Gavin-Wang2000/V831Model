from dis import dis
from maix import display, camera, image, utils
import time
from PIL import ImageFont
from .board import get_board_name, connect_wifi, get_ip, is_support_model_platform
import os
import json
from evdev import InputDevice
from select import select
from .data_collect import upload_dataset, upload_heartbeat
from .trans import tr, set_language
from .params import Params
from .utils import download_file, unzip_files, remove_dir, Audio
from .demos import load_model_info
from .widgets.list import UI_List
 
curr_dir = os.path.abspath(os.path.dirname(__file__))
assets_dir = os.path.join(curr_dir, "assets")
 
paly_key_sound = True
color_green = (76, 175, 80)
 
image.load_freetype("/home/res/sans.ttf")
if paly_key_sound:
    audio = Audio(os.path.join(assets_dir, "btn.wav"))
 
def get_keys(device):
    '''
        @return is_left_pressed, is_right_pressed
    '''
    left = False
    right = False
    release_l = False
    release_r = False
    r,w,x = select([device], [], [], 0)
    if r:
        for event in device.read():
            if event.value == 1 and event.code == 0x02:
                right = True
            elif event.value == 1 and event.code == 0x03:
                left = True
            elif event.value == 0 and event.code == 0x02:
                release_r = True
            elif event.value == 0 and event.code == 0x03:
                release_l = True
    return left, right, release_l, release_r
 
def check_key(default="/dev/input/event0"):
    import os
    tmp = "/dev/input/by-path/"
    if os.path.exists(tmp):
        for i in os.listdir(tmp):
            if i.find("kbd") != -1:
                return tmp + i
    return default
 
keys_device = InputDevice(check_key())
_l_pressed = False
_r_pressed = False
def key_pressed():
    global _l_pressed, _r_pressed
    l, r, l_release, r_release = get_keys(keys_device)
    if l:
        _l_pressed = True
        if paly_key_sound:
            audio.play()
    elif l_release:
        _l_pressed = False
    if r:
        _r_pressed = True
        if paly_key_sound:
            audio.play()
    elif r_release:
        _r_pressed = False
    return l, r, _l_pressed, _r_pressed
 
def show_msg(img, msg, dis_size, y=110, diaplay=True, fill = None, scale = 1.2, thickness = 2):
    w, h = image.get_string_size(msg, scale=scale, thickness = thickness)
    x = int((dis_size[0] - w) // 2)
    if fill:
        img.draw_rectangle(x, y, x + w, y + h, color=fill, thickness=-1)
    img.draw_string(x, y, msg, scale = scale, color = (255, 255, 255), thickness = thickness)
    if diaplay:
        display.show(img)
 
def draw_center_string(img, msg, dis_size, y=110, diaplay=False, fill = None, scale = 1.2, thickness = 2):
    w, h = image.get_string_size(msg, scale=scale, thickness = thickness)
    x = int((dis_size[0] - w) // 2)
    if fill:
        img.draw_rectangle(x, y, x + w, y + h, color=fill, thickness=-1)
    img.draw_string(x, int(y), msg, scale = scale, color = (255, 255, 255), thickness = thickness)
    if diaplay:
        display.show(img)
 
def draw_frame(dis_img, dis_size, key_l = None, key_r = None, img = None, msg = None, image_offset = (0, 0), msg_y = None):
    if key_l:
        key_l = "| " + key_l
        dis_img.draw_string(2, 2, key_l, scale = 1.2, color = (255, 0, 0), thickness = 2)
    if key_r:
        key_r += " |"
        w = int(dis_size[0] - 2 - image.get_string_size(key_r)[0] * 1.2)
        dis_img.draw_string(w, 2, key_r, scale = 1.2, color = (255, 0, 0), thickness = 2)
    if img:
        icon = image.open(img)
        dis_img.draw_image(icon, image_offset[0], image_offset[1], alpha=1)
        if msg:
            x = int((dis_size[0] - 1.2 * image.get_string_size(msg)[0]) / 2)
            y = 180 if msg_y is None else msg_y
            dis_img.draw_string(x, y, msg, scale = 1.2, color = (255, 0, 0), thickness = 2)
    elif msg:
        x = int((dis_size[0] - 1.2 * image.get_string_size(msg)[0]) / 2)
        y = 110 if msg_y is None else int(msg_y)
        dis_img.draw_string(x, y, msg, scale = 1.2, color = (255, 0, 0), thickness = 2)
 
def frame_func_select(cam_size, dis_size, func_idx = 0):
    key_l = False
    key_r = False
    upload_img = os.path.join(assets_dir, "upload.png")
    deploy_img = os.path.join(assets_dir, "deployment.png")
    res_img = os.path.join(assets_dir, "resolution.png")
    lang_img = os.path.join(assets_dir, "language.png")
    wifi_img = os.path.join(assets_dir, "wifi.png")
    exit_img = os.path.join(assets_dir, "exit.png")
    funcs = ["collect", "deployment", "resolution", "language", "wifi", "exit"]
    names = [tr("Collect images"), tr("Deploy model"), tr("Resolution settings"), tr("Language settings"), tr("WiFi settings"), tr("Exit")]
    icons = [upload_img, deploy_img, res_img, lang_img, wifi_img, exit_img]
    if dis_size[0] == 320:
        icons_pos = [(96, 56), (96, 56), (96, 56), (96, 56), (96, 56), (96, 56)]
    else:
        icons_pos = [(56, 56), (56, 56), (56, 56), (56, 56), (56, 56), (56, 56)]
    icons_size = [(128, 128), (128, 128), (128, 128), (128, 128), (128, 128), (128, 128)]
    animing = None  # (olg_idx, new_idx, pox_x)
    animing_stage = 0
    camera.camera.config(size = cam_size)
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        if key_r:
            key_r = False
            return funcs[func_idx], func_idx
        if key_l:
            animing = [func_idx]
            func_idx += 1
            if func_idx >= len(funcs):
                func_idx = 0
            animing.append(func_idx)
            animing.append(icons_pos[animing[0]][0])
            animing_stage = 0
            key_l = False
        dis_img = img.resize(dis_size[0], dis_size[1])
        if animing:
            old_idx, new_idx, pos_x = animing
            animing[2] -= 40
            # old right to left
            if animing_stage == 0:
                if pos_x <= -icons_size[old_idx][0]:
                    animing_stage = 1
                    animing[2] = dis_size[0]
                    continue
                image_path = icons[old_idx] if icons[old_idx] else None
                pos = (pos_x, icons_pos[old_idx][1])
                draw_frame(dis_img, dis_size, tr("func"), tr("ok"), image_path, names[old_idx], pos)
            else:
                if pos_x <= icons_pos[new_idx][0]:
                    animing = None
                    continue
                image_path = icons[new_idx] if icons[new_idx] else None
                pos = (pos_x, icons_pos[new_idx][1])
                draw_frame(dis_img, dis_size, tr("func"), tr("ok"), image_path, names[new_idx], pos)
        else:
            image_path = icons[func_idx] if icons[func_idx] else None
            draw_frame(dis_img, dis_size, tr("func"), tr("ok"), image_path, names[func_idx], icons_pos[func_idx])
        display.show(dis_img)
    return None, func_idx
 
def frame_collect(cam_size, dis_size):
    key_l = False
    key_r = False
    camera.camera.config(size = cam_size)
    url = None
    token = None
    status_list = ["init", "scan", "collect", "sure_upload", "upload", "scan_error", "collect_local", "sure_save"]
    status = "init"
    upload_img = None
    start_collect_local = False
    save_count = 1
    def get_new_save_dir():
        save_dir = os.path.join(os.getcwd(), "collect")
        if not os.path.exists(save_dir):
            save_dir = os.path.join(save_dir, "1")
        else:
            name_id = len(os.listdir(save_dir))
            save_dir = os.path.join(save_dir, str(name_id + 1))
            while os.path.exists(save_dir):
                name_id += 1
                save_dir = os.path.join(save_dir, str(name_id + 1))
        return save_dir
 
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        dis_img = img.copy()
        dis_img = dis_img.resize(dis_size[0], dis_size[1])
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        # first time, show loading
        if status == "init":
            string = tr("Loading") + " ..."
            show_msg(dis_img, string, dis_size)
            status = "scan"
        # no upload url
        #进入二维码扫描界面
        if status == "scan":
            if key_l:
                key_l = False
                break
            #如果按下右键，就进入本地采集状态，start_collect_local赋值为True,左下角会显示保存路径信息
            if key_r:
                status = "collect_local"
                start_collect_local = True
                save_dir = get_new_save_dir()
                save_count = 1
                key_r = False
                continue
            result = img.find_qrcodes()
            if result:
                try:
                    result = json.loads(result[0]["payload"])
                    url = result["u"]
                    token = result["k"]
                    _type = result["t"]
                    if _type != "u":
                        print("QR code type error, {} not correct, should be {}".format(_type, "u"))
                        raise Exception("type error")
                except Exception:
                    status = "scan_error"
                    key_r = False
                    continue
                ok, msg = upload_heartbeat(url, token)
                if not ok:
                    print("Connet server failed:", msg)
                    show_msg(dis_img, tr("Connect failed") + "!", dis_size, y = 130)
                    show_msg(dis_img, msg, dis_size, y = 150)
                    time.sleep(3)
                    status = "scan_error"
                    continue
                status = "collect"
                dis_img.draw_rectangle(0, 0, dis_size[0], dis_size[1], color=color_green, thickness=-1)
                show_msg(dis_img, tr("Loading") + " ...", dis_size)
                time.sleep(0.5)
                key_r = False
                continue
            draw_frame(dis_img, dis_size, tr("back"), tr("collect locally"), None, tr("Scan QR code"), msg_y = dis_size[1] - 30)
            tmp = (display.width()-180) // 2
            dis_img.draw_rectangle(tmp, 30, display.width()-tmp, 200, color=(255, 255, 255), thickness=2)
            msg = tr("Visit") + " maixhub.com"
            draw_center_string(dis_img, msg, dis_size, y = 30)
        elif status == "scan_error":
            if key_r:
                key_r = False
                status = "scan"
                continue
            draw_frame(dis_img, dis_size, None, tr("ok"), None, tr("QR code error"))
        # collect data and upload
        elif status == "collect":
            if key_r:
                upload_img = img
                status = "sure_upload"
                key_r = False
            if key_l:
                status = "scan"
                key_l = False
                continue
            draw_frame(dis_img, dis_size, tr("back"), tr("collect"))
        elif status == "collect_local":
        # need set save_dir and save_count variable
            if key_r:
                upload_img = img
                status = "start_collet_picture"
                start_collect_local = False
                key_r = False
                continue
            if key_l:
                status = "scan"
                key_l = False
                continue
            if start_collect_local:
                msg = tr("Will save to")
                w, h = image.get_string_size(msg, scale = 1, thickness = 1)
                dis_img.draw_string(2, dis_size[1] - h * 3 - 15, msg, scale = 1, color = (255, 0, 0), thickness = 1)
                dis_img.draw_string(2, dis_size[1] - h * 2 - 10, os.path.join(save_dir, f'{save_count}.jpg'), scale = 1, color = (255, 0, 0), thickness = 1)
                dis_img.draw_string(2, dis_size[1] - h - 5, tr("Can re-enter to change dir"), scale = 1, color = (255, 0, 0), thickness = 1)
            else:
                dis_img.draw_string(2, dis_size[1] - h * 2 - 10, msg, scale = 1, color = (255, 0, 0), thickness = 1)
                dis_img.draw_string(2, dis_size[1] - h - 5, os.path.join(save_dir, f'{save_count}.jpg'), scale = 1, color = (255, 0, 0), thickness = 1)
            draw_frame(dis_img, dis_size, tr("back"), tr("collect"))
 
        elif status == "start_collet_picture":
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            img.save(os.path.join(save_dir, f"{save_count}.jpg"))
            save_count += 1
            dis_img.draw_string(2, dis_size[1] - h - 5, tr("collecting pictures"), scale=1,color=(255, 0, 0), thickness=1)
            if key_r:
                status = "sure_save"
                key_r = False
                continue
            if key_l:
                status = "collect_local"
                key_l = False
                continue
            draw_frame(dis_img, dis_size, tr("back"), tr("finish collected"))
 
        elif status == "sure_save":
            if key_r:
                status = "collect_local"
                key_r = False
                continue
            if key_l:
                status = "collect_local"
                key_l = False
                continue
            dis_img = upload_img.copy()
            dis_img = dis_img.resize(dis_size[0], dis_size[1])
            draw_frame(dis_img, dis_size, tr("cancel"), tr("save"), None, tr("Save") + " ?")
        elif status == "sure_upload":
            dis_img = upload_img.copy()
            dis_img = dis_img.resize(dis_size[0], dis_size[1])
            draw_frame(dis_img, dis_size, tr("cancel"), tr("upload"), None, tr("Upload") + " ?")
            if key_r:
                status = "upload"
                key_r = False
            if key_l:
                upload_img = None
                status = "collect"
                key_l = False
        elif status == "upload":
            show_msg(dis_img, tr("Uploading") + " ...", dis_size)
            jpg = utils.rgb2jpg(upload_img.convert("RGB").tobytes(), upload_img.width, upload_img.height, 3, 2, 95)
            ok, msg = upload_dataset(jpg, url, token)
            if not ok:
                print("upload failed:", msg)
                show_msg(dis_img, tr("Upload failed!"), dis_size, y = 130)
                show_msg(dis_img, msg, dis_size, y = 150)
                time.sleep(3)
            upload_img = None
            key_r = False
            key_l = False
            status = "collect"
        display.show(dis_img)
    return "func"
 
def frame_resolution(cam_size, dis_size):
    status_list = ["select", "sure"]
    status = "select"
    key_l = False
    key_r = False
    final = cam_size
    camera.camera.config(size = cam_size)
    res_list = [(96, 96), (128, 128), (224, 224), (240, 240), (320, 240), (320, 320), (416, 416), (448, 448), (640, 480)]
    names = []
    for item in res_list:
        names.append(f'{item[0]} x {item[1]}')
    res_idx = 2
    for i, size in enumerate(res_list):
        if cam_size[0] == size[0] and cam_size[1] == size[1]:
            res_idx = i
    ui_list = UI_List(names, -1, 60, 5, 1.5, default_idx = res_idx, value_items=res_list)
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        dis_img = img.copy()
        dis_img = dis_img.resize(dis_size[0], dis_size[1])
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        if status == "select":
            if key_r:
                key_l = False
                key_r = False
                i, item = ui_list.get_selected()
                if item[0] != final[0] or item[1] != final[1]:
                    status = "sure"
                    continue
                break # no change
            if key_l:
                ui_list.next()
                key_l = False
                continue
            ui_list.draw(dis_img)
            draw_frame(dis_img, dis_size, tr("switch"), tr("ok back"))
        elif status == "sure":
            if key_l:
                key_l = False
                break
            if key_r:
                i, item = ui_list.get_selected()
                final = item
                key_r = False
                break
            draw_frame(dis_img, dis_size, tr("cancel"), tr("save"), None, tr("Sure to change ?"))
        display.show(dis_img)
    return "func", final
 
def frame_language(cam_size, dis_size, curr):
    status_list = ["select", "sure"]
    status = "select"
    key_l = False
    key_r = False
    final = curr
    camera.camera.config(size = cam_size)
    lang_list = ["English", "中文"]
    lang_id = ["en", "zh"]
    lang_idx = lang_id.index(curr)
    ui_list = UI_List(lang_list, -1, dis_size[1] // 2 - 20, 2, 1.5, default_idx = lang_idx, value_items=lang_id)
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        dis_img = img.copy()
        dis_img = dis_img.resize(dis_size[0], dis_size[1])
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        if status == "select":
            if key_r:
                key_l = False
                key_r = False
                i, item = ui_list.get_selected()
                if item != final:
                    status = "sure"
                    continue
                break # no change
            if key_l:
                ui_list.next()
                key_l = False
                continue
            ui_list.draw(dis_img)
            draw_frame(dis_img, dis_size, tr("switch"), tr("ok back"))
        elif status == "sure":
            if key_l:
                key_l = False
                break
            if key_r:
                i, item = ui_list.get_selected()
                final = item
                key_r = False
                break
            draw_frame(dis_img, dis_size, tr("cancel"), tr("save"), None, tr("Sure to change ?"))
        display.show(dis_img)
    return "func", final
 
def frame_wifi(cam_size, dis_size):
    key_l = False
    key_r = False
    camera.camera.config(size = cam_size)
    ssid = None
    passwd = None
    status_list = ["init", "scan", "connect", "connecting", "complete", "scan_error"]
    status = "init"
    res_ok = False
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        dis_img = img.copy()
        dis_img = dis_img.resize(dis_size[0], dis_size[1])
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        # first time, show loading
        if status == "init":
            string = tr("Loading") + " ..."
            show_msg(dis_img, string, dis_size)
            status = "scan"
        # no upload url
        if status == "scan":
            ip = get_ip()
            if key_l:
                key_l = False
                break
            result = img.find_qrcodes()
            if result:
                try:
                    result = json.loads(result[0]["payload"])
                    ssid = result["s"]
                    passwd = result["p"]
                except Exception:
                    status = "scan_error"
                    key_r = False
                    continue
                status = "connect"
                key_r = False
                continue
            msg = tr("Visit") + " maixhub.com/wifi"
            draw_frame(dis_img, dis_size, tr("back"), None, None, msg, msg_y = dis_size[1] - 30)
            msg = "IP: " + ip if ip else tr("No IP")
            x = int((dis_size[0] - 1.2 * image.get_string_size(msg)[0]) / 2)
            tmp = (display.width()-180) // 2
            dis_img.draw_rectangle(tmp, 30, display.width()-tmp, 200, color=(255, 255, 255), thickness=2)
        elif status == "scan_error":
            if key_r:
                key_r = False
                status = "scan"
                continue
            draw_frame(dis_img, dis_size, None, tr("ok"), None, tr("QR code error"))
        # connect WiFi
        elif status == "connect":
            if key_r:
                ok, msg = connect_wifi(ssid, passwd)
                res_ok = ok
                if ok:
                    show_msg(dis_img, tr("Connecting") + " ...", dis_size)
                    time.sleep(1)
                    status = "connecting"
                    connect_time = time.time()
                    key_r = False
                    continue
                status = "complete"
                key_r = False
                continue
            if key_l:
                key_l = False
                break
            msg = f'SSID: {ssid}'
            draw_frame(dis_img, dis_size, tr("cancel"), tr("connect"), msg=msg, msg_y = dis_size[1] // 2 - 20)
            msg = f'{tr("Passwd")}: {passwd}'
            draw_center_string(dis_img, msg, dis_size, y = dis_size[1] // 2)
            msg = tr("Connect now ?")
            draw_center_string(dis_img, msg, dis_size, y = dis_size[1] // 2 + 20)
        elif status == "connecting":
            if key_l:
                break
            # wait for get ip
            ip = get_ip()
            if ip:
                msg = f"IP: {ip}"
                status = "complete"
                res_ok = True
                continue
            if time.time() - connect_time > 30:
                msg = tr("Connect timeout")
                status = "complete"
                res_ok = False
                continue
            draw_frame(dis_img, dis_size, tr("back"), msg=tr("Connecting") + " ...",)
        elif status == "complete":
            if key_l:
                break
            draw_frame(dis_img, dis_size, tr("back"), msg=msg, msg_y = dis_size[1] // 2 + 10)
            msg2 = tr("Connect success") if res_ok else tr("Connect failed")
            draw_center_string(dis_img, msg2, dis_size, y = dis_size[1] // 2 - 10)
 
        display.show(dis_img)
    return "func"
 
def frame_deploy(cam_size, dis_size):
    key_l = False
    key_r = False
    camera.camera.config(size = cam_size)
    url = None
    token = None
    saved_models_info = []
    ui_model_list = None
    ui_model_sub_list = None
    status_list = ["init", "scan", "get_model", "run", "error", "view_model"]
    status = "init"
    def get_model_info(url, token):
        import requests
        headers = {
            "token": token
        }
        try:
            res = requests.post(url, headers = headers)
            if res.status_code != 200:
                return None, tr("Request server error")
            try:
                res = res.json()
                if res["code"] != 0:
                    print("response code != 0:", res["code"], res["msg"])
                    raise Exception()
            except Exception:
                return None, tr("Response error")
            res = res["data"]
        except Exception:
            return None, tr("Request server error")
        # check args
        args = ["id", "model", "name"]
        for v in args:
            if v not in res:
                return False, tr("Params error!")
        return res, ""
 
    def load_saved_models(models_dir):
        '''
            @return models list: [
                [model_dir, model_path, report_info, code_obj, model_info]
            ]
        '''
        models = []
        if os.path.isdir(models_dir):
            names = os.listdir(models_dir)
            for name in names:
                path = os.path.join(models_dir, name)
                if os.path.isdir(path):
                    info_ = load_model_info(path, init_model=False)
                    if not info_[0]:
                        continue
                    info = [path]
                    info.extend(info_)
                    with open(os.path.join(path, "model_info.json"), "r") as f:
                        model_info = json.load(f)
                        info.append(model_info)
                    models.append(info)
        return models
 
    while 1:
        img = camera.capture()
        if not img:
            time.sleep(0.01)
            continue
        dis_img = img.copy()
        dis_img = dis_img.resize(dis_size[0], dis_size[1])
        # keys
        l, r, l_pressed, r_pressed = key_pressed()
        key_l = l | key_l
        key_r = r | key_r
        # first time, show loading
        if status == "init":
            string = tr("Loading") + " ..."
            show_msg(dis_img, string, dis_size)
            status = "scan"
        # no upload url
        if status == "scan":
            if key_l:
                key_l = False
                break
            if key_r:
                status = "view_model"
                key_r = False
                continue
            result = img.find_qrcodes()
            if result:
                try:
                    result = json.loads(result[0]["payload"])
                    url = result["u"]
                    token = result["k"]
                    _type = result["t"]
                    platform = result["p"]
                    if not is_support_model_platform(platform):
                        print("Not support platform")
                        raise Exception()
                    if _type != "d":
                        print("QR code type error, {} not correct, should be {}".format(_type, "d"))
                        raise Exception()
                except Exception:
                    status = "error"
                    err_msg = tr("QR code error")
                    key_r = False
                    continue
                status = "get_model"
                dis_img.draw_rectangle(0, 0, dis_size[0], dis_size[1], color=color_green, thickness=-1)
                show_msg(dis_img, tr("Loading") + " ...", dis_size)
                time.sleep(0.5)
                key_r = False
                continue
            draw_frame(dis_img, dis_size, tr("back"), tr("view saved"), None, tr("Scan QR code"), msg_y = dis_size[1] - 30)
            tmp = (display.width()-180) // 2
            dis_img.draw_rectangle(tmp, 30, display.width()-tmp, 200, color=(255, 255, 255), thickness=2)
            msg = tr("Visit") + " maixhub.com"
            draw_center_string(dis_img, msg, dis_size, y = 30)
        elif status == "error":
            if key_r:
                key_r = False
                status = "scan"
                continue
            draw_frame(dis_img, dis_size, None, tr("ok"), None, err_msg)
        # get model info
        elif status == "get_model":
            bg = (0, 0, 0)
            dis_img.draw_rectangle(0, 0, dis_size[0], dis_size[1], color=bg, thickness=-1)
            draw_frame(dis_img, dis_size, tr("cancel"))
            show_msg(dis_img, tr("Get model info") + " ...", dis_size, y = 70)
            res, msg = get_model_info(url, token)
            if not res:
                status = "error"
                if msg:
                    err_msg = msg
                else:
                    err_msg = tr("Get model info") + " " + tr("failed")
                continue
            show_msg(dis_img, tr("Downloading model") + " ...", dis_size, y=90)
            def on_progress(curr, total):
                download_cancel = False
                # update keys
                l, r, l_pressed, r_pressed = key_pressed()
                if l:
                    download_cancel = True
                dis_img.draw_rectangle(1, 132, dis_size[0] - 2, 148, color=(255, 255, 255), thickness=2)
                dis_img.draw_rectangle(3, 134, int(curr / total * (dis_size[0] - 2)), 146, color=(255, 255, 255), thickness=1)
                show_msg(dis_img, f'{curr / total * 100:.1f}%', dis_size, y=112, fill=bg)
                return download_cancel
            ok, msg = download_file(res["model"], "model.zip", on_progress)
            if not ok:
                status = "error"
                err_msg = tr("Download Failed!") + " " + msg
                continue
            show_msg(dis_img, tr("Unzip model") + " ...", dis_size, y=150)
            model_dir = f'models/{res["id"]}'
            ok, msg = unzip_files("model.zip", model_dir)
            if not ok:
                status = "error"
                err_msg = tr("Unzip Failed!")
                continue
            # save model info to model_info.json
            with open(os.path.join(model_dir, "model_info.json"), "w") as f:
                res.pop("model")
                json.dump(res, f)
            key_r = False
            key_l = False
            model_init = False
            status = "run"
        elif status == "run":
        # need set var model_dir and set model_init to False
            if not model_init:
                dis_img.draw_rectangle(0, 0, dis_size[0], dis_size[1], color=color_green, thickness=-1)
                show_msg(dis_img, tr("Loading model") + " ...", dis_size)
                try:
                    model_path, info, demo = load_model_info(model_dir)
                except Exception as e:
                    model_path = None; info = ""
                    import traceback; traceback.print_exc()
                if not model_path:
                    status = "error"
                    print("Load model failed:", info)
                    err_msg = tr("Load model failed")
                    continue
                model_init = True
                continue
            demo.loop(img, dis_img, key_r)
            draw_frame(dis_img, dis_size, tr("back"))
            if key_r:
                key_r = False
            if key_l:
                key_l = False
                break
        elif status == "view_model":
            if not saved_models_info:
                names = [tr("back")]
                saved_models_info = load_saved_models("models")
                for model_info in saved_models_info:
                    names.append(model_info[4]["name"])
                ui_model_list = UI_List(names, 20, 50, lines = 7, scale = 1.5, color_active = color_green)
                ui_model_sub_list = None
            draw_frame(dis_img, dis_size, tr("switch"), tr("select"))
            if key_l:
                key_l = False
                if not ui_model_sub_list:
                    ui_model_list.next()
                else:
                    ui_model_sub_list.next()
                continue
            if key_r:
                if not ui_model_sub_list:
                    slected_idx, item = ui_model_list.get_selected()
                    if item == tr("back"):
                        status = "scan"
                    else:
                        slected_idx -= 1 # first item is back
                        names = [tr("back"), tr("run"), tr("delete")]
                        ui_model_sub_list = UI_List(names, 160, 100, lines = 3, scale = 1.5,
                                                color = (102, 102, 102), color_active = color_green,
                                                rectangle = (255, 255, 255))
                else:
                    i, item = ui_model_sub_list.get_selected()
                    if item == tr("back"):
                        ui_model_sub_list = None
                    elif item == tr("run"):
                        status = "run"
                        model_init = False
                        model_dir = saved_models_info[slected_idx][0]
                    elif item == tr("delete"):
                        model_dir = saved_models_info[slected_idx][0]
                        remove_dir(model_dir)
                        ui_model_list.remove(slected_idx + 1)
                        ui_model_sub_list = None
                key_r = False
                continue
            ui_model_list.draw(dis_img)
            if ui_model_sub_list:
                ui_model_sub_list.draw(dis_img)
        display.show(dis_img)
    return "func"
 
def main():
    print("ui main")
    try:
        board = get_board_name()
        if not board:
            raise Exception("unknown board, maybe you need to upgrade maixhub tool and upgrade maixpy3")
        board = "-".join(board)
        if board not in ["m2-v831-dock", "m2-v831-cam"]:
            raise Exception(f"board {board} not support yet")
        dis_size = (display.width(), display.height())
        func = "func"
        idx = 0
        params = Params()
        params.load()
        cam_size= params.params["resolution"]
        set_language(params.params["language"])
        while 1:
            if func == "func":
                func, idx = frame_func_select(cam_size, dis_size, idx)
            elif func == "collect":
                func = frame_collect(cam_size, dis_size)
            elif func == "resolution":
                func, new_cam_size = frame_resolution(cam_size, dis_size)
                if new_cam_size[0] != cam_size[0] or new_cam_size[1] != cam_size[1]:
                    cam_size = new_cam_size
                    params.params["resolution"] = cam_size
                    params.save()
            elif func == "language":
                func, language = frame_language(cam_size, dis_size, params.params["language"])
                if language != params.params["language"]:
                    params.params["language"] = language
                    set_language(language)
                    params.save()
            elif func == "wifi":
                func = frame_wifi(cam_size, dis_size)
            elif func == "deployment":
                func = frame_deploy(cam_size, dis_size)
            else:
                print("exit")
                break
    except Exception as e:
        import traceback, time
        msg = traceback.format_exc()
        print(msg)
        img = image.new(size = (display.width(), display.height()), color = (255, 0, 0), mode = "RGB")
        x, y = 0, 0
        for s in msg.split('\n'):
            w, h = image.get_string_size(msg, scale = 0.8)
            img.draw_string(x, y, s, scale = 0.8, color = (255, 255, 255), thickness = 1)
            y += h + 5
        display.show(img)
        time.sleep(5)