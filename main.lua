local ROT_DEGREES = false   -- true if your build expects degrees in drawModel(rx, ry, rz)
local ROT_SIGN    = 1       -- set to -1 if the rotor visually spins the opposite way to the physics

-- =========================================================================================
--  Theme  (identical colours to the original theme.td)
-- =========================================================================================
local function hex(s)
    s = s:gsub("#", "")
    return { tonumber(s:sub(1, 2), 16) / 255, tonumber(s:sub(3, 4), 16) / 255, tonumber(s:sub(5, 6), 16) / 255 }
end
local THEME = {
    green = hex("#26cb21"), red = hex("#ff2c2c"), black = hex("#1c1c1c"), white = hex("#ffffff"),
    bg = hex("#1c1c1c"), chip = hex("#ffe72c"), ball = hex("#feff2c"),
}

-- =========================================================================================
--  Constants shared with tools/generate_assets.py
-- =========================================================================================
local PI = math.pi
local SLOTS, SLOT = 37, 2 * PI / 37
local R_HUB, R_IN, R_OUT, R_BANK_OUT = 1.18, 1.20, 1.66, 2.42
local RC = (R_IN + R_OUT) / 2          -- pocket centre radius
local BALL_R = 0.065
local TABLE_Y = -0.5
local FELT_Y = TABLE_Y + 0.04
local LAY_X0, LAY_Z0 = 5.0, -2.5       -- top-left of the betting layout (the zero cell)
local STEP = 1 / 120                   -- fixed physics step
local A = "assets/"

local function bankY(r)
    local u = math.max(0, (r - R_OUT) / (R_BANK_OUT - R_OUT))
    return 0.62 * u ^ 2.4
end

-- =========================================================================================
--  Wheel layout (identical to wheel.td)
-- =========================================================================================
local WHEEL = {
    {0,"g"},{32,"r"},{15,"b"},{19,"r"},{4,"b"},{21,"r"},{2,"b"},{25,"r"},{17,"b"},{34,"r"},
    {6,"b"},{27,"r"},{13,"b"},{36,"r"},{11,"b"},{30,"r"},{8,"b"},{23,"r"},{10,"b"},{5,"r"},
    {24,"b"},{16,"r"},{33,"b"},{1,"r"},{20,"b"},{14,"r"},{31,"b"},{9,"r"},{22,"b"},{18,"r"},
    {29,"b"},{7,"r"},{28,"b"},{12,"r"},{35,"b"},{3,"r"},{26,"b"},
}
local COLOR_KEY = { g = "green", r = "red", b = "black" }
local COLOR_OF = {}
for _, s in ipairs(WHEEL) do COLOR_OF[s[1]] = COLOR_KEY[s[2]] end

-- =========================================================================================
--  Rules (port of rules.td - payouts are returned as total credit incl. the stake)
-- =========================================================================================
local COLUMNS = { {}, {}, {} }                       -- id 49 / 50 / 51  (top row first, as in the original)
for j = 1, 3 do for i = 0, 11 do COLUMNS[j][#COLUMNS[j] + 1] = 3 * (i + 1) - (j - 1) end end

local function inList(list, n) for _, v in ipairs(list) do if v == n then return true end end return false end

local function computePayout(totals, n)
    local color = COLOR_OF[n]
    local win = 0
    for id, amt in pairs(totals) do
        if id >= 0 and id <= 36 then
            if id == n then win = win + 36 * amt end
        elseif id >= 49 and id <= 51 then
            if inList(COLUMNS[id - 48], n) then win = win + 3 * amt end
        elseif id >= 40 and id <= 42 then
            local lo = (id - 40) * 12 + 1
            if n >= lo and n <= lo + 11 then win = win + 3 * amt end
        elseif id == 43 then if n >= 1 and n <= 18 then win = win + 2 * amt end
        elseif id == 48 then if n >= 19 and n <= 36 then win = win + 2 * amt end
        elseif id == 44 then if n > 0 and n % 2 == 0 then win = win + 2 * amt end
        elseif id == 47 then if n % 2 == 1 then win = win + 2 * amt end
        elseif id == 45 then if color == "red" then win = win + 2 * amt end
        elseif id == 46 then if color == "black" then win = win + 2 * amt end
        end
    end
    return win
end

-- =========================================================================================
--  Betting areas on the felt (ids identical to the original: 0, 1-36, 40-42, 43-48, 49-51)
-- =========================================================================================
local areas, areaById = {}, {}
local function addArea(id, gx, gy, gw, gh)
    local x0, z0 = LAY_X0 + gx, LAY_Z0 + gy
    local a = { id = id, x0 = x0, z0 = z0, x1 = x0 + gw, z1 = z0 + gh, cx = x0 + gw / 2, cz = z0 + gh / 2, w = gw, h = gh }
    areas[#areas + 1] = a; areaById[id] = a
end
addArea(0, 0, 0, 1, 3)
for i = 0, 11 do for j = 0, 2 do addArea(3 * (i + 1) - j, 1 + i, j, 1, 1) end end
for j = 0, 2 do addArea(49 + j, 13, j, 1, 1) end
for k = 0, 2 do addArea(40 + k, 1 + 4 * k, 3, 4, 1) end
for k = 0, 5 do addArea(43 + k, 1 + 2 * k, 4, 2, 1) end

-- =========================================================================================
--  Game state
-- =========================================================================================
local SCALES = { 10, 50, 100, 500, 1000, 5000, 10000, 50000, 1000000, 5000000, 10000000, 50000000 }
local G = { points = 25000, scaleIdx = 1, scale = 10, chips = {}, lastWon = 0 }
local history = {}
local lastPoints = G.points
local isGameOver = false
local showHistory = false
local comment = ""
local state = "bet"              -- "bet" | "spin" | "result"
local resultTimer = 0
local lastResult = nil           -- {number=, color=, index=}
local rng = math.random

local function floorN(n) return math.floor(n + 0.0) end

local function formatNum(n)
    n = floorN(n)
    if n < 1000 then return tostring(n)
    elseif n < 1000000 then return tostring(floorN(n / 1000)) .. "K"
    elseif n < 1000000000 then return tostring(floorN(n / 1000000)) .. "M"
    else return tostring(floorN(n / 1000000000)) .. "B" end
end
local function formatComma(n)
    local neg = n < 0
    local s = tostring(math.abs(floorN(n)))
    local out, c = "", 0
    for i = #s, 1, -1 do
        out = s:sub(i, i) .. out; c = c + 1
        if c == 3 and i ~= 1 then out = "," .. out; c = 0 end
    end
    return (neg and "-" or "") .. out
end

local function totalBet() local t = 0 for _, c in ipairs(G.chips) do t = t + c.amt end return t end
local function betTotals() local t = {} for _, c in ipairs(G.chips) do t[c.id] = (t[c.id] or 0) + c.amt end return t end

local function bestScaleFor(points)
    for i = #SCALES, 1, -1 do if SCALES[i] <= points then return i end end
    return nil
end

-- ------------------------------------------------------------------ persistence
local savePath
local function savefile()
    if savePath then return savePath end
    local ok, dir = pcall(function() return crayon.fs.getSaveDir("Ruretto3D", "Ruretto3D") end)
    if ok and dir then savePath = tostring(dir) .. "/ruretto3d.dat" end
    return savePath
end

local function saveGame()
    local p = savefile(); if not p then return end
    local lines = { "points=" .. floorN(G.points), "scale=" .. floorN(G.scale), "scaleIdx=" .. G.scaleIdx,
                    "lastWon=" .. floorN(G.lastWon), "gameover=" .. (isGameOver and 1 or 0) }
    for _, c in ipairs(G.chips) do lines[#lines + 1] = string.format("C\t%d\t%d\t%d", c.id, floorN(c.amt), c.den) end
    for _, h in ipairs(history) do
        lines[#lines + 1] = string.format("H\t%s\t%d\t%d\t%s\t%d\t%d\t%d", h.time, floorN(h.bet), h.number, h.color,
            floorN(h.won), floorN(h.change), floorN(h.balance))
    end
    pcall(function() crayon.fs.writeText(p, table.concat(lines, "\n")) end)
end

local function loadGame()
    local p = savefile(); if not p then return end
    local ok, txt = pcall(function() return crayon.fs.readText(p) end)
    if not ok or not txt then return end
    G.chips, history = {}, {}
    for line in txt:gmatch("[^\n]+") do
        local f = {}
        for part in line:gmatch("[^\t]+") do f[#f + 1] = part end
        if f[1] == "C" then
            G.chips[#G.chips + 1] = { id = tonumber(f[2]), amt = tonumber(f[3]), den = tonumber(f[4]) or 1 }
        elseif f[1] == "H" then
            history[#history + 1] = { time = f[2], bet = tonumber(f[3]), number = tonumber(f[4]), color = f[5],
                won = tonumber(f[6]), change = tonumber(f[7]), balance = tonumber(f[8]) }
        else
            local k, v = line:match("^(%w+)=(%-?%d+)$")
            if k == "points" then G.points = tonumber(v)
            elseif k == "scale" then G.scale = tonumber(v)
            elseif k == "scaleIdx" then G.scaleIdx = tonumber(v)
            elseif k == "lastWon" then G.lastWon = tonumber(v)
            elseif k == "gameover" then isGameOver = (tonumber(v) == 1) end
        end
    end
    if G.scaleIdx > 0 and SCALES[G.scaleIdx] and SCALES[G.scaleIdx] > G.points then
        G.scaleIdx = bestScaleFor(G.points) or 1; G.scale = SCALES[G.scaleIdx]
    end
    if G.points == 0 and totalBet() == 0 then isGameOver = true end
    lastPoints = G.points + totalBet()      -- chips already on the felt were taken from the balance
end

-- =========================================================================================
--  Assets / handles
-- =========================================================================================
local gfx, phys
local M, TX = {}, {}                -- models, textures
local chipTex = {}
local fonts = {}
local SND = {}
local confetti

local function loadAssets()
    local function model(name) return gfx.loadModel(A .. "models/" .. name .. ".obj") end
    local function tex(name) return gfx.loadTexture(A .. "textures/" .. name .. ".png") end
    for _, n in ipairs({ "table_body", "table_felt", "trim", "wheel_track", "rotor_pockets", "rotor_metal",
                         "ball", "chip", "marker", "floor" }) do M[n] = model(n) end
    M.trackPhysics = model("wheel_track_physics")
    for _, n in ipairs({ "wood", "gold", "trim", "ball", "carpet", "track", "felt_layout", "pockets" }) do TX[n] = tex(n) end
    for i, v in ipairs(SCALES) do chipTex[i] = tex("chip_" .. v) end
    fonts.s = gfx.loadFont("res/IBMPlexSans-Bold.ttf", 14)
    fonts.m = gfx.loadFont("res/IBMPlexSans-Bold.ttf", 20)
    fonts.l = gfx.loadFont("res/IBMPlexSans-Bold.ttf", 34)
    local function snd(name)
        local ok, id = pcall(function() return crayon.audio.loadSound(A .. "sfx/" .. name .. ".wav") end)
        return ok and id or nil
    end
    SND.tick, SND.chip, SND.launch, SND.win, SND.click, SND.wooh = snd("tick"), snd("chip"), snd("launch"), snd("win"), snd("click"), snd("wooh")
end

local function play(id, vol, pitch)
    if not id then return end
    pcall(function() crayon.audio.playSound(id, { volume = vol or 1, pitch = pitch or 1 }) end)
end

-- =========================================================================================
--  Physics world: static bowl + kinematic rotor + dynamic ball
-- =========================================================================================
local frets = {}
local floorBody, ball
local theta, W = 0.0, 0.35            -- rotor angle (rad) and angular speed (rad/s)
local IDLE_W = 0.35
local accum = 0.0
local debugPhysics = false
local lastTick = -1

local function syncRotor()
    for j = 0, SLOTS - 1 do
        local beta = (j - 0.5) * SLOT + theta
        local x, z = RC * math.cos(beta), -RC * math.sin(beta)
        local b = frets[j]
        b:setPosition(x, 0.05, z)
        b:setRotation(0, beta, 0)
        b:setVelocity(W * z, 0, -W * x)
        b:setAngularVelocity(0, W, 0)
    end
    floorBody:setAngularVelocity(0, W, 0)
end

local function buildPhysics()
    phys.setGravity(0, -20, 0)
    phys.createMeshBody(0, 0, 0, M.trackPhysics, 0.15, 0.35)                                   -- ball track (static)
    phys.createCylinder(0, 0.15, 0, 0.15, R_HUB, "static", 0.4, 0.3)                           -- hub / turret
    floorBody = phys.createCylinder(0, -0.05, 0, 0.05, R_OUT + 0.02, "kinematic", 0.9, 0.2)   -- rotating pocket floor
    for j = 0, SLOTS - 1 do
        local beta = (j - 0.5) * SLOT
        frets[j] = phys.createBox(RC * math.cos(beta), 0.05, -RC * math.sin(beta),
                                  (R_OUT - R_IN) / 2, 0.05, 0.02, "kinematic", 0.2, 0.45)
    end
    syncRotor()
end

-- ------------------------------------------------------------------ spin / ball logic
local spin = nil          -- active spin data
local cap = nil           -- capture animation
local restLocal = { phi = 0, r = RC, y = BALL_R }   -- where the ball sits in the rotor between rounds

local function wrapPi(a) while a > PI do a = a - 2 * PI end while a < -PI do a = a + 2 * PI end return a end

local function pocketAt(x, z)
    local phi = math.atan2(-z, x)
    local local_ = (phi - theta) % (2 * PI)
    return math.floor(local_ / SLOT + 0.5) % SLOTS
end

local function launchBall()
    if ball and ball:isValid() then ball:destroy() end
    local phi = rng() * 2 * PI
    local r = 2.28
    local x, z = r * math.cos(phi), -r * math.sin(phi)
    ball = phys.createSphere(x, bankY(r) + 0.14, z, BALL_R, "dynamic", 0.2, 0.5, 1.0)
    ball:setMotionQuality(true)
    ball:setDamping(0.16, 0.05)
    local spd = 6.2 + rng() * 1.6
    ball:setVelocity(spd * math.sin(phi), 0, spd * math.cos(phi))      -- clockwise, opposite to the rotor
end

local function startCapture(idx, x, y, z)
    if ball and ball:isValid() then ball:destroy() end
    ball = nil
    local phi0 = math.atan2(-z, x) - theta
    local r0 = math.min(math.sqrt(x * x + z * z), R_OUT)
    cap = { t = 0, dur = 0.55, phi0 = phi0, r0 = r0, y0 = math.max(y, BALL_R), idx = idx,
            diff = wrapPi(idx * SLOT - phi0) }
end

local function ballWorldFromLocal(phi, r, y)
    local a = phi + theta
    return r * math.cos(a), y, -r * math.sin(a)
end

local function beginSpin()
    spin = { t = 0, inRotor = 0, tries = 0 }
    cap = nil
    state = "spin"
    W = 2.3
    launchBall()
    play(SND.launch, 0.8)
end

local function stepSpin(h)
    spin.t = spin.t + h
    -- rotor slows down while the ball is in play
    local target = 0.6 + 1.7 * math.exp(-spin.t / 9)
    W = W + (target - W) * math.min(1, h * 1.5)
    if not ball then return end
    local x, y, z = ball:getPosition()
    local vx, vy, vz = ball:getVelocity()
    local r = math.sqrt(x * x + z * z)

    if spin.t > 9 and not spin.dragged then spin.dragged = true; ball:setDamping(0.5, 0.2) end   -- make sure it eventually drops

    -- fell out of the world -> relaunch once, then give up
    if y < -1.5 or r > 3.4 then
        spin.tries = spin.tries + 1
        if spin.tries <= 2 then launchBall() else startCapture(rng(0, SLOTS - 1), 0, 0.3, RC) end
        return
    end

    if r < R_OUT and y < 0.2 then
        spin.inRotor = spin.inRotor + h
        local rx, ry, rz = vx - W * z, vy, vz + W * x         -- velocity relative to the rotating floor
        local rel = math.sqrt(rx * rx + ry * ry + rz * rz)
        if (rel < 0.45 and spin.inRotor > 0.45) or spin.inRotor > 6 then
            startCapture(pocketAt(x, z), x, y, z)
        end
    end
    if spin.t > 28 and not cap then startCapture(pocketAt(x, z), x, y, z) end
end

-- =========================================================================================
--  Round resolution
-- =========================================================================================
local function addHistory(bet, luck, won, change)
    local t = "-"
    pcall(function() t = os.date("%d %b %y %H:%M") end)
    history[#history + 1] = { time = t, bet = bet, number = luck.number, color = luck.color, won = won, change = change, balance = G.points }
    if #history > 100 then table.remove(history, 1) end
end

local function resolveRound(idx)
    local slot = WHEEL[idx + 1]
    local luck = { number = slot[1], color = COLOR_KEY[slot[2]], index = idx }
    local betBefore = totalBet()
    local totals = betTotals()
    local pointsBefore = G.points
    G.points = G.points + computePayout(totals, luck.number)
    G.lastWon = G.points - lastPoints
    local change = G.points - pointsBefore
    local won = (change > 0) and change or -betBefore
    addHistory(betBefore, luck, won, change)
    if G.lastWon < 0 then
        if SND.wooh then play(SND.wooh, 1) end
    elseif G.lastWon > 0 then
        play(SND.win, 1)
        if confetti then pcall(function() local x, y, z = ballWorldFromLocal(luck.index * SLOT, RC, 0.3); confetti:setPosition(x, y, z); confetti:burst(80) end) end
    end
    lastPoints = G.points
    G.chips = {}
    lastResult = luck
    restLocal = { phi = idx * SLOT, r = RC, y = BALL_R }
    if G.points == 0 then comment = "Woooh! You lost all of your chips, didn't you?"; isGameOver = true
    elseif G.points >= 1000000000 then comment = "Damn! You've become a billionaire!"
    else comment = "" end
    state = "result"; resultTimer = 3.2
    saveGame()
end

-- =========================================================================================
--  Betting actions (ports of the original button handlers)
-- =========================================================================================
local function refreshScale()
    if G.scaleIdx > 0 and SCALES[G.scaleIdx] and SCALES[G.scaleIdx] > G.points then
        local i = bestScaleFor(G.points)
        if i then G.scaleIdx = i; G.scale = SCALES[i] end
    end
end

local function denFor(amount) return bestScaleFor(amount) or 1 end

local function placeBet(id)
    if G.points <= 0 then return end
    local den = (G.scaleIdx > 0) and G.scaleIdx or denFor(G.scale)
    if G.points >= G.scale then
        G.points = G.points - G.scale
        G.chips[#G.chips + 1] = { id = id, amt = G.scale, den = den }
    else
        G.chips[#G.chips + 1] = { id = id, amt = G.points, den = denFor(G.points) }
        G.points = 0
    end
    refreshScale()
    play(SND.chip, 0.8, 0.9 + rng() * 0.2)
end

local function clearBets()
    for _, c in ipairs(G.chips) do G.points = G.points + c.amt end
    G.chips = {}
    play(SND.click, 0.7)
end

local function doubleBets()
    for _, c in ipairs(G.chips) do
        if G.points >= c.amt then G.points = G.points - c.amt; c.amt = c.amt * 2 else break end
    end
    refreshScale()
    play(SND.click, 0.7)
end

local function allIn() G.scale = G.points; G.scaleIdx = 0; play(SND.click, 0.7) end

local function newGame()
    G.points, G.scale, G.scaleIdx, G.lastWon, G.chips = 25000, 10, 1, 0, {}
    isGameOver = false; comment = ""; lastPoints = G.points; lastResult = nil
    saveGame()
end

local camMode = "table"
local function trySpin()
    if state ~= "bet" or isGameOver then return end
    beginSpin(); camMode = "wheel"
end

local function selectChip(i)
    if i >= 1 and i <= #SCALES and G.points >= SCALES[i] then G.scaleIdx = i; G.scale = SCALES[i]; play(SND.click, 0.6) end
end

-- =========================================================================================
--  Camera
-- =========================================================================================
local CAMS = {
    table = { px = 8.2, py = 16.0, pz = 9.5, tx = 8.2, ty = -0.5, tz = -0.2, fov = 42 },
    wheel = { px = 0.0, py = 7.2, pz = 6.4, tx = 0.0, ty = 0.2, tz = 0.0, fov = 48 },
}
local cam = {}
for k, v in pairs(CAMS.table) do cam[k] = v end
local function updateCamera(dt)
    local c = CAMS[camMode]
    for k, v in pairs(c) do cam[k] = crayon.math.damp(cam[k], v, 3.2, dt) end
end

-- =========================================================================================
--  Picking: ray -> felt plane -> betting area
-- =========================================================================================
-- getCameraRay historically returned either {origin={x,y,z}, direction={x,y,z}} with named fields
-- or plain positional tables {x,y,z} indexed [1],[2],[3] (or userdata vectors with :x()/:y()/:z()).
-- These helpers normalise the components so pickArea never indexes a nil field.
local function vecComp(v, name, idx)
    if v == nil then return nil end
    local t = type(v)
    if t == "table" then
        local c = v[name]
        if c == nil then c = v[idx] end
        return c
    end
    -- userdata / vector object: try method form, then field form
    local ok, c = pcall(function() return v[name]() end)
    if ok and c ~= nil then return c end
    ok, c = pcall(function() return v[name] end)
    if ok and c ~= nil then return c end
    return nil
end

local hover = nil
local function pickArea(mx, my)
    local ray = gfx.getCameraRay(mx, my)
    if not ray then return nil end
    local o = ray.origin or ray[1]
    local d = ray.direction or ray.dir or ray[2]
    if not o or not d then return nil end

    local ox, oy, oz = vecComp(o, "x", 1), vecComp(o, "y", 2), vecComp(o, "z", 3)
    local dx, dy, dz = vecComp(d, "x", 1), vecComp(d, "y", 2), vecComp(d, "z", 3)
    if not (ox and oy and oz and dx and dy and dz) then return nil end
    if math.abs(dy) < 1e-6 then return nil end

    local t = (FELT_Y - oy) / dy
    if t < 0 then return nil end
    local x, z = ox + dx * t, oz + dz * t
    for _, a in ipairs(areas) do
        if x >= a.x0 and x < a.x1 and z >= a.z0 and z < a.z1 then return a end
    end
    return nil
end

-- =========================================================================================
--  UI (2D overlay) - bounds are rebuilt every frame, like the original
-- =========================================================================================
local UI = {}
local VW, VH = 1280, 720
local retro = false

-- touch / Android support
local platform = "?"
local isTouch = false               -- device reports touch support
local lastTouchTime = -10           -- used to ignore the mouse events SDL synthesises from touches
local touchStart = {}               -- id -> {x, y} where each finger went down
local pendingTap = nil              -- completed tap, consumed in update()
local function barTop() return isTouch and 570 or 596 end

local function setCol(c, a) gfx.setColor(c[1], c[2], c[3], a or 1) end
local function txt(str, x, y, font, a, col)
    gfx.setFont(font or fonts.m); setCol(col or THEME.white, a or 1); gfx.drawText(str, x, y, 1)
end
local function txtC(str, cx, cy, font, a, col)
    gfx.setFont(font or fonts.m)
    local w, h = gfx.getTextWidth(str, 1), gfx.getTextHeight(str, 1)
    setCol(col or THEME.white, a or 1); gfx.drawText(str, cx - w / 2, cy - h / 2, 1)
end
local function addBound(x, y, w, h, id) UI[#UI + 1] = { x = x, y = y, w = w, h = h, id = id } end

local function drawChip2D(cx, cy, r, label)
    for k = 0, 9 do
        local a0, a1 = 2 * PI * k / 10, 2 * PI * (k + 1) / 10
        local pts = { cx, cy }
        for s = 0, 4 do local a = a0 + (a1 - a0) * s / 4; pts[#pts + 1] = cx + r * math.cos(a); pts[#pts + 1] = cy + r * math.sin(a) end
        setCol(k % 2 == 0 and THEME.white or THEME.chip); gfx.drawPolygon("fill", pts)
    end
    setCol(THEME.chip); gfx.drawCircle("fill", cx, cy, r * 0.78, 24)
    gfx.setColor(0, 0, 0, 0.25); gfx.drawCircle("fill", cx, cy, r * 0.78, 24)
    txtC(label, cx, cy, fonts.s, 0.73, { 0, 0, 0 })
end

local function drawHistoryPanel()
    local pw, ph = VW * 0.8, VH * 0.7
    local px, py = (VW - pw) / 2, (VH - ph) / 2
    gfx.setColor(0.07, 0.07, 0.07, 0.97); gfx.drawRect("fill", px, py, pw, ph)
    txtC("Game History", px + pw / 2, py + 22, fonts.m)
    setCol(THEME.red); gfx.drawCircle("line", px + pw - 22, py + 22, 11, 20)
    txtC("x", px + pw - 22, py + 21, fonts.s, 1, THEME.red)
    addBound(px + pw - 56, py + 2, 52, 52, "closeHistory")
    local heads = { "Time", "Bet", "Result", "Won", "Balance" }
    local colW = pw / #heads
    local rowH = 26
    for i, h in ipairs(heads) do txt(h, px + (i - 1) * colW + 14, py + 50, fonts.s, 0.55) end
    gfx.setColor(1, 1, 1, 0.25); gfx.drawLine(px, py + 76, px + pw, py + 76, 1)
    local maxRows = math.floor((ph - 120) / rowH)
    for i = 0, math.min(#history, maxRows) - 1 do
        local e = history[#history - i]
        local y = py + 82 + i * rowH
        if i % 2 == 0 then gfx.setColor(1, 1, 1, 0.06); gfx.drawRect("fill", px, y, pw, rowH) end
        local wonStr, wonCol = "$0", { 1, 1, 1 }
        if e.won > 0 then wonStr, wonCol = "+$" .. formatNum(e.won), THEME.green
        elseif e.won < 0 then wonStr, wonCol = "-$" .. formatNum(math.abs(e.won)), THEME.red end
        local balStr, balCol = "$0", { 1, 1, 1 }
        if e.change > 0 then balStr, balCol = "+$" .. formatNum(e.change), THEME.green
        elseif e.change < 0 then balStr, balCol = "-$" .. formatNum(math.abs(e.change)), THEME.red end
        local cols = { e.time, "$" .. formatNum(e.bet), e.number .. " " .. (e.color == "red" and "R" or (e.color == "black" and "B" or "G")), wonStr, balStr }
        for j, c in ipairs(cols) do
            local col = (j == 4) and wonCol or ((j == 5) and balCol or { 1, 1, 1 })
            txt(c, px + (j - 1) * colW + 14, y + 4, fonts.s, (j >= 4) and 1 or 0.6, col)
        end
    end
    if #history == 0 then txtC("No games played yet", px + pw / 2, py + ph / 2, fonts.m, 0.4) end
    if #history > 0 then
        local tw, tl, wins, games = 0, 0, 0, 0
        for _, e in ipairs(history) do
            if e.won > 0 then tw = tw + e.won; wins = wins + 1; games = games + 1
            elseif e.won < 0 then tl = tl + math.abs(e.won); games = games + 1 end
        end
        local rate = games > 0 and (wins / games * 100) or 0
        txtC(string.format("Games: %d | Wins: %d (%.0f%%) | Profit: $%s", games, wins, rate, formatComma(tw - tl)),
             px + pw / 2, py + ph - 16, fonts.s, 0.55)
    end
end

local function drawUI()
    UI = {}
    gfx.setBlendMode("alpha")
    -- top bar: balance, current bet, last result (same info as the original header)
    local bal = string.format("$%s   $%s", formatComma(G.points), formatComma(totalBet()))
    txt(bal, 16, 14, fonts.m)
    local bw = gfx.getTextWidth(bal, 1)
    local lw, lc = "$" .. formatComma(G.lastWon), THEME.white
    if G.lastWon > 0 then lw, lc = "+$" .. formatComma(G.lastWon), THEME.green
    elseif G.lastWon < 0 then lw, lc = "-$" .. formatComma(math.abs(G.lastWon)), THEME.red end
    txt(lw, 36 + bw, 14, fonts.m, 1, lc)

    -- history button + camera button (big enough for fingers)
    setCol(THEME.white); gfx.drawCircle("line", VW - 36, 36, 16, 24)
    gfx.drawLine(VW - 36, 36, VW - 36, 27, 1.5); gfx.drawLine(VW - 36, 36, VW - 29, 40, 1.5)
    addBound(VW - 64, 8, 56, 56, "history")
    gfx.setColor(1, 1, 1, 0.5); gfx.drawRect("line", VW - 154, 16, 80, 40, 1.5)
    txtC("VIEW", VW - 114, 36, fonts.s, 0.8)
    addBound(VW - 160, 8, 92, 56, "view")

    -- result badge (the "previous bet" circle of the original)
    if lastResult and state ~= "spin" then
        local col = THEME[lastResult.color]
        local fill = (lastResult.color == "black") and { 0.2, 0.2, 0.2 } or col
        setCol(fill); gfx.drawCircle("fill", VW / 2, 52, 30, 32)
        setCol(THEME.white, 0.35); gfx.drawCircle("line", VW / 2, 52, 30, 32)
        local tc = (lastResult.color == "red") and THEME.black or ((lastResult.color == "black") and THEME.red or THEME.black)
        txtC(tostring(lastResult.number), VW / 2, 52, fonts.l, 1, tc)
    end
    if comment ~= "" then txtC(comment, VW / 2, 108, fonts.m) end
    if state == "spin" then txtC("No more bets!", VW / 2, 52, fonts.l, 0.9) end

    -- bottom bar
    local top = barTop()
    local rowY = isTouch and 632 or 640                       -- chip row centre
    local btnY, btnH = isTouch and 598 or 616, isTouch and 68 or 48
    gfx.setColor(0, 0, 0, 0.6); gfx.drawRect("fill", 0, top, VW, VH - top)
    if not isGameOver then
        for i, v in ipairs(SCALES) do
            if G.points >= v then
                local cx, cy = 46 + (i - 1) * 56, rowY
                if i == G.scaleIdx then gfx.setColor(1, 1, 1, 0.3); gfx.drawCircle("fill", cx, cy, 26, 24) end
                drawChip2D(cx, cy, 22, formatNum(v))
                addBound(cx - 28, cy - 32, 56, 64, "chip" .. i)
            end
        end
        local labels = { "CLEAR", "DOUBLE", "ALL", "SPIN" }
        for i, lb in ipairs(labels) do
            local x, y, w, h = 770 + (i - 1) * 122, btnY, 112, btnH
            local active = (state == "bet")
            local a = active and 0.5 or 0.2
            if lb == "ALL" and G.scaleIdx == 0 then setCol(THEME.red, 1) else gfx.setColor(1, 1, 1, a) end
            gfx.drawRect("line", x, y, w, h, 1.5)
            txtC(lb, x + w / 2, y + h / 2, fonts.m, active and 0.9 or 0.35)
            if active then addBound(x, y, w, h, "btn" .. i) end
        end
    else
        gfx.setColor(1, 1, 1, 1); gfx.drawRect("fill", 520, btnY, 240, btnH)
        txtC("Play Again?", 640, btnY + btnH / 2, fonts.m, 1, THEME.black)
        addBound(520, btnY, 240, btnH, "again")
    end
    if isTouch then
        txt("Tap the felt to place a chip", 16, 692, fonts.s, 0.4)
    else
        txt("SPACE spin | C clear | D double | A all | V camera | H history | TAB debug | F2 CRT", 16, 690, fonts.s, 0.35)
    end

    -- debug-view banner (shown on top of the UI when TAB has toggled debug on)
    if debugPhysics then
        local msg = "DEBUG VIEW  -  press TAB to return to game"
        gfx.setFont(fonts.m)
        local w = gfx.getTextWidth(msg, 1)
        gfx.setColor(0, 0, 0, 0.7); gfx.drawRoundedRect("fill", VW / 2 - w / 2 - 14, VH - 46, w + 28, 32, 8)
        txtC(msg, VW / 2, VH - 30, fonts.m, 1, { 1, 0.85, 0.3 })
    end

    -- bet amounts floating above the chip stacks (projected from 3D).
    -- In debug view the game meshes aren't drawn, so skip these to avoid ghosts.
    if not debugPhysics then
        local totals = betTotals()
        for id, amt in pairs(totals) do
            local a = areaById[id]
            local count = 0
            for _, c in ipairs(G.chips) do if c.id == id then count = count + 1 end end
            local sx, sy, vis = gfx.project(a.cx, FELT_Y + 0.07 * math.min(count, 8) + 0.35, a.cz)
            if vis ~= false then
                local s = formatNum(amt)
                gfx.setFont(fonts.s)
                local w = gfx.getTextWidth(s, 1)
                gfx.setColor(0, 0, 0, 0.7); gfx.drawRoundedRect("fill", sx - w / 2 - 5, sy - 10, w + 10, 20, 6)
                txtC(s, sx, sy, fonts.s, 1, THEME.chip)
            end
        end
    end
    if showHistory then drawHistoryPanel() end
end

-- =========================================================================================
--  Rendering
-- =========================================================================================
local function rotAngle(a) return ROT_SIGN * (ROT_DEGREES and math.deg(a) or a) end

local function draw3D(dt)
    gfx.setCamera3D({ position = { cam.px, cam.py, cam.pz }, target = { cam.tx, cam.ty, cam.tz }, up = { 0, 1, 0 },
                      fov = cam.fov, near = 0.1, far = 200 })

    -- Debug view: skip all game rendering, only draw the physics wireframes.
    -- (The 2D UI is still drawn afterwards by drawUI - see crayon.draw.)
    if debugPhysics then
        gfx.setShadingMode("unlit")
        gfx.setColor(1, 1, 1, 1)
        phys.drawDebug()
        return
    end

    gfx.setShadingMode("gouraud")
    gfx.setLight(0.35, -1, -0.45, 0.85, 0.82, 0.78, 0.5, 0.48, 0.48)
    gfx.setPointLight(0, 0, 6.5, 0, 1.0, 0.85, 0.7, 14, 1.2)
    gfx.setPointLight(1, 12.5, 7.5, 0, 1.0, 0.9, 0.85, 22, 1.0)
    gfx.setPointLightEnabled(0, true); gfx.setPointLightEnabled(1, true)
    gfx.setCullFace(false)
    gfx.setColor(1, 1, 1, 1)

    gfx.drawModel(M.floor, 0, 0, 0, 0, 0, 0, 1, 1, 1, TX.carpet)
    gfx.drawModel(M.table_body, 0, 0, 0, 0, 0, 0, 1, 1, 1, TX.wood)
    gfx.drawModel(M.table_felt, 0, 0, 0, 0, 0, 0, 1, 1, 1, TX.felt_layout)
    gfx.drawModel(M.trim, 0, 0, 0, 0, 0, 0, 1, 1, 1, TX.trim)
    gfx.drawModel(M.wheel_track, 0, 0, 0, 0, 0, 0, 1, 1, 1, TX.track)

    -- rotating part of the wheel
    local ry = rotAngle(theta)
    gfx.drawModel(M.rotor_pockets, 0, 0, 0, 0, ry, 0, 1, 1, 1, TX.pockets)
    gfx.drawModel(M.rotor_metal, 0, 0, 0, 0, ry, 0, 1, 1, 1, TX.gold)

    -- ball
    local bx, by, bz
    if ball and ball:isValid() then
        bx, by, bz = ball:getPosition()
    elseif cap then
        local e = math.min(1, cap.t / cap.dur); e = e * e * (3 - 2 * e)
        local phi = cap.phi0 + cap.diff * e
        local r = cap.r0 + (RC - cap.r0) * e
        local y = cap.y0 + (BALL_R - cap.y0) * e + 0.12 * math.sin(PI * e) * (1 - e)
        bx, by, bz = ballWorldFromLocal(phi, r, y)
    else
        bx, by, bz = ballWorldFromLocal(restLocal.phi, restLocal.r, restLocal.y)
    end
    gfx.drawModel(M.ball, bx, by, bz, 0, 0, 0, BALL_R, BALL_R, BALL_R, TX.ball)

    -- chips on the felt
    local stacks = {}
    for _, c in ipairs(G.chips) do
        local s = stacks[c.id]; if not s then s = {}; stacks[c.id] = s end
        s[#s + 1] = c.den
    end
    for id, list in pairs(stacks) do
        local a = areaById[id]
        local first = math.max(1, #list - 7)
        for k = first, #list do
            gfx.drawModel(M.chip, a.cx, FELT_Y + (k - first) * 0.07, a.cz, 0, 0, 0, 1, 1, 1, chipTex[list[k]])
        end
    end

    -- hover + winning highlight
    gfx.setBlendMode("alpha")
    if hover and state == "bet" and not showHistory then
        gfx.setColor(1, 1, 1, 0.2)
        gfx.drawPlane(hover.cx, FELT_Y + 0.012, hover.cz, hover.w - 0.04, hover.h - 0.04, 0, 0, 0, 0)
    end
    if lastResult and state ~= "spin" then
        local a = areaById[lastResult.number]
        local pulse = 0.3 + 0.2 * math.sin(crayon.time.getTime() * 4)
        gfx.setColor(THEME.ball[1], THEME.ball[2], THEME.ball[3], pulse)
        gfx.drawPlane(a.cx, FELT_Y + 0.014, a.cz, a.w - 0.04, a.h - 0.04, 0, 0, 0, 0)
        gfx.setColor(1, 1, 1, 1)
        gfx.drawModel(M.marker, a.cx, FELT_Y + 0.02 + 0.06 * math.abs(math.sin(crayon.time.getTime() * 3)), a.cz, 0, 0, 0, 1, 1, 1, TX.ball)
    end
    gfx.setColor(1, 1, 1, 1)
    if confetti then pcall(function() confetti:update(dt); confetti:draw3D() end) end
end

-- =========================================================================================
--  Crayon callbacks
-- =========================================================================================
function crayon.config(t)
    t.identity = "Ruretto3D"
    t.version = "1.0.0"
    t.fpsLimit = 60
    t.window = { title = "Rūretto 3D", width = 640, height = 360, virtualWidth = VW, virtualHeight = VH,
                 minWidth = 640, minHeight = 360, resizable = true, vsync = true, scaling = "aspect" }
    t.modules = { physics3D = true, physics2D = false, physics4D = false, audio = true, mesh3D = true,
                  particles = true, input = true, fs = true }
    t.graphics = { clearColor = { THEME.bg[1], THEME.bg[2], THEME.bg[3], 1 } }
end

local function applyRetro(on)
    if on then
        gfx.setRetroEffects({ jitterResolution = { 640, 360 }, dither = true, colorDepth = 32, ditherLevels = 48,
                              crt = { scanlines = 0.18, curvature = 0.04, vignette = 0.25 } })
    else
        gfx.setRetroEffects({ jitterResolution = false, affine = 0, dither = false, colorDepth = 32,
                              crt = { scanlines = 0, curvature = 0, vignette = 0.12 } })
    end
end

function crayon.init()
    gfx, phys = crayon.graphics, crayon.physics3D
    math.randomseed(os.time()); rng(); rng()
    crayon.window.setTitle("Rūretto 3D")
    pcall(function() platform = crayon.window.getPlatform() end)
    pcall(function() isTouch = crayon.touch.isAvailable() and true or false end)
    print("platform:", platform, "touch:", isTouch)
    loadAssets()
    buildPhysics()
    loadGame()
    applyRetro(false)
    local ok, em = pcall(function()
        return crayon.particles.createEmitter({ maxParticles = 300, emissionRate = 0, lifetimeMin = 0.6, lifetimeMax = 1.6,
            sizeStart = 0.18, sizeEnd = 0.0, gravity = -6, blendMode = "additive", is3d = true })
    end)
    if ok then confetti = em end
end

local function handleUIClick(id)
    if id == "history" then showHistory = not showHistory; return end
    if id == "view" then camMode = (camMode == "table") and "wheel" or "table"; return end
    if id == "closeHistory" then showHistory = false; return end
    if showHistory then return end
    if id == "again" then newGame(); return end
    if state ~= "bet" then return end
    if id:sub(1, 4) == "chip" then selectChip(tonumber(id:sub(5)))
    elseif id == "btn1" then clearBets()
    elseif id == "btn2" then doubleBets()
    elseif id == "btn3" then allIn()
    elseif id == "btn4" then trySpin() end
end

function crayon.update(dt)
    dt = math.min(dt, 0.05)

    -- ---- fixed-step physics + rotor
    accum = accum + dt
    local n = 0
    while accum >= STEP and n < 6 do
        accum = accum - STEP; n = n + 1
        if state ~= "spin" then W = W + (IDLE_W - W) * math.min(1, STEP * 1.2) end
        theta = (theta + W * STEP) % (2 * PI)
        syncRotor()
        if state == "spin" and not cap then stepSpin(STEP) end
        phys.step(STEP)
    end

    -- ---- capture animation
    if cap then
        cap.t = cap.t + dt
        if cap.t >= cap.dur then
            local idx = cap.idx; cap = nil; spin = nil
            resolveRound(idx)
        end
    end
    if state == "result" then
        resultTimer = resultTimer - dt
        if resultTimer <= 0 then state = "bet"; camMode = "table" end
    end

    updateCamera(dt)

    -- ---- input (mouse and touch share one code path)
    local now = crayon.time.getTime()
    local mx, my = crayon.mouse.getPosition()
    local touching = false
    if isTouch then
        local ok, ts = pcall(function() return crayon.touch.getTouches() end)
        if ok and ts and ts[1] then mx, my = ts[1].x, ts[1].y; touching = true end
    end
    local recentTouch = (now - lastTouchTime) < 2.0
    if recentTouch and not touching then mx, my = -1000, -1000 end   -- no hover when the finger is up

    -- Felt hover uses a raycast against the felt plane; it is meaningless in debug view
    -- because we're not rendering the felt, so we only compute it in game mode.
    hover = nil
    if not debugPhysics then
        local overUI = (my >= barTop())
        for _, b in ipairs(UI) do
            if mx >= b.x and mx < b.x + b.w and my >= b.y and my < b.y + b.h then overUI = true end
        end
        if state == "bet" and not isGameOver and not showHistory and not overUI then hover = pickArea(mx, my) end
    end

    local function pressAt(x, y)
        -- UI buttons (chips / CLEAR / SPIN / VIEW / history ...) always work, in both modes.
        for i = #UI, 1, -1 do
            local b = UI[i]
            if x >= b.x and x < b.x + b.w and y >= b.y and y < b.y + b.h then handleUIClick(b.id); return end
        end
        -- Felt picking only makes sense while the felt is visible.
        if debugPhysics then return end
        if showHistory or y >= barTop() or state ~= "bet" or isGameOver then return end
        local a = pickArea(x, y)
        if a then placeBet(a.id); saveGame() end
    end

    if pendingTap then local t = pendingTap; pendingTap = nil; pressAt(t.x, t.y) end
    if crayon.mouse.isPressed(1) and not recentTouch then pressAt(mx, my) end

    local k = crayon.key
    if k.isPressed("h") then showHistory = not showHistory end
    if not showHistory then
        if k.isPressed("space", "enter") then trySpin() end
        if state == "bet" and not isGameOver then
            if k.isPressed("c") then clearBets() end
            if k.isPressed("d") then doubleBets() end
            if k.isPressed("a") then allIn() end
            if k.isPressed("right") then selectChip(math.min(#SCALES, (G.scaleIdx > 0 and G.scaleIdx or 1) + 1)) end
            if k.isPressed("left") then selectChip(math.max(1, (G.scaleIdx > 0 and G.scaleIdx or 1) - 1)) end
        end
    end
    if k.isPressed("v") then camMode = (camMode == "table") and "wheel" or "table" end
    -- TAB (and F1) toggle between game mode and physics debug view
    if k.isPressed("tab", "f1") then debugPhysics = not debugPhysics end
    if k.isPressed("f2") then retro = not retro; applyRetro(retro) end
    if k.isPressed("escape") then            -- Android Back button arrives as "escape"
        if debugPhysics then debugPhysics = false
        elseif showHistory then showHistory = false
        elseif camMode == "wheel" and state ~= "spin" then camMode = "table"
        elseif tostring(platform):lower():find("android") then saveGame(); crayon.window.quit() end
    end
end

function crayon.draw()
    gfx.clear(THEME.bg[1], THEME.bg[2], THEME.bg[3])
    draw3D(crayon.time.getDt())
    gfx.setDepthTest(false)
    drawUI()
    gfx.setDepthTest(true)
end

-- ball hits something: play a click scaled by the impact
function crayon.onCollisionEnter(a, b, nx, ny, nz, impulse)
    if not ball or not ball:isValid() then return end
    local id = ball:getId()
    if a ~= id and b ~= id then return end
    local now = crayon.time.getTime()
    if now - lastTick < 0.04 then return end
    lastTick = now
    local v = math.max(0.15, math.min(1, (impulse or 0.5) * 0.6))
    play(SND.tick, v, 0.9 + rng() * 0.3)
end

-- a tap = finger goes down and comes up without moving far; the bet is placed on release
function crayon.touchdown(id, x, y)
    isTouch = true
    lastTouchTime = crayon.time.getTime()
    touchStart[id] = { x = x, y = y }
end

function crayon.touchup(id, x, y)
    lastTouchTime = crayon.time.getTime()
    local st = touchStart[id]; touchStart[id] = nil
    if st and (x - st.x) ^ 2 + (y - st.y) ^ 2 < 40 * 40 then pendingTap = { x = x, y = y } end
end

function crayon.quit() saveGame() end