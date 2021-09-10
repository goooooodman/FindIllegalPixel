###############################################################################
# The MIT License (MIT)
#
# Copyright (c) 2021 Baldur Karlsson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###############################################################################

import os
import tempfile
import sys

import qrenderdoc as qrd
import renderdoc as rd

contain = False
for path in sys.path:
    if path.endswith("FindIllegalPixel/package"):
        contain = True
        break

if not contain:
    path_set = set()
    for path in sys.path:
        if path.endswith("qrenderdoc/extensions"):
            path_set.add(path)

    for path in path_set:
        sys.path.append("%s/FindIllegalPixel/package" % path)

import cv2

extiface_version = ''

last_event = -1
last_resource_id = -1
last_illegal_index = -1
last_illegal_array = []

def open_Panel_callback(ctx: qrd.CaptureContext, data):
    def find_illegal_pixel(controller: rd.ReplayController):
        global last_event
        global last_resource_id
        global last_illegal_index
        global last_illegal_array
        texture_viewer = pyrenderdoc.GetTextureViewer()

        if last_event != pyrenderdoc.CurEvent() or last_resource_id != texture_viewer.GetCurrentResource():

            last_event = pyrenderdoc.CurEvent()
            last_resource_id = texture_viewer.GetCurrentResource()
            last_illegal_index = -1
            last_illegal_array = []

            texsave = rd.TextureSave()
            texsave.resourceId = texture_viewer.GetCurrentResource()

            tmpfd, tempfilename = tempfile.mkstemp()

            filename = tempfilename + ".exr"

            print("----------------------------------------------------")
            print("Saving images of %s" % filename)
            print("----------------------------------------------------")

            texsave.mip = 0
            texsave.slice.sliceIndex = 0

            texsave.destType = rd.FileType.EXR
            controller.SaveTexture(texsave, filename)

            image = cv2.imread(str(filename), cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH)
            def collect_illegal_pixel(image):
                rows, cols, channels = image.shape
                for i in range(rows):
                    for j in range(cols):
                        x = j
                        y = i
                        for n in range(channels):
                            if str(image[i, j, n]).lower() == "nan" or str(image[i, j, n]).lower() == "inf":
                                last_illegal_array.append((x, y))
                                break

            collect_illegal_pixel(image)
            os.remove(filename)

        if len(last_illegal_array) <= 0:
            print("未找到非法像素!")
        else:
            last_illegal_index = last_illegal_index + 1
            if last_illegal_index >= len(last_illegal_array):
                last_illegal_index = 0

            x, y = last_illegal_array[last_illegal_index]
            texture_viewer.GotoLocation(x, y)
            print("找到非法像素 (%s, %s)!" % (x, y))

    ctx.Replay().BlockInvoke(find_illegal_pixel)

def register(version: str, ctx: qrd.CaptureContext):
    global extiface_version
    extiface_version = version

    print("Registering 'Find Illegal Pixel' extension for RenderDoc version {}".format(version))

    ctx.Extensions().RegisterPanelMenu(qrd.PanelMenu.TextureViewer, ["Find Illegal Pixel"], open_Panel_callback)

def unregister():
    print("Unregistering 'Find Illegal Pixel' extension")
