# FindIllegalPixel
RenderDoc插件，查找Texture中非法像素(NaN, INF)

# 用法
1. 将库克隆到RenderDoc插件目录(C:\Users\xxx\AppData\Roaming\qrenderdoc\extensions)
2. 启动RenderDoc，点击Tools->Extension Manager，勾选FindIllegalPixel右侧的Loaded以及下方的Always Load
3. 打开Capture，选择一个Event，切换至Texture Viewer选项卡
4. 点击Actions右侧的拼图图标->Find Illegal Pixel

如果Texture中有非法像素，会自动定位。如果有多个，再次执行步骤4会定位下一个非法像素。
