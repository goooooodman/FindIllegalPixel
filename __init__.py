import os
import tempfile
import sys
import math
import time

import qrenderdoc as qrd
import renderdoc as rd

def _add_3rd_path():
    contain = False
    for path in sys.path:
        if path.endswith("FindIllegalPixel/third_party"):
            contain = True
            break

    if not contain:
        path_set = set()
        for path in sys.path:
            if path.endswith("qrenderdoc/extensions"):
                path_set.add(path)

        for path in path_set:
            sys.path.append("%s/FindIllegalPixel/third_party" % path)

_add_3rd_path()
import cv2
import numpy as np

extiface_version = ''

_last_event = -1
_last_resource_id = -1
_last_illegal_index = -1
_last_illegal_array = []

def _illegal_check(pixel):
    return math.isnan(pixel) or math.isinf(pixel) or pixel < 0
    # return np.isnan(pixel) or np.isinf(pixel) or pixel < 0 # too slow

def _collect_illegal_pixel(image):
    global _last_illegal_array
    illegal_result = np.isfinite(image)

    zero_array = np.zeros(image.shape, dtype = float, order = 'C')
    negative_result = np.less(image, zero_array)

    rows, cols, channels = image.shape

    # too slow
    # for i in range(rows):
    #     for j in range(cols):
    #         x = j
    #         y = i
    #         for n in range(channels):
    #             if _illegal_check(image[i, j, n]):
    #                 _last_illegal_array.append((x, y))
    #                 break

    for i in range(rows):
        for j in range(cols):
            x = j
            y = i
            for n in range(channels):
                if not illegal_result[i, j, n] or negative_result[i, j, n]:
                    _last_illegal_array.append((x, y))
                    break

def _find_illegal_pixel(controller: rd.ReplayController):
    global _last_event
    global _last_resource_id
    global _last_illegal_index
    global _last_illegal_array
    texture_viewer = pyrenderdoc.GetTextureViewer()

    # print("----------------------------------------------------")
    # print("pyrenderdoc.CurEvent() = %s" % pyrenderdoc.CurEvent())
    # print("_last_event = %s" % _last_event)
    # print("texture_viewer.GetCurrentResource() = %s" % texture_viewer.GetCurrentResource())
    # print("_last_resource_id = %s" % _last_resource_id)
    # print("----------------------------------------------------")

    if _last_event != pyrenderdoc.CurEvent() or _last_resource_id != texture_viewer.GetCurrentResource():

        _last_event = pyrenderdoc.CurEvent()
        _last_resource_id = texture_viewer.GetCurrentResource()
        _last_illegal_index = -1
        _last_illegal_array = []

        texsave = rd.TextureSave()
        texsave.resourceId = texture_viewer.GetCurrentResource()

        tmpfd, tempfilename = tempfile.mkstemp()

        filename = tempfilename + ".exr"

        # print("----------------------------------------------------")
        # print("Saving temp image of %s" % filename)
        # print("----------------------------------------------------")

        texsave.mip = 0
        texsave.slice.sliceIndex = 0

        texsave.destType = rd.FileType.EXR
        controller.SaveTexture(texsave, filename)

        image = cv2.imread(str(filename), cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH)

        # time_start = time.time()
        _collect_illegal_pixel(image)
        # time_end = time.time()
        
        # print("----------------------------------------------------")
        # print('totally cost : %ss' % str(time_end - time_start))
        # print("----------------------------------------------------")

        os.remove(filename)

    if len(_last_illegal_array) <= 0:
        print("未找到非法像素!")
    else:
        _last_illegal_index = _last_illegal_index + 1
        if _last_illegal_index >= len(_last_illegal_array):
            _last_illegal_index = 0

        x, y = _last_illegal_array[_last_illegal_index]
        texture_viewer.GotoLocation(x, y)
        print("找到非法像素 (%s, %s)!" % (x, y))

def _open_Panel_callback(ctx: qrd.CaptureContext, data):
    ctx.Replay().BlockInvoke(_find_illegal_pixel)

def register(version: str, ctx: qrd.CaptureContext):
    global extiface_version
    extiface_version = version

    print("Registering 'Find Illegal Pixel' extension for RenderDoc version {}".format(version))

    ctx.Extensions().RegisterPanelMenu(qrd.PanelMenu.TextureViewer, ["Find Illegal Pixel"], _open_Panel_callback)

def unregister():
    print("Unregistering 'Find Illegal Pixel' extension")
