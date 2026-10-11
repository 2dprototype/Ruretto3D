# Crayon Engine - Lua API Documentation

## Overview
Crayon Engine is a 2D/3D game engine with retro aesthetics, modern physics, and Lua scripting. All engine functionality is accessed through the global `crayon` table.

**Conventions:** All exposed functions, methods, and config keys use strict camelCase. Acronyms that appear as a suffix capitalize only their first letter (`getFps`, `getEngineRpm`, `setSfxVolume`, `getId`, `setVsync`). Numeric suffixes are `2D` / `3D` (capital `D`).

## Table of Contents
1. [Time Module](#time-module)
2. [Window Module](#window-module)
3. [Input Modules](#input-modules)
4. [Graphics Module](#graphics-module)
5. [Physics3D Module](#physics3d-module)
6. [Physics2D Module](#physics2d-module)
7. [Physics4D Module](#physics4d-module)
8. [Audio Module](#audio-module)
9. [Particles Module](#particles-module)
10. [Math Module](#math-module)
11. [File System Module](#file-system-module)
12. [Configuration (`crayon.config`)](#configuration)
13. [Lua Callbacks](#lua-callbacks)
14. [Complete Examples](#complete-examples)

---

## Time Module
Access via: `crayon.time`

| Function | Description |
|----------|-------------|
| `getTime()` | Total elapsed time (seconds) |
| `getDt()` | Delta time (seconds since last frame) |
| `getFps()` | Current frames per second |

```lua
local t = crayon.time.getTime()
local dt = crayon.time.getDt()
local fps = crayon.time.getFps()
```

---

## Window Module
Access via: `crayon.window`

### Resolution & Size

| Function | Description |
|----------|-------------|
| `setResolution(w, h)` | Set virtual resolution (default: 320x240) |
| `getResolution()` | Returns virtual width, height |
| `setWindowSize(w, h)` | Set physical window size |
| `getWindowSize()` | Returns window width, height |
| `setMinSize(w, h)` | Set minimum window size |
| `setMaxSize(w, h)` | Set maximum window size |
| `getDisplaySize()` | Returns primary monitor width, height |
| `getUsableBounds()` | Returns usable desktop x, y, w, h |

### Position

| Function | Description |
|----------|-------------|
| `setPosition(x, y)` | Set window position on screen |
| `getPosition()` | Returns window x, y |
| `center()` | Center window on screen |

### Display State

| Function | Description |
|----------|-------------|
| `setFullscreen(enabled)` | Toggle fullscreen |
| `isFullscreen()` | Returns fullscreen state |
| `setVsync(enabled)` | Toggle VSync |
| `getVsync()` | Returns VSync state |
| `setResizable(enabled)` | Allow/disable resizing |
| `isResizable()` | Returns resizable state |
| `setBordered(enabled)` | Show/hide window borders |
| `isBordered()` | Returns bordered state |
| `maximize()` | Maximize window |
| `minimize()` | Minimize window |
| `restore()` | Restore window from min/max |
| `isMaximized()` | Returns maximized state |
| `isMinimized()` | Returns minimized state |
| `isFocused()` | Returns focused state |
| `raise()` | Raise window to front |
| `focus()` | Focus window |
| `flash()` | Flash taskbar icon |

### Title

| Function | Description |
|----------|-------------|
| `setTitle(title)` | Set window title |
| `getTitle()` | Returns window title |

### Scaling

| Function | Description |
|----------|-------------|
| `setScalingMode(mode)` | Set scaling: "integer", "aspect", "stretch", "center" |
| `getScalingMode()` | Returns current scaling mode |

### Opacity & Layering

| Function | Description |
|----------|-------------|
| `setOpacity(opacity)` | Set window opacity (0.0–1.0) |
| `getOpacity()` | Returns window opacity |
| `setAlwaysOnTop(enabled)` | Keep window on top |
| `isAlwaysOnTop()` | Returns always-on-top state |
| `isTransparent()` | Returns transparency state |

### Mouse & Cursor

| Function | Description |
|----------|-------------|
| `setMouseGrab(enabled)` | Grab mouse to window |
| `isMouseGrabbed()` | Returns mouse grab state |
| `setMouseRelative(enabled)` | Enable relative mouse mode |
| `isMouseRelative()` | Returns relative mouse state |
| `showCursor(show)` | Show/hide cursor |
| `isCursorVisible()` | Returns cursor visibility |

### Overlay Flags (see config for creation-time flags)

| Function | Description |
|----------|-------------|
| `show()` / `hide()` | Show / hide window |
| `isVisible()` | Returns visibility state |
| `setClickThrough(enabled)` / `isClickThrough()` | Mouse passthrough |
| `setSkipTaskbar(skip)` / `isSkipTaskbar()` | Hide from taskbar |
| `setNotFocusable(nf)` / `isNotFocusable()` | Prevent focus stealing |
| `setUtilityWindow(util)` / `isUtilityWindow()` | Utility chrome |
| `getDisplays()` | Array of display tables |
| `getVirtualDesktopBounds()` | x, y, w, h of virtual desktop |

### Misc

| Function | Description |
|----------|-------------|
| `getFps()` | Returns current FPS |
| `quit()` | Quit the engine |

### Window Examples

```lua
crayon.window.setResolution(640, 360)
crayon.window.setWindowSize(1280, 720)
crayon.window.setTitle("My Game")
crayon.window.setVsync(true)
crayon.window.setScalingMode("integer")

local w, h = crayon.window.getDisplaySize()
print("Display:", w, "x", h)
```

---

## Input Modules

Input is exposed as three sub-tables: `crayon.key`, `crayon.mouse`, and `crayon.gamepad`. The previous `crayon.input` alias table has been **removed**; use the sub-tables directly.

### `crayon.key`

| Function | Description |
|----------|-------------|
| `isDown(...keys)` | Returns true if **any** listed key is held |
| `isPressed(...keys)` | Returns true if **any** listed key was just pressed |
| `isReleased(...keys)` | Returns true if **any** listed key was just released |
| `isScancodeDown(...codes)` | Returns true if any scancode is held |
| `anyPressed()` | Returns true if any key was just pressed |
| `anyDown()` | Returns true if any key is held |
| `getPressedKeys()` | Returns array of key names pressed this frame |
| `getDownKeys()` | Returns array of key names currently held |
| `isShiftDown()` | Shift held? |
| `isCtrlDown()` | Ctrl held? |
| `isAltDown()` | Alt held? |
| `isGuiDown()` | GUI (Windows/Command) held? |
| `isCapsLock()` | Caps Lock active? |

**Text Input & Clipboard:**

| Function | Description |
|----------|-------------|
| `setTextInput([enabled])` | Start/stop text input (IME). Default: true |
| `hasTextInput()` | Returns true if text input is active |
| `getTextInput()` | Get current text input buffer |
| `getClipboard()` | Get clipboard text |
| `setClipboard(text)` | Set clipboard text |

**Key Names**: `"a"`–`"z"`, `"space"`, `"enter"`, `"escape"`, `"tab"`, `"backspace"`, `"up"`, `"down"`, `"left"`, `"right"`, `"shift"`, `"ctrl"`, `"alt"`, `"gui"`, `"f1"`–`"f12"`.

### `crayon.mouse`

| Function | Description |
|----------|-------------|
| `isDown(...buttons)` | Any listed button held? |
| `isPressed(...buttons)` | Any listed button just pressed? |
| `isReleased(...buttons)` | Any listed button just released? |
| `getPosition()` | Returns virtual x, y |
| `getX()` / `getY()` | Returns virtual x or y |
| `getDelta()` | Returns mouse delta x, y |
| `getDeltaX()` / `getDeltaY()` | Returns delta x or y |
| `getWindowPosition()` | Returns window x, y |
| `getWindowX()` / `getWindowY()` | Returns window x or y |
| `getWindowDelta()` | Returns window delta x, y |
| `getWheel()` | Returns wheel x, y |
| `getWheelX()` / `getWheelY()` | Returns wheel x or y |
| `getGlobalPosition()` | Global desktop mouse position |
| `setPosition(x, y)` | Set mouse virtual position |
| `setWindowPosition(x, y)` | Set mouse window position |
| `setVisible(visible)` | Show/hide cursor |
| `isVisible()` | Cursor visible? |
| `setGrabbed(grab)` | Grab mouse to window |
| `isGrabbed()` | Mouse grabbed? |
| `setRelativeMode(enabled)` | Enable relative mode |
| `isRelativeMode()` | Relative mode active? |

**Button Types**: `1`–`5`, `"left"`/`"l"`/`"1"`, `"middle"`/`"mid"`/`"m"`/`"2"`, `"right"`/`"r"`/`"3"`, `"x1"`/`"mouse4"`/`"4"`, `"x2"`/`"mouse5"`/`"5"`.

### `crayon.gamepad`

| Function | Description |
|----------|-------------|
| `isDown(button)` | Gamepad button held? |
| `isPressed(button)` | Gamepad button just pressed? |
| `isReleased(button)` | Gamepad button just released? |
| `getAxis(axis)` | Get axis value (-1 to 1) |
| `isConnected([idx])` | Gamepad connected? Default idx: 0 |
| `getName([idx])` | Gamepad name string |
| `getCount()` | Number of connected gamepads |

### Input Examples

```lua
-- Keyboard
if crayon.key.isPressed("space") then jump() end
if crayon.key.isDown("w", "up") then moveUp() end
if crayon.key.isShiftDown() then run() end

-- Mouse
local mx, my = crayon.mouse.getPosition()
local dx, dy = crayon.mouse.getDelta()
if crayon.mouse.isPressed(1) then shoot() end
local wx, wy = crayon.mouse.getWheel()

-- Gamepad
if crayon.gamepad.isDown(0) then fire() end
local lx = crayon.gamepad.getAxis("leftx")
```

---

## Graphics Module
Access via: `crayon.graphics`

### Color & Canvas

| Function | Description |
|----------|-------------|
| `clear(r, g, b [, a])` | Clear screen with color (0–1) |
| `setColor(r, g, b [, a])` | Set active drawing color (0–1) |
| `createCanvas([w, h])` | Create offscreen canvas (defaults to virtual resolution) |
| `setCanvas(canvas_or_nil)` | Bind canvas for rendering, or unbind with nil |

**Canvas Methods**: `:getSize()`, `:getWidth()`, `:getHeight()`, `:clear(r,g,b,a)`, `:renderTo(fn)`, `:getTexture()`

```lua
local canvas = crayon.graphics.createCanvas(320, 240)
canvas:renderTo(function()
    canvas:clear(0, 0, 0, 1)
    crayon.graphics.setColor(1, 0.5, 0)
    crayon.graphics.drawCircle("fill", 160, 120, 50)
end)
crayon.graphics.drawSprite(canvas:getTexture(), 0, 0)
```

### Shaders

| Function | Description |
|----------|-------------|
| `loadShader(path_or_source [, frag])` | Load shader from file path or inline GLSL source |
| `setShader(shader_or_nil)` | Bind custom shader (nil = default) |

**Shader Methods**: `:sendFloat(name, v)`, `:sendInt(name, v)`, `:sendVec2(name, x, y)`, `:sendVec3(name, x, y, z)`, `:sendVec4(name, x, y, z, w)`

### Retro Effects

| Function | Description |
|----------|-------------|
| `setRetroEffects(opts)` | Apply retro visual effects |

**Options Table:**
```lua
{
    jitterResolution = {160, 120},  -- Pixel snap resolution, or nil/false to disable
    affine = 1.0,                    -- 0=perspective, 1=affine texture mapping
    dither = true,                   -- Enable dithering
    colorDepth = 32,                 -- 32 or 8 (bits per channel)
    ditherLevels = 32,               -- Override colorDepth
    fog = {                          -- Distance fog
        startDist = 5.0,
        endDist = 25.0,
        color = {0.1, 0.1, 0.2}
    },
    crt = {                          -- CRT effects
        scanlines = 0.25,            -- or true for default
        curvature = 0.05,            -- or true for default
        vignette = 0.25              -- or true for default
    },
    scanlines = 0.25,                -- Shortcut for crt.scanlines
    curvature = 0.05,                -- Shortcut for crt.curvature
    vignette = 0.25                  -- Shortcut for crt.vignette
}
```

### 3D Camera

| Function | Description |
|----------|-------------|
| `setCamera3D(cam)` | Set 3D camera parameters |
| `getCameraRay(sx, sy)` | Returns `{origin={x,y,z}, direction={x,y,z}}` for screen pos |

**Camera Table:**
```lua
{
    position = {x, y, z},
    target = {x, y, z},
    up = {x, y, z},       -- default: {0, 1, 0}
    fov = 60,             -- field of view in degrees
    near = 0.1,
    far = 1000.0,
    ortho = false,        -- true for orthographic projection
    orthoSize = 10.0      -- half-height in world units
}
```

Alternative: `setCamera3D(x, y, z [, yaw, pitch, fov])` — sets position and orients using yaw/pitch in degrees.

### Lighting

| Function | Description |
|----------|-------------|
| `setLight(dx, dy, dz [, lr, lg, lb, ar, ag, ab])` | Set directional light |
| `setPointLight(idx, x, y, z [, r, g, b, radius, intensity])` | Set point light (idx 0-based or 1-based accepted) |
| `setPointLightEnabled(idx, enabled)` | Enable/disable point light |
| `setSpotLight(idx, px, py, pz, dx, dy, dz [, radius, r, g, b, intensity, innerAngle, outerAngle])` | Set spot light |
| `setSpotLightEnabled(idx, enabled)` | Enable/disable spot light |
| `setShadingMode(mode)` | Set shading: "gouraud", "flat", "unlit" |

### Depth & Culling

| Function | Description |
|----------|-------------|
| `setDepthTest([enabled])` | Toggle depth testing (default: true) |
| `setDepthWrite([enabled])` | Toggle depth writes (default: true) |
| `setCullFace(mode)` | "back", "front", or false to disable |

### Textures

| Function | Description |
|----------|-------------|
| `loadTexture(path)` | Load texture, returns `Graphics.Texture` userdata |
| `getTextureSize(tex_or_id)` | Returns width, height |
| `getWhiteTexture()` | Returns white 1x1 texture userdata |

**Texture Methods**: `:getSize()`, `:getWidth()`, `:getHeight()`, `:getId()`, `:isValid()`

### Fonts

| Function | Description |
|----------|-------------|
| `loadFont(path [, size, nearest])` | Load a font (default size: 16, nearest: true) |
| `setFont(font_or_nil)` | Set active font for subsequent drawText calls |
| `getFont()` | Get the currently active font |

**Font Methods**: `:getSize()`, `:getLineHeight()`, `:getAscent()`, `:getDescent()`, `:measure(text [, scale])`, `:getWidth(text [, scale])`, `:getHeight(text [, scale])`

### Models & Meshes

| Function | Description |
|----------|-------------|
| `loadModel(name)` | Load/create model. Primitives or file path (`.obj`, `.gltf`, `.glb`) |
| `createMesh(data)` | Create custom mesh from `{vertices, indices}` |
| `createAnimator(model)` | Create skeletal `Graphics.Animator` from a skinned model |

**Primitive Names**: `"cube"`, `"plane"`, `"sphere"`, `"cylinder"`, `"cone"`, `"pyramid"`, `"torus"`, `"capsule"`, `"grid"`.

**Model Methods:**
- `:isValid()`
- `:getNodeCount()` / `:getNode(idx_or_name)` / `:getNodes()`
- `:getPartCount()` / `:getPartName(idx)` → name, material_name
- `:getPartTexture(idx)` / `:setPartTexture(idx, tex)` / `:setPartColor(idx, r, g, b [, a])`
- `:getBounds()` → minX, minY, minZ, maxX, maxY, maxZ
- `:getCenter()` → cx, cy, cz
- `:getSize()` → sx, sy, sz
- `:getTriangles()` → table of `{{p1},{p2},{p3}}`
- `:isSkinned()` / `:getJointCount()` / `:getJointName(idx)` / `:getJointIndex(name)` / `:getJointNames()`
- `:getAnimationCount()` / `:getAnimationNames()` / `:getAnimationDuration(name_or_idx)`
- `:createAnimator()` → `Graphics.Animator`
- `:createPhysicsSkeleton()` → `Physics3D.Skeleton`
- `:drawSkinned(animator_or_pose, x, y, z, rx, ry, rz, sx, sy, sz, tex)`

**Node Table** (returned by `getNode`/`getNodes`):
```lua
{ name, index, parent, x, y, z, rx, ry, rz, rw, sx, sy, sz }
```

**Mesh Data** (`createMesh`):
```lua
{
    vertices = {
        { pos = {x,y,z}, norm = {x,y,z}, uv = {u,v}, color = {r,g,b,a} },
        ...
    },
    indices = { 1, 2, 3, ... }  -- 1-indexed
}
```

### Skeletal Animation (`Graphics.Animator`)

| Method | Description |
|--------|-------------|
| `:play(clip [, loop, speed])` | Start clip (defaults: loop=true, speed=1.0) |
| `:stop()` | Stop and reset time |
| `:pause()` / `:resume()` | Pause / resume |
| `:isPlaying()` | Playback state |
| `:getCurrentAnimation()` | Current clip name |
| `:getTime()` / `:setTime(t)` | Playback timestamp |
| `:getDuration()` | Duration of active clip |
| `:setSpeed(s)` / `:getSpeed()` | Speed multiplier |
| `:crossFade(targetClip [, duration, loop])` | Crossfade (default duration: 0.2s) |
| `:crossFadeFromCurrentPose(targetClip [, duration, loop])` | Crossfade preserving pose |
| `:blend(clipA, clipB, factor)` | 1D locomotion blend (factor 0–1) |
| `:setLayerClip(layer, clip [, loop, speed])` | Set layer clip |
| `:setLayerWeight(layer, weight)` | Set layer weight |
| `:setLayerMask(layer, rootJointName [, includeChildren])` | Bone hierarchy mask |
| `:setUpdateRate(fps)` | LOD tick throttling |
| `:update(dt)` | Advance by dt seconds |
| `:applyToPhysicsPose(pose [, x,y,z, qx,qy,qz,qw])` | Transfer to `SkeletonPose`. Returns bool |
| `:capturePhysicsPose(pose)` | Transfer from pose. Returns bool |
| `:getModel()` | Associated Model |

### 3D Drawing

| Function | Description |
|----------|-------------|
| `drawModel(model, x, y, z, rx, ry, rz, sx, sy, sz, tex)` | Draw static model |
| `drawModelSkinned(model, anim_or_pose, x, y, z, rx, ry, rz, sx, sy, sz, tex)` | Draw skinned model |
| `drawModelNode(model, node, x, y, z, rx, ry, rz, sx, sy, sz, tex)` | Draw single node |
| `drawCube(x, y, z, sx, sy, sz, tex, rx, ry, rz)` | Draw cube |
| `drawPlane(x, y, z, w, d, tex, rx, ry, rz)` | Draw plane |
| `drawSphere(x, y, z, radius, tex, rx, ry, rz)` | Draw sphere |
| `drawCylinder(x, y, z, radius, height, tex, rx, ry, rz)` | Draw cylinder |
| `drawCone(x, y, z, radius, height, tex, rx, ry, rz)` | Draw cone |
| `drawPyramid(x, y, z, baseSize, height, tex, rx, ry, rz)` | Draw pyramid |
| `drawTorus(x, y, z, radius, tube, tex, rx, ry, rz)` | Draw torus |
| `drawCapsule(x, y, z, radius, height, tex, rx, ry, rz)` | Draw capsule |
| `drawBillboard(x, y, z, w, h, tex, mode, u0, v0, u1, v1)` | Billboard. `mode` = `true`/`"cylindrical"` for cylindrical; else spherical |
| `drawBillboardRot(tex, x, y, z, w, h, angle [, mode, color])` | Rotated billboard |
| `drawLine3D(x1, y1, z1, x2, y2, z2)` | 3D line |
| `drawLines3D(points)` | Multiple 3D segments |
| `drawGrid3D([size, divs, y])` | 3D grid |
| `drawTriangle3D(p1, p2, p3 [, tex])` | 3D triangle (points as `{x,y,z}`) |
| `drawQuad3D(p1, p2, p3, p4 [, tex])` | 3D quad |
| `drawAxes3D(x, y, z, size)` | Coordinate axes |
| `drawCubeWires(x, y, z, sx, sy, sz [, color, rx, ry, rz])` | Wireframe cube |
| `drawCapsuleWires(x, y, z, radius, halfH [, color, rx, ry, rz])` | Wireframe capsule |
| `drawCylinderWires(x, y, z, radius, halfH [, color, rx, ry, rz])` | Wireframe cylinder |
| `drawRay3D(sx, sy, sz, dx, dy, dz, length, color)` | Draw ray |
| `drawSkeleton(positions, connections [, color])` | positions = `{{x,y,z},...}`, connections = `{{parentIdx, childIdx},...}` (1-indexed) |
| `drawSegmentedMesh(meshes, transforms [, textures])` | Draw segmented mesh; transforms = array of 16-element matrices |
| `project(x, y, z)` | Returns sx, sy, visible |
| `unproject(sx, sy)` | Returns ox, oy, oz, dx, dy, dz |

### 2D Drawing

| Function | Description |
|----------|-------------|
| `drawSprite(tex, x, y, w, h, rot, ox, oy)` | Draw sprite |
| `drawSpritePart(tex, x, y, u0, v0, u1, v1, w, h, rot, ox, oy)` | Draw sprite part |
| `drawSpriteTiled(tex, x, y, w, h, tileW, tileH, ox, oy)` | Tiled sprite |
| `drawSprite9Slice(tex, x, y, w, h, left, top, right, bottom [, texW, texH])` | 9-slice sprite |
| `drawTextureRot(tex, x, y, w, h, angle [, ox, oy])` | Rotated texture |
| `drawPoint(x, y, size)` | Draw point |
| `drawLine(x1, y1, x2, y2, thick)` | Draw line |
| `drawRect(mode, x, y, w, h [, thick])` | Rect ("fill" or "line") |
| `drawRoundedRect(mode, x, y, w, h, radius [, segs])` | Rounded rect |
| `drawRoundedRectEx(mode, x, y, w, h, rtl, rtr, rbr, rbl [, segs])` | Per-corner rounded |
| `drawTriangle(mode, x1, y1, x2, y2, x3, y3)` | Triangle |
| `drawQuad(mode, x1, y1, x2, y2, x3, y3, x4, y4)` | Quad |
| `drawPolygon(mode, points)` | Polygon (`{{x,y},...}` or flat) |
| `drawPolyline(points, thick, loop)` | Polyline |
| `drawCircle(mode, cx, cy, r [, segs])` | Circle |
| `drawEllipse(mode, cx, cy, rx, ry [, segs])` | Ellipse |
| `drawArc(mode, cx, cy, r, a0, a1 [, segs])` | Arc |
| `drawRing(mode, cx, cy, innerR, outerR [, segs])` | Ring |
| `drawPie(mode, cx, cy, r, a1, a2 [, segs])` | Pie slice |
| `drawBezier(x0, y0, x1, y1, x2, y2 [, x3, y3, thick, segs])` | Quadratic or cubic |
| `drawGradientRect(x, y, w, h, cTl, cTr, cBr, cBl)` | 4-corner gradient |
| `drawGradientH(x, y, w, h, cLeft, cRight)` | Horizontal gradient |
| `drawGradientV(x, y, w, h, cTop, cBottom)` | Vertical gradient |
| `drawSkyGradient([topColor, bottomColor])` | Draw vertical sky gradient across screen |
| `drawText(text, x, y [, scale_or_opts])` | Draw text. Opts: `{scale, wrap, align, font}` |
| `getTextWidth(text, scale)` | Text width |
| `getTextHeight(text, scale)` | Text height |

### Rich Text Markup

| Function | Description |
|----------|-------------|
| `drawTextMarkup(text, x, y [, opts])` | Draw markup-formatted text. Opts: `{scale, wrapWidth, align, visibleChars}` |
| `measureTextMarkup(text [, opts])` | Returns width, height, totalPrintableChars |

```lua
crayon.graphics.drawTextMarkup("[wave]Hello[/wave] [color=1,0,0]World[/color]", 10, 10, {
    scale = 2, wrapWidth = 200, align = "center", visibleChars = -1
})
local w, h, total = crayon.graphics.measureTextMarkup("[wave]Hello[/wave]", { scale = 2 })
```

### State

| Function | Description |
|----------|-------------|
| `setBlendMode(mode)` | "alpha", "additive", "multiply", "none" |
| `setScissor(x, y, w, h)` / `resetScissor()` | Scissor rect |
| `pushScissor(x, y, w, h)` / `popScissor()` | Scissor stack |
| `setCamera2D(cam)` / `resetCamera2D()` | 2D camera |

**2D Camera Table:**
```lua
{ x = 0, y = 0, zoom = 1.0, angle = 0.0, originX = 0, originY = 0 }
```

### Camera2D Object

| Function | Description |
|----------|-------------|
| `newCamera2D([x, y, zoom])` | Create a `Graphics.Camera2D` object |

**Camera2D Methods**:
- `:setTarget(x, y)` / `:clearTarget()`
- `:setBounds(x, y, w, h)` / `:clearBounds()`
- `:setDeadzone(w, h)` / `:setLookahead(dx, dy)` / `:setFollowLerp(speed)`
- `:shake(intensity, duration [, frequency])`
- `:moveTo(tx, ty, duration [, ease])` — ease: "linear", "easeIn", "easeOut", "easeInOut"
- `:update(dt)` / `:apply()`
- `:getVisibleRect()` → vx, vy, vw, vh
- `:setPosition(x, y)` / `:getPosition()` / `:setZoom(z)` / `:getZoom()`
- `:setRotation(r)` / `:getRotation()` / `:setOffset(ox, oy)` / `:getOffset()`
- `:screenToWorld(sx, sy)` / `:worldToScreen(wx, wy)`
- `:isMoving()` / `:isShaking()`

```lua
local cam = crayon.graphics.newCamera2D(160, 120, 2.0)
cam:setTarget(player.x, player.y)
cam:setDeadzone(40, 30)
cam:shake(5.0, 0.3)
cam:update(dt)
cam:apply()
```

### Post-Processing

| Function | Description |
|----------|-------------|
| `pushEffect(name_or_shader [, name] [, uniforms])` | Push a post-process effect. Pass built-in name string or `Graphics.Shader` userdata, with optional name and uniform table. |
| `popEffect()` | Pop the last effect |
| `clearEffects()` | Remove all effects |
| `setEffectUniform([effectName_or_idx,] name, value_or_x [, y, z, w])` | Set a uniform on the active/last/target effect. Values may be a number, boolean, or `{x,y}`, `{x,y,z}`, `{x,y,z,w}`. |

**Built-in effects**: `"chromatic"`, `"vignette"`, `"dissolve"`, `"vhs"`, `"bloom2D"`, `"pixelate"`, `"radialBlur"`, `"filmGrain"`.

```lua
crayon.graphics.pushEffect("bloom2D", { intensity = 1.5, threshold = 0.8 })
-- ... draw scene ...
crayon.graphics.setEffectUniform("intensity", 2.0)
crayon.graphics.popEffect()

-- Update by name
crayon.graphics.setEffectUniform("bloom2D", "threshold", 0.9)
```

### Transform Stacks

**3D:** `pushMatrix()`, `popMatrix()`, `translate(x,y,z)`, `rotate(angle, ax,ay,az)`, `scale(sx,sy,sz)`

**2D:** `pushMatrix2D()`, `popMatrix2D()`, `translate2D(x,y)`, `rotate2D(angle)`, `scale2D(sx,sy)`

---

## Physics3D Module
Access via: `crayon.physics3D`

### Body Creation

| Function | Description |
|----------|-------------|
| `createBox(x, y, z, hx, hy, hz [, motion, friction, restitution, density])` | Box body |
| `createSphere(x, y, z, radius [, motion, friction, restitution, density])` | Sphere body |
| `createCapsule(x, y, z, halfH, radius [, motion, friction, restitution, density])` | Capsule body |
| `createCylinder(x, y, z, halfH, radius [, motion, friction, restitution, density])` | Cylinder body |
| `createPlane(x, y, z [, nx, ny, nz, halfExtent])` | Static plane |
| `createMeshBody(x, y, z, model, friction, restitution)` | Mesh from Model |
| `createMeshBody(model, friction, restitution)` | Mesh at origin |
| `createMeshBody(x, y, z, vertices, indices, friction, restitution)` | From flat tables |
| `createMeshBody(meshData, friction, restitution)` | `meshData = {vertices={...}, indices={...}}` |

**Motion Types**: `"static"`, `"kinematic"`, `"dynamic"` (or `0`, `1`, `2`). Default: `"dynamic"`.

### Body Methods

| Method | Description |
|--------|-------------|
| `:getId()` | Returns body ID |
| `:isValid()` | Body still exists? |
| `:isActive()` / `:setActive(active)` | Active state |
| `:destroy()` | Destroy body |
| `:getPosition()` / `:setPosition(x, y, z [, activate])` | Position |
| `:getRotation()` / `:setRotation(rx, ry, rz [, activate])` | Euler rotation (radians) |
| `:getVelocity()` / `:setVelocity(vx, vy, vz)` | Linear velocity |
| `:getAngularVelocity()` / `:setAngularVelocity(wx, wy, wz)` | Angular velocity |
| `:applyForce(fx, fy, fz)` | Apply force |
| `:applyImpulse(ix, iy, iz)` | Apply impulse |
| `:applyTorque(tx, ty, tz)` | Apply torque |
| `:setGravityFactor(f)` | Gravity multiplier |
| `:setFriction(f)` / `:setRestitution(r)` | Physics material |
| `:setMotionType(type)` | Change motion type |
| `:setMotionQuality(mode)` | `true` or `"linearCast"` for CCD; else discrete |
| `:setPlanarLock(plane)` | "xy", "xz", "yz" for planar 2D-in-3D constraint |
| `:setDamping(linear [, angular])` | Set damping |
| `:setSensor(bool)` / `:isSensor()` | Sensor (trigger) mode |

### World Operations

| Function | Description |
|----------|-------------|
| `step([dt, collisionSteps])` | Advance simulation (default: 1/60s, 1 step) |
| `setGravity(gx, gy, gz)` / `getGravity()` | World gravity |
| `destroyAll()` | Destroy all bodies |
| `getBodyCount()` | Returns total, active body count |
| `getBody(id)` | Returns Body or nil |
| `raycast(ox, oy, oz, dx, dy, dz [, maxDist])` | Returns `hit, px,py,pz, nx,ny,nz, dist, body` |
| `overlapSphere(cx, cy, cz, radius)` | Array of bodies in sphere |
| `drawDebug([opts])` or `drawDebug(r,g,b,a, sr,sg,sb,sa [, flags])` | Debug visualization |

**Debug Flags:**
```lua
{
    shapes = true, softBodies = true, constraints = true,
    softBodyConstraints = true, softBodyRods = true,
    bounds = false, velocities = false,
    characters = false, vehicles = false, ragdolls = false
}
```

### Constraints

| Function | Description |
|----------|-------------|
| `createPointConstraint(b1, b2, px, py, pz)` | Point constraint |
| `createHingeConstraint(b1, b2, px, py, pz, ax, ay, az)` | Hinge |
| `createDistanceConstraint(b1, b2, p1x, p1y, p1z, p2x, p2y, p2z [, minD, maxD])` | Distance |
| `createFixedConstraint(b1, b2)` | Fixed |
| `destroyConstraint(c)` | Destroy (userdata or id) |

**Constraint Methods**: `:destroy()`, `:isValid()`, `:getId()`

### Characters

| Function | Description |
|----------|-------------|
| `createCharacter(opts)` | Create character controller |
| `createCharacterVirtual(opts)` | Create kinematic virtual character |

**Character Options:**
```lua
{
    pos = {x, y, z},
    radius = 0.4,
    halfHeight = 0.6,
    mass = 80.0,
    friction = 0.5,
    gravityFactor = 1.0,
    maxSlopeAngleDeg = 45.0,
    motion = "dynamic"
}
```

**Virtual Character Extra Options:**
```lua
{
    maxStrength = 100.0,
    stepHeight = 0.5,
    predictiveContactDistance = 0.1,
    innerBody = true
}
```

**Character Methods**: `:getId()`, `:isValid()`, `:destroy()`, `:getBodyId()`, `:getPosition()`, `:setPosition(x,y,z)`, `:getRotation()`, `:setRotation(x,y,z,w)`, `:getLinearVelocity()`, `:setLinearVelocity(vx,vy,vz)`, `:isSupported()`, `:getGroundState()`, `:getGroundNormal()`, `:getGroundVelocity()`, `:getGroundPosition()`

**Ground states**: `"onGround"`, `"onSteepGround"`, `"notSupported"`, `"inAir"`

**Virtual Character Methods**: same as Character plus `:update(dt)`

### Vehicles

| Function | Description |
|----------|-------------|
| `createWheeledVehicle(cfg)` | Wheeled vehicle |
| `createTrackedVehicle(cfg)` | Tracked vehicle |
| `createMotorcycle(cfg)` | Motorcycle |

**Wheel Config:**
```lua
{
    position = {x, y, z},
    radius = 0.3,
    width = 0.2,
    suspensionMinLength = 0.1,
    suspensionMaxLength = 0.5,
    suspensionSpring = 1000.0,
    suspensionDamping = 50.0,
    maxSteerAngleRad = 0.5,
    maxBrakeTorque = 100.0,
    maxHandBrakeTorque = 200.0,
    isFront = true,
    isDrive = true
}
```

**Wheeled Vehicle Config:**
```lua
{
    chassis = body,
    wheels = { wheel1, wheel2, ... },
    maxPitchRollAngle = 0.5,
    engineMaxTorque = 500.0,
    engineMinRpm = 1000.0,
    engineMaxRpm = 6000.0
}
```

**Tracked Vehicle Config:**
```lua
{
    chassis = body,
    leftWheels = { ... },
    rightWheels = { ... },
    engineMaxTorque = 500.0
}
```

**Motorcycle Config:**
```lua
{
    chassis = body,
    frontWheel = { ... },
    rearWheel = { ... },
    maxLeanAngleRad = 0.7,
    leanSpringConstant = 500.0,
    leanSpringDamping = 50.0,
    leanSmoothingFactor = 0.15,
    engineMaxTorque = 200.0
}
```

**Vehicle Methods**: `:getId()`, `:isValid()`, `:destroy()`, `:setInputWheeled(forward, steer, brake, handbrake)`, `:setInputTracked(leftRatio, rightRatio, brake)`, `:setInputMotorcycle(forward, steer, brake)`, `:enableLeanController(enabled)`, `:isLeanControllerEnabled()`, `:getLeanAngle()`, `:getSpeedKmh()`, `:getEngineRpm()`, `:getTransmissionGear()`, `:getWheelCount()`, `:getWheelTransform(idx)`

### Skeleton / Pose / Mapper

| Function | Description |
|----------|-------------|
| `createSkeleton(joints)` | Create skeleton from `{{name, parentIndex}, ...}` or `{{name="X", parentIndex=N}, ...}` |
| `createSkeletonPose(skel)` | Create pose |
| `createSkeletonMapper(skelLow, skelHigh, poseLow, poseHigh)` | Create mapper |
| `createRagdoll(cfg)` | Create ragdoll |

**Skeleton Methods**: `:getId()`, `:isValid()`, `:destroy()`

**SkeletonPose Methods**: `:getId()`, `:isValid()`, `:destroy()`, `:setJoint(idx, tx, ty, tz, rx, ry, rz, rw)`, `:calculateMatrices()`, `:getJointMatrix(idx)` → 16-element array, `:setRootOffset(x,y,z)`, `:getRootOffset()`, `:getJointCount()`

**SkeletonMapper Methods**: `:getId()`, `:isValid()`, `:destroy()`, `:map(poseLow, poseHighLocal, poseHighOutModel)`, `:mapReverse(poseHighModel, poseLowOutModel)`, `:lockAllTranslations(skelHigh, neutralPose)`

### Ragdoll

**Ragdoll Config:**
```lua
{
    disableParentChildCollisions = false,
    stabilize = true,
    parts = {
        {
            name = "Head",
            parentJointIndex = 0,
            position = {x, y, z},
            rotation = {x, y, z, w},        -- quaternion
            shapeType = "capsule",          -- "box", "sphere", "capsule"
            halfExtent = {hx, hy, hz},
            radius = 0.15,
            halfHeight = 0.1,
            motion = "dynamic",
            mass = 5.0,
            friction = 0.5,
            swingLimitY = 0.5,
            swingLimitZ = 0.5,
            twistMin = -0.3,
            twistMax = 0.3,
            enableMotors = true,
            motorSpringK = 100.0,
            motorDampingC = 10.0,
            motorMaxTorque = 50.0
        }
    }
}
```

**Ragdoll Methods**:
- Core: `:getId()`, `:isValid()`, `:destroy()`, `:activate()`, `:isActive()`, `:getPartCount()`, `:getSkeletonId()`
- Pose: `:setPose(pose)`, `:getPose(pose)`, `:setHardKeying(enabled)`
- Driving: `:driveToPoseKinematics(pose, dt)`, `:driveToPoseMotors(pose)`, `:driveToPoseMotorsVelocity(prevPose, pose, dt)`
- Velocities: `:setLinearVelocity(x,y,z)`, `:setLinearAndAngularVelocity(lx,ly,lz, ax,ay,az)`, `:addLinearVelocity(x,y,z)`, `:addImpulse(x,y,z)`, `:addImpulseToPart(partIdx, x,y,z)`, `:addImpulseToPartAtPos(partIdx, ix,iy,iz, px,py,pz)`, `:resetWarmStart()`
- Transforms: `:getRootTransform()` → px,py,pz, qx,qy,qz,qw; `:getGroundOrientation()` → "back"/"belly"/"unknown"; `:getBounds()` → 6 values
- Parts: `:getBodyId(partIdx)`, `:getPartPosition(i)`, `:getPartRotation(i)`, `:getPartLinearVelocity(i)`, `:getLinearVelocity()`, `:getBody(i)`
- Motors: `:setMotorsStiffness(k [, c, maxTorque])`, `:setPartMotor(i, k [, c, maxTorque])`, `:setPartMotionType(i, motion)`, `:setPartFriction(i, f)`, `:setPartRestitution(i, r)`

### Soft Bodies

| Function | Description |
|----------|-------------|
| `createSoftBody(config)` | Full config soft body |
| `createSoftBodyCloth(opts_or_x, y, z, w, h, segX, segY, compliance, bendCompliance, pinCorners, addLra)` | Cloth |
| `createSoftBodyCube(opts_or_x, y, z, size, gridSize, compliance, pressure)` | Soft cube |
| `createSoftBodySphere(opts_or_x, y, z, radius, rings, sectors, compliance, pressure)` | Soft sphere |
| `createSoftBodyRod(opts)` | Rod from points |
| `destroySoftBody(sb_or_id)` | Destroy (userdata or id) |

**Cloth Options:**
```lua
{ x=0, y=0, z=0, width=4.0, height=4.0, segmentsX=10, segmentsY=10,
  compliance=0.0, bendCompliance=0.01, pinCorners=true, addLra=true }
```

**Cube Options:** `{ x=0, y=0, z=0, size=2.0, gridSize=3, compliance=0.0, pressure=0.0 }`

**Sphere Options:** `{ x=0, y=0, z=0, radius=1.0, rings=8, sectors=12, compliance=0.0, pressure=500.0 }`

**Rod Options:**
```lua
{
    points = { {x,y,z}, {x,y,z}, ... },   -- required
    stretchCompliance = 0.0,
    bendTwistCompliance = 0.001,
    pinRoot = true
}
```

**Full Config (`createSoftBody`):**
```lua
{
    position = {x, y, z},
    rotation = {x, y, z, w},              -- quaternion
    vertices = { {x, y, z, mass=1.0}, ... },
    faces = { {v1, v2, v3}, ... },        -- 1-indexed
    edges = { {v1, v2, compliance=0.0}, ... },        -- or `edgeConstraints`
    bends = { {v1, v2, v3, v4, compliance}, ... },    -- or `dihedralBendConstraints`
    volumes = { {v1, v2, v3, v4, compliance}, ... },  -- or `volumeConstraints`
    tethers = { {kinematicV, dynamicV, maxDistance}, ... },  -- or `lraConstraints`
    rods = { {v1, v2, compliance}, ... },             -- or `rodStretchShearConstraints`
    rodBendTwistConstraints = { {rod0, rod1, compliance}, ... },

    pressure = 0.0,
    vertexRadius = 0.0,
    linearDamping = 0.0,
    maxLinearVelocity = 0.0,
    friction = 0.5,
    restitution = 0.2,
    gravityFactor = 1.0,
    numIterations = 3,
    updatePosition = true,
    allowSleeping = true,
    facesDoubleSided = true,

    autoGenerateConstraints = true,
    compliance = 0.0,
    shearCompliance = 0.0,
    bendCompliance = 0.0,
    lraMultiplier = 1.0,
    bendType = "dihedral",                -- "dihedral", "distance", "none"
    lraType = "euclidean"                 -- "euclidean", "geodesic", "none"
}
```

**SoftBody Methods:**

| Method | Description |
|--------|-------------|
| `:getId()` / `:isValid()` / `:destroy()` | Identity & lifetime |
| `:getBodyId()` | Underlying physics body ID |
| `:getPosition()` / `:setPosition(x,y,z)` | Body position |
| `:getRotation()` / `:setRotation(x,y,z,w)` | Body rotation (quaternion) |
| `:getVertexCount()` | Vertex count |
| `:getVertex(idx)` | `px, py, pz, vx, vy, vz, invMass` (1-indexed) |
| `:setVertex(idx, x, y, z [, vx, vy, vz [, invMass]])` | Set vertex data |
| `:getVertices()` / `:getVerticesFlat()` | Vertex positions |
| `:getFaces()` / `:getFacesFlat()` | Faces (1-indexed) |
| `:getPressure()` / `:setPressure(p)` | Pressure |
| `:getNumIterations()` / `:setNumIterations(n)` | Solver iterations |
| `:getVolume()` | Current volume |
| `:applyImpulse(ix, iy, iz)` | Impulse to all vertices |
| `:applyImpulse(vertexIdx, ix, iy, iz)` | Impulse to one vertex |
| `:applyForce(fx, fy, fz)` | Force to all vertices |
| `:applyForce(vertexIdx, fx, fy, fz)` | Force to one vertex |
| `:skinVertices(jointMatrices [, hardSkin])` | Skin to 16-element matrices |
| `:setSkinnedMaxDistanceMultiplier(mult)` | Skinned distance multiplier |
| `:getRodTransform(rodIdx)` | `px, py, pz, qx, qy, qz, qw` |
| `:activate()` / `:isActive()` | Wake state |

---

## Physics2D Module
Access via: `crayon.physics2D`

### World Operations

| Function | Description |
|----------|-------------|
| `createBody(type, x, y [, opts])` | Create body. `type` = `"static"`, `"kinematic"`, `"dynamic"` |
| `destroyBody(body_or_id)` | Destroy body |
| `setGravity(gx, gy)` / `getGravity()` | World gravity |
| `setMeterScale(scale)` / `getMeterScale()` | Pixels-per-meter scale |
| `raycast(x1, y1, x2, y2)` | Returns `hit, px, py, nx, ny, fraction, bodyId` |
| `drawDebug()` | Draw debug visualization |

**Body Options:**
```lua
{ fixedRotation = false, linearDamping = 0.0, angularDamping = 0.0,
  gravityScale = 1.0, bullet = false, allowSleep = true }
```

### Joints

| Function | Description |
|----------|-------------|
| `createDistanceJoint(bA, bB, ax1, ay1, ax2, ay2 [, length, freq, damping, collide])` | Distance joint |
| `createRevoluteJoint(bA, bB, ax, ay [, enableLimit, lower, upper, enableMotor, speed, maxTorque, collide])` | Revolute (hinge) |
| `createPrismaticJoint(bA, bB, ax, ay, axisX, axisY [, enableLimit, lower, upper, enableMotor, speed, maxForce, collide])` | Prismatic (slider) |
| `createWeldJoint(bA, bB, ax, ay [, freq, damping, collide])` | Weld joint |
| `createWheelJoint(bA, bB, ax, ay, axisX, axisY [, freq, damping, collide])` | Wheel joint |
| `destroyJoint(joint_or_id)` | Destroy joint |

### Physics2D.Body

| Method | Description |
|--------|-------------|
| `:addBox(w, h [, ox, oy, angle, density, friction, restitution, isSensor])` | Add box fixture |
| `:addCircle(r [, ox, oy, density, friction, restitution, isSensor])` | Add circle fixture |
| `:addPolygon(verts [, density, friction, restitution, isSensor])` | verts is flat `{x1,y1,x2,y2,...}` |
| `:addEdge(x1, y1, x2, y2 [, friction, restitution, isSensor])` | Edge fixture |
| `:addChain(verts, loop [, friction, restitution, isSensor])` | Chain fixture |
| `:getPosition()` / `:setPosition(x, y)` | Position |
| `:getAngle()` / `:setAngle(rad)` | Rotation |
| `:getLinearVelocity()` / `:setLinearVelocity(vx, vy)` | Linear velocity |
| `:getAngularVelocity()` / `:setAngularVelocity(w)` | Angular velocity |
| `:applyForce(fx, fy [, px, py])` | Force (optional world point) |
| `:applyImpulse(ix, iy [, px, py])` | Impulse |
| `:applyTorque(t)` / `:applyAngularImpulse(i)` | Torque / angular impulse |
| `:setGravityScale(s)` / `:getGravityScale()` | Gravity scale |
| `:setFixedRotation(bool)` / `:isFixedRotation()` | Fixed rotation |
| `:setBullet(bool)` / `:isBullet()` | CCD flag |
| `:setEnabled(bool)` / `:isEnabled()` | Enable/disable |
| `:setAwake(bool)` / `:isAwake()` | Sleep state |
| `:getId()` / `:isValid()` / `:destroy()` | Identity & lifetime |

### Physics2D.Joint

`:destroy()`, `:isValid()`, `:getId()`

### Physics2D Example

```lua
crayon.physics2D.setGravity(0, 980)
crayon.physics2D.setMeterScale(32.0)

local ground = crayon.physics2D.createBody("static", 160, 220)
ground:addBox(320, 20)

local box = crayon.physics2D.createBody("dynamic", 160, 100)
box:addBox(20, 20, 0, 0, 0, 1.0, 0.3, 0.1)

function crayon.update(dt)
    -- Physics step happens automatically via the engine
end

function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)
    crayon.graphics.setColor(1, 1, 1)
    local bx, by = box:getPosition()
    crayon.graphics.drawRect("fill", bx - 10, by - 10, 20, 20)
end
```

---

## Physics4D Module
Access via: `crayon.physics4D`

A real 4D rigid-body engine (the **hv4d** library in `vendor/hypervis4d`, a C++ re-creation of the
*hypervis* 4D physics engine). Bodies live in a world with four spatial axes `x, y, z, w` (`y` is up;
`w` is the extra dimension). Since you can only *see* 3D, the engine renders the **3D slice** where the
world meets a hyperplane (by default `w = sliceW`): move the slice to scan through the objects.

* Shapes: the six regular 4-polytopes — `"5cell"`, `"8cell"` (tesseract), `"16cell"`, `"24cell"`,
  `"120cell"`, `"600cell"` — plus hyperspheres and half-spaces (infinite walls/floors).
* Rotations are **bivectors** (rotation *planes*), not quaternions. Order everywhere is
  `xy, xz, xw, yz, yw, zw`. `xy, xz, yz` are ordinary 3D rotations; `xw, yw, zw` turn an object
  "into" the 4th axis (this is what makes a cross-section morph as it spins).
* The engine steps the world at a fixed 60 Hz automatically.

### Body Creation

| Function | Description |
|----------|-------------|
| `createPolytope(shape, x, y, z, w [, scale] [, opts])` | Convex 4-polytope. `scale` = circumradius (default 1) |
| `createTesseract(x, y, z, w [, edgeLength] [, opts])` | Shortcut for `"8cell"` (scale = edge length) |
| `createHypersphere(x, y, z, w [, radius] [, opts])` | Hypersphere (default radius 0.5) |
| `createHalfSpace(px, py, pz, pw, nx, ny, nz, nw [, opts])` | Static infinite wall; the normal points to the *empty* side |
| `createArena([halfSize=10, friction=0.4, restitution=0.4])` | Floor at `y=0` + walls at `±halfSize` on `x`, `z`, `w` |
| `getShapes()` | List of valid polytope names |

**Options** (`opts`, all optional):
```lua
{ type = "dynamic" | "static" | "sensor",   -- "sensor": static trigger volume, no collision response
  mass = 1.0, restitution = 0.2, friction = 0.4, sensor = false,
  linearDamping = 0, angularDamping = 0, gravityScale = 1,
  scale = 1,                                 -- (polytopes) same as the positional argument
  rotation = {xy, xz, xw, yz, yw, zw},       -- initial orientation (plane angles, radians)
  velocity = {vx, vy, vz, vw},
  angularVelocity = {xy, xz, xw, yz, yw, zw} }
```

### World Operations

| Function | Description |
|----------|-------------|
| `destroyBody(body_or_id)` / `destroyAll()` | Remove bodies |
| `getBody(id)` / `getBodyCount()` | Look up a body handle / count bodies |
| `setGravity(gx, gy, gz, gw)` / `getGravity()` | World gravity (default `0, -9.8, 0, 0`) |
| `setSolverIterations(n)` | Contact solver iterations (default 20) |
| `step(dt)` | Manual step (the engine already steps at 60 Hz) |
| `raycast(ox,oy,oz,ow, dx,dy,dz,dw [, maxDist])` | `hit, px,py,pz,pw, nx,ny,nz,nw, distance, bodyId` (just `false` on a miss) |
| `overlapSphere(x, y, z, w, radius)` | Table of body ids overlapping a hypersphere |
| `testOverlap(bodyA, bodyB)` | Exact GJK+EPA test. Overlap: `true, depth, nx,ny,nz,nw`. Apart: `false, distance, dx,dy,dz,dw` (A → B). No half-spaces |

### Slice Control

| Function | Description |
|----------|-------------|
| `setSlice(w)` / `getSlice()` | Slice at constant `w` (the default `w = 0`) |
| `setSliceHyperplane(nx,ny,nz,nw [, bx,by,bz,bw])` | Any hyperplane: a normal plus a point on it |
| `getSliceNormal()` | Current slice normal |
| `sliceToWorld(x, y, z)` | 3D slice-space point → 4D world point |
| `sliceDirectionToWorld(x, y, z)` | 3D slice-space direction → 4D direction |
| `worldToSlice(x, y, z, w)` | `sx, sy, sz, distanceToSlice` |

Use `sliceToWorld` / `sliceDirectionToWorld` to turn `crayon.graphics.getCameraRay()` into a 4D ray for
mouse picking (see `examples/19_physics4d.lua`).

### Debug Rendering

`drawDebug([flags])` draws everything through the 3D renderer — call it from `crayon.draw()` after
`setCamera3D`:

```lua
crayon.physics4D.drawDebug({
    shapes = true,       -- wireframe of each body's current 3D cross-section
    fill = false,        -- lit, filled cross-section surfaces
    projection = false,  -- ghost wireframe of the *whole* 4D body, fading with distance from the slice
    contacts = true,     -- contact points + normals (projected into the slice)
    bounds = false,      -- bounding hyperspheres
    velocities = false,  -- velocity arrows (a +/- cross marks motion along the slice normal, i.e. w)
    planes = true,       -- grid patches for half-spaces
    color = {0.2, 1, 0.4, 1}, staticColor = {...}, sensorColor = {...}, contactColor = {...},
    projectionRange = 3.0, planeExtent = 8.0, planeDivisions = 8,
})
```

### Physics4D.Body

| Method | Description |
|--------|-------------|
| `:getId()` / `:isValid()` / `:destroy()` | Identity & lifetime |
| `:getPosition()` / `:setPosition(x,y,z,w)` | Position (4 values) |
| `:getLinearVelocity()` / `:setLinearVelocity(x,y,z,w)` | Linear velocity (`getVelocity`/`setVelocity` are aliases) |
| `:getAngularVelocity()` / `:setAngularVelocity(xy,xz,xw,yz,yw,zw)` | Angular velocity bivector (body frame) |
| `:getRotor()` | Orientation rotor: `s, xy,xz,xw,yz,yw,zw, xyzw` |
| `:setRotation(xy,xz,xw,yz,yw,zw)` / `:rotateBy(...)` / `:resetRotation()` | Set / add a rotation / identity |
| `:localToWorld(x,y,z,w)` / `:worldToLocal(x,y,z,w)` / `:localDirectionToWorld(...)` | Frame conversion |
| `:applyImpulse(ix,iy,iz,iw [, px,py,pz,pw])` | Impulse (optional world point → also spins the body) |
| `:applyForce(fx,fy,fz,fw)` / `:applyTorque(xy,xz,xw,yz,yw,zw)` | Applied on the next step |
| `:getMass()` / `:setMass(m)` | Mass (inertia is recomputed from the shape) |
| `:isStatic()` / `:setStatic(bool)` | Static ↔ dynamic (original mass is kept) |
| `:isSensor()` / `:setSensor(bool)` | Sensors report overlaps (trigger events) but never push |
| `:getRestitution()` / `:setRestitution(r)` / `:getFriction()` / `:setFriction(f)` | Material |
| `:getGravityScale()` / `:setGravityScale(s)` / `:setDamping(linear [, angular])` | Dynamics tweaks |
| `:getShape()` | `"8cell"`, `"600cell"`, …, `"hypersphere"`, `"halfspace"` |
| `:getRadius()` / `:getHalfSpaceNormal()` / `:getVertices()` | Shape info (world-space vertices, flat `{x,y,z,w,...}`) |
| `:getSliceSegments()` / `:getSliceTriangles()` / `:getSliceSphere()` | The body's current cross-section as raw 3D geometry, for custom rendering |
| `:distanceToSlice()` | Signed distance of the body's centre from the slice |

### Physics4D Callbacks

```lua
function crayon.onCollision4DEnter(a, b, nx, ny, nz, nw, impulse) end  -- normal points a -> b
function crayon.onCollision4DExit(a, b) end
function crayon.onTrigger4DEnter(sensor, other) end
function crayon.onTrigger4DExit(sensor, other) end
```

### Physics4D Example

```lua
local P = crayon.physics4D
P.createArena(6.0)                                   -- floor + walls (x, z and w)

local box  = P.createTesseract(0, 3, 0, 0.4)         -- 4D box, slightly off the w = 0 slice
local ball = P.createHypersphere(2, 1, 0, 0, 0.5)
ball:setLinearVelocity(-3, 2, 0, 0)

function crayon.update(dt)
    P.setSlice(math.sin(crayon.time.getTime()) * 1.5) -- sweep the slice through the objects
    box:rotateBy(0, 0, 0.01, 0, 0, 0)                 -- spin in the xw plane (impossible in 3D)
end

function crayon.draw()
    crayon.graphics.clear(0.05, 0.06, 0.1)
    crayon.graphics.setCamera3D({ position = {0, 6, 12}, target = {0, 1, 0}, up = {0, 1, 0}, fov = 50 })
    P.drawDebug({ fill = true, projection = true })
end
```

---

## Audio Module
Access via: `crayon.audio`

### Sound Effects

| Function | Description |
|----------|-------------|
| `loadSound(path)` | Load a sound effect, returns ID |
| `unloadSound(id)` | Unload a sound, returns bool |
| `playSound(id [, volume, pitch, pan, loop])` | Play a sound effect, returns voice ID |
| `playSound(id, opts)` | Play with `{volume, pitch, pan, loop}` table |
| `playSound3D(id, x, y, z [, opts])` | Positional 3D sound. Opts: `{volume, pitch, minDist, maxDist}` |
| `stopSound(voiceId)` | Stop a specific voice |
| `stopAllSounds()` | Stop all playing sounds |
| `isSoundPlaying(voiceId)` | Returns bool |

### Music

| Function | Description |
|----------|-------------|
| `playMusic(path [, loop, fadeIn])` | Play background music, returns bool |
| `playMusic(path, opts)` | Opts: `{loop, fadeIn}` |
| `stopMusic([fadeOut])` | Stop music with optional fade |
| `pauseMusic()` / `resumeMusic()` | Pause / resume music |
| `isMusicPlaying()` | Returns bool |

### Volume & Listener

| Function | Description |
|----------|-------------|
| `setMasterVolume(v)` / `getMasterVolume()` | Master volume (0–1) |
| `setMusicVolume(v)` / `getMusicVolume()` | Music volume |
| `setSfxVolume(v)` / `getSfxVolume()` | SFX volume |
| `setListenerPosition(x, y, z)` | 3D audio listener position |
| `setListenerOrientation(fx, fy, fz [, ux, uy, uz])` | Listener forward and up vectors |

```lua
local coin = crayon.audio.loadSound("coin.wav")
crayon.audio.playSound(coin, { volume = 0.8, pitch = 1.0 })
crayon.audio.playMusic("bgm.ogg", { loop = true, fadeIn = 2.0 })
```

---

## Particles Module
Access via: `crayon.particles`

| Function | Description |
|----------|-------------|
| `createEmitter(config)` | Create a particle emitter |

**Emitter Config:**
```lua
{
    maxParticles = 1000,
    emissionRate = 50.0,            -- particles per second
    lifetimeMin = 0.5,
    lifetimeMax = 1.5,
    sizeStart = 0.5,
    sizeEnd = 0.0,
    gravity = -9.8,                 -- applied to Y axis
    blendMode = "additive",         -- "alpha", "additive", "multiply"
    is3d = false
}
```

**Emitter Methods:**

| Method | Description |
|--------|-------------|
| `:emit([count])` | Emit N particles (default 1) |
| `:burst(count)` | Emit a burst of particles |
| `:update(dt)` | Advance simulation |
| `:draw()` | Draw with 2D batch renderer |
| `:draw3D()` | Draw with 3D mesh renderer |
| `:reset()` | Reset all particles |
| `:setPosition(x, y [, z])` | Set emitter position |
| `:setEmissionRate(rate)` | Set particles per second |
| `:setActive(active)` | Enable/disable emission |
| `:getAliveCount()` | Number of live particles |

```lua
local fire = crayon.particles.createEmitter({
    maxParticles = 500,
    emissionRate = 100,
    lifetimeMin = 0.3, lifetimeMax = 0.8,
    blendMode = "additive",
    is3d = true
})
fire:setPosition(0, 1, 0)

function crayon.update(dt)
    fire:update(dt)
end

function crayon.draw()
    fire:draw3D()
end
```

---

## Math Module
Access via: `crayon.math`

### Scalars & Interpolation

| Function | Description |
|----------|-------------|
| `lerp(a, b, t)` | Linear interpolation |
| `clamp(v, min, max)` | Clamp value |
| `smoothstep(e0, e1, x)` | Hermite smoothstep |
| `remap(val, inMin, inMax, outMin, outMax)` | Remap range |
| `damp(a, b, lambda, dt)` | Exponential damping |
| `noise(x [, y])` | Smooth value noise |

### 2D Vectors

| Function | Description |
|----------|-------------|
| `vec2Length(x, y)` | Length |
| `vec2Normalize(x, y)` | Returns nx, ny |
| `vec2Dot(x1, y1, x2, y2)` | Dot product |
| `vec2Distance(x1, y1, x2, y2)` | Distance |

### 3D Vectors

| Function | Description |
|----------|-------------|
| `vec3Length(x, y, z)` | Length |
| `vec3Normalize(x, y, z)` | Returns nx, ny, nz |
| `vec3Cross(x1,y1,z1, x2,y2,z2)` | Returns cx, cy, cz |
| `vec3Dot(x1,y1,z1, x2,y2,z2)` | Dot product |
| `vec3Distance(x1,y1,z1, x2,y2,z2)` | Distance |

### Quaternions

| Function | Description |
|----------|-------------|
| `quatFromEuler(pitch, yaw, roll)` | Returns qx, qy, qz, qw |
| `quatSlerp(q1x,q1y,q1z,q1w, q2x,q2y,q2z,q2w, t)` | Returns interpolated quaternion |

```lua
local t = crayon.math.clamp(crayon.time.getTime(), 0, 1)
local x = crayon.math.lerp(0, 100, t)
local nx, ny = crayon.math.vec2Normalize(3, 4)
local value = crayon.math.noise(10.5, 3.2)
```

---

## File System Module
Access via: `crayon.fs`

| Function | Description |
|----------|-------------|
| `exists(path)` | Returns bool |
| `isFile(path)` | Returns bool |
| `isDirectory(path)` | Returns bool |
| `readText(path)` | Returns string or nil, error |
| `writeText(path, content)` | Write file, creates parent dirs, returns bool [, error] |
| `appendText(path, content)` | Append to file, returns bool [, error] |
| `listDir(path)` | Array of filenames |
| `getSaveDir([org, app])` | Platform-appropriate save directory |

```lua
local data = crayon.fs.readText("config.json")
crayon.fs.writeText("saves/slot1.dat", "player data")
local save_dir = crayon.fs.getSaveDir("MyGame", "MyProject")
for _, f in ipairs(crayon.fs.listDir("assets/")) do
    print(f)
end
```

---

## Configuration

### `crayon.config(t)`

Invoked during the config phase (before the engine starts). Receives a table `t` that can be mutated to influence engine startup. All fields are optional.

```lua
function crayon.config(t)
    t.identity = "MyGame"
    t.version = "1.0.0"
    t.fpsLimit = 60
    t.console = false

    t.window = {
        title = "My Game",
        width = 1280, height = 720,
        virtualWidth = 320, virtualHeight = 240,
        minWidth = 640, minHeight = 360,
        resizable = true,
        fullscreen = false,
        vsync = true,
        transparent = false,
        borderless = false,
        alwaysOnTop = false,
        clickThrough = false,
        opacity = 1.0,
        skipTaskbar = false,
        notFocusable = false,
        utilityWindow = false,
        scaling = "integer"           -- "integer" | "aspect" | "stretch" | "center"
    }

    t.modules = {
        physics3D = true,
        physics2D = true,
        physics4D = true,
        audio = true,
        mesh3D = true,
        particles = true,
        input = true,
        fs = true
    }

    t.graphics = {
        clearColor = {0.1, 0.1, 0.15, 1.0},
        dither = false,
        crt = false,
        vignette = false
    }
end
```

**Disabling a module** replaces its table with a stub that raises an error when any member is accessed. For example, `t.modules.physics3D = false` will make `crayon.physics3D` unusable at runtime.

---

## Lua Callbacks

The runtime invokes these optional `crayon.*` functions. Only the canonical camelCase names are supported — the previous snake_case aliases have been removed.

### Lifecycle

| Callback | Args |
|----------|------|
| `crayon.config(t)` | t |
| `crayon.init()` | — |
| `crayon.update(dt)` | dt |
| `crayon.draw()` | — |
| `crayon.quit()` | — |

### Input Events

| Callback | Args |
|----------|------|
| `crayon.keydown(key, isRepeat)` | key, is_repeat |
| `crayon.keyup(key)` | key |
| `crayon.mousedown(x, y, button)` | x, y, btn |
| `crayon.mouseup(x, y, button)` | x, y, btn |
| `crayon.mousemoved(x, y, dx, dy)` | x, y, dx, dy |
| `crayon.wheelmoved(dx, dy)` | dx, dy |
| `crayon.textinput(text)` | text |
| `crayon.gamepaddown(btn)` | btn |
| `crayon.gamepadup(btn)` | btn |
| `crayon.gamepadaxis(axis, value)` | axis, value |

### Window Events

| Callback | Args |
|----------|------|
| `crayon.windowResized(w, h)` | w, h |
| `crayon.focusChanged(focused)` | bool |

### Physics Events (3D)

| Callback | Args |
|----------|------|
| `crayon.onCollisionEnter(bodyA, bodyB, nx, ny, nz, impulse)` | ids, normal, impulse |
| `crayon.onCollisionExit(bodyA, bodyB)` | ids |
| `crayon.onTriggerEnter(sensorId, otherBodyId)` | ids |
| `crayon.onTriggerExit(sensorId, otherBodyId)` | ids |

### Physics Events (2D)

| Callback | Args |
|----------|------|
| `crayon.onCollision2DEnter(bodyA, bodyB, nx, ny, impulse)` | ids, normal, impulse |
| `crayon.onCollision2DExit(bodyA, bodyB)` | ids |
| `crayon.onTrigger2DEnter(sensorId, otherBodyId)` | ids |
| `crayon.onTrigger2DExit(sensorId, otherBodyId)` | ids |

### Physics Events (4D)

| Callback | Args |
|----------|------|
| `crayon.onCollision4DEnter(bodyA, bodyB, nx, ny, nz, nw, impulse)` | ids, 4D normal (A → B), impulse |
| `crayon.onCollision4DExit(bodyA, bodyB)` | ids |
| `crayon.onTrigger4DEnter(sensorId, otherBodyId)` | ids |
| `crayon.onTrigger4DExit(sensorId, otherBodyId)` | ids |

### Drag & Drop Events

| Callback | Args |
|----------|------|
| `crayon.dropBegin(x, y)` | x, y |
| `crayon.dropFile(path, x, y)` | path, x, y |
| `crayon.dropText(text, x, y)` | text, x, y |
| `crayon.dropPosition(x, y)` | x, y |
| `crayon.dropComplete()` | — |

---

## Complete Examples

### Example 1: Minimal 2D Game

```lua
local player = { x = 160, y = 120, speed = 100 }

function crayon.init()
    crayon.window.setTitle("2D Game")
    crayon.window.setResolution(320, 240)
    crayon.window.setScalingMode("integer")
end

function crayon.update(dt)
    local dx, dy = 0, 0
    if crayon.key.isDown("a", "left") then dx = dx - 1 end
    if crayon.key.isDown("d", "right") then dx = dx + 1 end
    if crayon.key.isDown("w", "up") then dy = dy - 1 end
    if crayon.key.isDown("s", "down") then dy = dy + 1 end
    player.x = player.x + dx * player.speed * dt
    player.y = player.y + dy * player.speed * dt
end

function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)
    crayon.graphics.setColor(1, 0.8, 0.2)
    crayon.graphics.drawRect("fill", player.x - 8, player.y - 8, 16, 16)
    crayon.graphics.setColor(1, 1, 1)
    crayon.graphics.drawText("FPS: " .. math.floor(crayon.time.getFps()), 4, 4, 1)
end
```

### Example 2: 3D Scene with Physics

```lua
local cam = { yaw = 0, pitch = -20, dist = 10 }
local ground, ball

function crayon.init()
    crayon.window.setResolution(640, 360)
    crayon.graphics.setRetroEffects({
        jitterResolution = {320, 180},
        fog = { startDist = 10, endDist = 50, color = {0.1, 0.1, 0.15} },
        crt = { scanlines = 0.2, vignette = 0.15 }
    })

    ground = crayon.physics3D.createPlane(0, 0, 0)
    ball = crayon.physics3D.createSphere(0, 5, 0, 0.5)
end

function crayon.update(dt)
    crayon.physics3D.step(dt)
end

function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)

    local px, py, pz = ball:getPosition()
    crayon.graphics.setCamera3D(0, py + 4, 10, -20, 0, 60)
    crayon.graphics.setLight(0.5, -1, 0.3)

    crayon.graphics.setColor(0.3, 0.4, 0.5)
    crayon.graphics.drawPlane(0, 0, 0, 20, 20, 0)

    crayon.graphics.setColor(1, 0.3, 0.3)
    crayon.graphics.drawSphere(px, py, pz, 0.5, 0)
end
```

### Example 3: Raycast Picking

```lua
function crayon.update(dt)
    if crayon.mouse.isPressed(1) then
        local mx, my = crayon.mouse.getPosition()
        local ray = crayon.graphics.getCameraRay(mx, my)
        local o, d = ray.origin, ray.direction

        local hit, px, py, pz, nx, ny, nz, dist, body =
            crayon.physics3D.raycast(o.x, o.y, o.z, d.x, d.y, d.z, 1000)

        if hit then
            print("Hit at", px, py, pz, "distance:", dist)
        end
    end
end
```

### Example 4: Skeletal Animation

```lua
local model, animator, physics_skel, pose

function crayon.init()
    model = crayon.graphics.loadModel("character.glb")
    animator = model:createAnimator()
    animator:play("Idle", true)

    physics_skel = model:createPhysicsSkeleton()
    pose = crayon.physics3D.createSkeletonPose(physics_skel)
end

function crayon.update(dt)
    animator:update(dt)
    animator:applyToPhysicsPose(pose)
    pose:calculateMatrices()
end

function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)
    crayon.graphics.setCamera3D({ position = {0, 2, 5}, target = {0, 1, 0}, fov = 60 })
    crayon.graphics.drawModelSkinned(model, animator, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0)
end
```

### Example 5: Cloth Simulation

```lua
local cloth

function crayon.init()
    crayon.window.setResolution(640, 360)
    cloth = crayon.physics3D.createSoftBodyCloth({
        x = 0, y = 5, z = 0,
        width = 4, height = 4,
        segmentsX = 12, segmentsY = 12,
        compliance = 0.0,
        bendCompliance = 0.01,
        pinCorners = true
    })
end

function crayon.update(dt)
    crayon.physics3D.step(dt)
end

function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)
    crayon.graphics.setCamera3D({ position = {0, 4, 8}, target = {0, 3, 0}, fov = 60 })

    local verts = cloth:getVertices()
    local faces = cloth:getFaces()
    crayon.graphics.setColor(0.8, 0.3, 0.4)

    for _, f in ipairs(faces) do
        local p1, p2, p3 = verts[f[1]], verts[f[2]], verts[f[3]]
        crayon.graphics.drawTriangle3D(p1, p2, p3)
    end
end
```

### Example 6: Audio & Particles

```lua
local explosion_sfx, music
local fire

function crayon.init()
    explosion_sfx = crayon.audio.loadSound("explosion.wav")
    crayon.audio.playMusic("bgm.ogg", { loop = true, fadeIn = 2.0 })
    crayon.audio.setSfxVolume(0.8)

    fire = crayon.particles.createEmitter({
        maxParticles = 500,
        emissionRate = 80,
        lifetimeMin = 0.4, lifetimeMax = 1.0,
        sizeStart = 0.6, sizeEnd = 0.1,
        gravity = -2.0,
        blendMode = "additive",
        is3d = true
    })
    fire:setPosition(0, 1, 0)
end

function crayon.update(dt)
    fire:update(dt)
    if crayon.key.isPressed("space") then
        crayon.audio.playSound(explosion_sfx)
        fire:burst(100)
    end
end

function crayon.draw()
    crayon.graphics.clear(0.05, 0.05, 0.1)
    fire:draw3D()
end
```

### Example 7: Canvas & Shader

```lua
local canvas, shader

function crayon.init()
    crayon.window.setResolution(640, 360)
    canvas = crayon.graphics.createCanvas(320, 240)
    shader = crayon.graphics.loadShader([[
        #version 330 core
        layout(location=0) in vec3 aPos;
        layout(location=1) in vec2 aUV;
        out vec2 uv;
        uniform mat4 uProjection;
        uniform mat4 uView;
        void main() {
            uv = aUV;
            gl_Position = uProjection * uView * vec4(aPos, 1.0);
        }
    ]], [[
        #version 330 core
        in vec2 uv;
        out vec4 fragColor;
        void main() {
            fragColor = vec4(uv, 0.5, 1.0);
        }
    ]])
end

function crayon.draw()
    crayon.graphics.clear(0, 0, 0)
    canvas:renderTo(function()
        canvas:clear(0.2, 0.0, 0.4, 1.0)
        crayon.graphics.setColor(1, 1, 1)
        crayon.graphics.drawText("On Canvas", 10, 10, 2)
    end)
    crayon.graphics.drawSprite(canvas:getTexture(), 0, 0, 640, 480)
end
```

### Example 8: Post-Processing

```lua
function crayon.draw()
    crayon.graphics.clear(0.1, 0.1, 0.15)
    crayon.graphics.pushEffect("bloom2D", { intensity = 1.5, threshold = 0.8 })
    -- ... draw scene ...
    crayon.graphics.setEffectUniform("intensity", 2.0)
    crayon.graphics.popEffect()
end
```

---

## Migration Notes (from pre-camelCase API)

The following names have been **renamed**; update any existing scripts:

| Old | New |
|---|---|
| `crayon.physics3d` | `crayon.physics3D` |
| `crayon.physics2d` | `crayon.physics2D` |
| `t.modules.physics3d` / `t.modules.physics2d` | `t.modules.physics3D` / `t.modules.physics2D` |
| `setCamera3d` / `setCamera2d` / `resetCamera2d` / `newCamera2d` | `setCamera3D` / `setCamera2D` / `resetCamera2D` / `newCamera2D` |
| `pushMatrix2d` / `popMatrix2d` / `translate2d` / `rotate2d` / `scale2d` | `pushMatrix2D` / `popMatrix2D` / `translate2D` / `rotate2D` / `scale2D` |
| `drawLine3d` / `drawLines3d` / `drawGrid3d` / `drawTriangle3d` / `drawQuad3d` / `drawAxes3d` / `drawRay3d` | `drawLine3D` / `drawLines3D` / `drawGrid3D` / `drawTriangle3D` / `drawQuad3D` / `drawAxes3D` / `drawRay3D` |
| `drawSprite9slice` | `drawSprite9Slice` |
| `playSound3d` | `playSound3D` |
| `Particles.Emitter:draw3d()` | `Particles.Emitter:draw3D()` |
| `"bloom2d"` | `"bloom2D"` |

The following names have been **removed**:

- The entire `crayon.input` alias table — use `crayon.key`, `crayon.mouse`, `crayon.gamepad` directly.
- The `crayon.physics` alias stub — use `crayon.physics3D`.
- Event-callback aliases: `crayon.keypressed`, `crayon.keyreleased`, `crayon.mousepressed`, `crayon.mousereleased`, `crayon.gamepadpressed`, `crayon.gamepadreleased`, `crayon.resize`, `crayon.focus`, `crayon.collisionEnter`, `crayon.collisionExit`, `crayon.triggerEnter`, `crayon.triggerExit`, `crayon.collision2dEnter`, `crayon.collision2dExit`, `crayon.trigger2dEnter`, `crayon.trigger2dExit`, `crayon.dropbegin`, `crayon.dropenter`, `crayon.dropfile`, `crayon.filedropped`, `crayon.fileDropped`, `crayon.droptext`, `crayon.dropposition`, `crayon.dropmove`, `crayon.dropcomplete`, `crayon.dropleave`.
- `"linear_cast"` and `"ccd"` string values accepted by `Body:setMotionQuality` — use `"linearCast"` (or boolean `true`) only.

C++ identifiers, metatable registry keys (e.g. `"Physics3D.Body"`), file names, and internal helpers retain their original names and are not part of the Lua surface.