-- ============================================================================
-- air_strike_2.lua — Kinetic Strike (Aircraft Thermal / Heatmap Edition)
-- ============================================================================

local ROT_IN_DEGREES = true    -- body:getRotation() returns degrees here; draw calls need radians

local cam = { x = 0, y = 62, z = 34, yaw = -90, pitch = -62, fov = 55, shake = 0 }

local models, tex_white = {}, nil
local tex_smoke, tex_glow = nil, nil
local bodies, info_by_id = {}, {}        -- drawable bodies / id lookup
local projectiles, tracers, fx, explosions = {}, {}, {}, {}
local enemies, parts = {}, {}
local proj_by_id = {}
local score, wave, wave_timer, banner, banner_t = 0, 0, 1.0, "", 0
local time_scale, flash_alpha, flash_color = 1.0, 0.0, { 1, 1, 1 }
local fx_mode, debug_draw = 2, false     -- default to full FX mode for thermal processing
local light_t = 0
local pov, saved_view = 1, { y = 62, pitch = -62, fov = 55 }
local mcam = { x = 0, y = 0, z = 0, dx = 0, dy = 0, dz = 1, hold = 0 }
local scorch, scorch_i, frame = {}, 0, 0
local ENEMY_YAW = math.pi
local POV_NAMES = { "BOMBER", "GROUND", "MISSILE" }
local SPHERE_H = { 0.45, 1.0, 1.55 }
local cam_tbl = { position = { 0, 0, 0 }, target = { 0, 0, 0 }, fov = 55, far = 400 }

local MAX_FX = 120
local MAX_ENEMIES_BASE, MAX_ENEMIES_CAP = 5, 9
local HX, HZ = 70, 50                    -- half-size of the map
local ZONE_X, ZONE_Z = 62, 36            -- where enemies may walk

local glitch = { intensity = 0, next_spike = 5, whisper = "", whisper_t = 0, t = 0 }
local WHISPERS = { "TARGET ACQUIRED", "FLIR_HOT", "LOCK ESTABLISHED", "THERMAL FEED ACTIVE" }
local hud = { tc = 0, blink = 0, burst = 0, bands = {} }

-- ---------------------------------------------------------------------------
-- Plane definition
-- ---------------------------------------------------------------------------
local PLANE_S = 5.0
local PLANE_X, PLANE_Y, PLANE_Z = 0.0, 1.682 * PLANE_S, 0.0
local PART_DEFS = {
    { n = "mid",   hp = 420, c = {0.00,-0.88, 0.22}, h = {0.69,0.81,1.99} },
    { n = "nose",  hp = 200, c = {0.00,-0.98,-3.54}, h = {0.69,0.70,1.77}, parent = "mid" },
    { n = "rear",  hp = 220, c = {0.00,-0.70, 3.76}, h = {0.61,0.89,1.55}, parent = "mid" },
    { n = "tail",  hp = 140, c = {0.00, 0.63, 4.15}, h = {1.98,1.05,1.11}, parent = "rear" },
    { n = "wingL", hp = 260, c = {-2.94,-0.25,0.64}, h = {2.30,0.32,1.37}, parent = "mid" },
    { n = "wingR", hp = 260, c = { 2.94,-0.25,0.64}, h = {2.30,0.32,1.37}, parent = "mid" },
    { n = "engL1", hp = 110, c = {-1.76,-0.64,-0.30}, h = {0.22,0.25,0.47}, parent = "wingL" },
    { n = "engL2", hp = 110, c = {-3.52,-0.72, 0.52}, h = {0.22,0.25,0.47}, parent = "wingL" },
    { n = "engR1", hp = 110, c = { 1.76,-0.64,-0.30}, h = {0.22,0.25,0.47}, parent = "wingR" },
    { n = "engR2", hp = 110, c = { 3.52,-0.72, 0.52}, h = {0.22,0.25,0.47}, parent = "wingR" },
}

-- Thermal / Heatmap color scheme: Cold elements are dark/black-blue, hot elements are white-hot/glowing amber
local COL = {
    ground = {0.05, 0.08, 0.12}, asphalt = {0.03, 0.05, 0.08}, white = {0.85, 0.90, 0.95},
    yellow = {0.95, 0.75, 0.20}, hangar = {0.10, 0.14, 0.20}, roof = {0.08, 0.12, 0.18},
    tower = {0.15, 0.20, 0.28}, glass = {0.20, 0.30, 0.40}, tank = {0.90, 0.45, 0.10}, -- Hot fuel tanks
    crate = {0.12, 0.16, 0.22}, barrel = {0.15, 0.22, 0.30}, scorch = {0.01, 0.01, 0.02}, 
    plane = {0.18, 0.24, 0.32, 1.0},
    cannon = {1.0, 0.95, 0.6}, missile = {0.90, 0.90, 0.95}, smoke = {0.20, 0.25, 0.30},
}

local WEAPONS = {
    cannon  = { cooldown = 0.07, speed = 260, damage = 7,  spread = 0.010 },
    missile = { cooldown = 1.1,  radius = 15, force = 300, damage = 230, color = {1.0, 0.5, 0.1} },
}
local wtimer = { cannon = 0, missile = 0 }
local missile_side = 1

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
local function rnd(a, b) return a + math.random() * (b - a) end
local function tint(c) crayon.graphics.setModelColor(c[1], c[2], c[3]) end
local function tint_model(m, c, k)
    if not m or not m:isValid() then return end
    k = k or 1.0
    for i = 0, m:getPartCount() - 1 do m:setPartColor(i, c[1]*k, c[2]*k, c[3]*k, c[4] or 1.0) end
end
local function norm(x, y, z)
    local l = math.sqrt(x*x + y*y + z*z); if l < 1e-6 then return 0, 1, 0, 0 end
    return x/l, y/l, z/l, l
end
local function rot(x) if ROT_IN_DEGREES then return math.rad(x) end return x end
local function clamp(v, lo, hi) if v < lo then return lo elseif v > hi then return hi else return v end end

local function reg(body, tbl) tbl.body = body; info_by_id[body:getId()] = tbl; return tbl end

local function spawn_box(x, y, z, w, h, d, motion, dens, color, extra)
    local b = crayon.physics3D.createBox(x, y, z, w*.5, h*.5, d*.5, motion, 0.8, 0.25, dens or 1)
    local t = { kind = (motion == "static") and "static" or "prop", shape = "cube",
                sx = w, sy = h, sz = d, color = color, dynamic = motion ~= "static" }
    if extra then for k, v in pairs(extra) do t[k] = v end end
    reg(b, t); bodies[#bodies + 1] = t
    t.cx, t.cy, t.cz, t.crx, t.cry, t.crz = x, y, z, 0, 0, 0
    return t
end
local function spawn_cyl(x, y, z, r, h, motion, dens, color, extra)
    local b = crayon.physics3D.createCylinder(x, y, z, h*.5, r, motion, 0.8, 0.25, dens or 1)
    local t = { kind = (motion == "static") and "static" or "prop", shape = "cyl",
                sx = r*2, sy = h, sz = r*2, color = color, dynamic = motion ~= "static" }
    if extra then for k, v in pairs(extra) do t[k] = v end end
    reg(b, t); bodies[#bodies + 1] = t
    t.cx, t.cy, t.cz, t.crx, t.cry, t.crz = x, y, z, 0, 0, 0
    return t
end

-- Effects particles
local function add_fx(kind, x, y, z, vx, vy, vz, life, size, c)
    if #fx >= MAX_FX then return end
    fx[#fx + 1] = { k = kind, x = x, y = y, z = z, vx = vx, vy = vy, vz = vz,
                    life = life, max = life, size = size, c = c,
                    rx = math.random(0, 6), ry = math.random(0, 6) }
end
local function smoke_puff(x, y, z, big)
    local s = (big == true) and 1.6 or (type(big) == "number" and big or 0.8)
    add_fx("smoke", x, y, z, rnd(-.8, .8), rnd(1.5, 3.5), rnd(-.8, .8), rnd(.8, 1.6), s, COL.smoke)
end

-- ---------------------------------------------------------------------------
-- Plane parts
-- ---------------------------------------------------------------------------
local part_by_name = {}
local function build_plane()
    parts = {}; part_by_name = {}
    for _, d in ipairs(PART_DEFS) do
        local wx = PLANE_X + d.c[1] * PLANE_S
        local wy = PLANE_Y + d.c[2] * PLANE_S
        local wz = PLANE_Z + d.c[3] * PLANE_S
        local b = crayon.physics3D.createBox(wx, wy, wz,
            d.h[1]*PLANE_S, d.h[2]*PLANE_S, d.h[3]*PLANE_S, "kinematic", 0.7, 0.3, 12)
        local p = { kind = "comp", name = d.n, hp = d.hp, max_hp = d.hp, parent = d.parent,
                    attached = true, dynamic = false, model = models["c17_" .. d.n],
                    wx = wx, wy = wy, wz = wz, burn = 0, pending = nil, shade = 1.0,
                    hx = d.h[1]*PLANE_S, hy = d.h[2]*PLANE_S, hz = d.h[3]*PLANE_S }
        reg(b, p)
        parts[#parts + 1] = p; part_by_name[d.n] = p
        tint_model(p.model, COL.plane, 1.0)
    end
end

local trigger_explosion  -- forward

local function detach_part(p, ex, ey, ez, strength)
    if not p.attached then return end
    p.attached, p.dynamic, p.pending = false, true, nil
    local b = p.body
    if not b:isValid() then return end
    b:setMotionType("dynamic"); b:setActive(true)
    b:setFriction(0.8); b:setRestitution(0.25); b:setDamping(0.05, 0.2)
    local dx, dy, dz = p.wx - ex, p.wy - ey, p.wz - ez
    local nx, ny, nz = norm(dx, dy, dz)
    local s = (strength or 1.0)
    b:setVelocity(nx * rnd(6, 14) * s, (ny * 4 + rnd(5, 12)) * s, nz * rnd(6, 14) * s)
    b:setAngularVelocity(rnd(-3, 3) * s, rnd(-3, 3) * s, rnd(-3, 3) * s)
    p.burn = rnd(5, 9)
    score = score + 250
    tint_model(p.model, COL.plane, 0.35)
    flash_alpha = math.max(flash_alpha, 0.25); flash_color = { 1, 0.7, 0.3 }
    cam.shake = cam.shake + 0.6
    if p.name:sub(1, 3) == "eng" or p.name == "mid" then
        trigger_explosion(p.wx, p.wy, p.wz, 7, 60, 0, {1.0, 0.6, 0.2}, 0, nil, true)
    end
    for _, c in ipairs(parts) do
        if c.parent == p.name and c.attached then c.pending = rnd(0.05, 0.35) end
    end
end

local function damage_part(p, amount, ex, ey, ez)
    if not p.attached then return end
    p.hp = p.hp - amount
    local k = 0.45 + 0.55 * math.max(0, p.hp / p.max_hp)
    if math.abs(k - p.shade) > 0.12 then p.shade = k; tint_model(p.model, COL.plane, k) end
    if p.hp <= 0 then detach_part(p, ex, ey, ez, 1.0) end
end

local function plane_left()
    local n = 0
    for _, p in ipairs(parts) do if p.attached then n = n + 1 end end
    return n
end

-- ---------------------------------------------------------------------------
-- Airbase
-- ---------------------------------------------------------------------------
local function build_base()
    crayon.physics3D.destroyAll()
    crayon.physics3D.setGravity(0, -16, 0)
    bodies, info_by_id, projectiles, tracers, fx, explosions = {}, {}, {}, {}, {}, {}
    proj_by_id, enemies = {}, {}
    scorch, scorch_i = {}, 0
    crayon.physics3D.createPlane(0, 0, 0, 0, 1, 0, 120.0)

    spawn_box(0, 0.02, 0, 84, 0.05, 76, "static", 0, COL.asphalt)
    spawn_box(0, 0.06, 0, 0.7, 0.05, 74, "static", 0, COL.yellow)
    for i = -3, 3 do spawn_box(i * 10, 0.06, 36, 4, 0.05, 0.8, "static", 0, COL.white) end

    for _, hx in ipairs({ -44, 44 }) do
        local hz = -44
        spawn_box(hx, 6, hz - 8, 28, 12, 1, "static", 0, COL.hangar)
        spawn_box(hx - 14, 6, hz, 1, 12, 16, "static", 0, COL.hangar)
        spawn_box(hx + 14, 6, hz, 1, 12, 16, "static", 0, COL.hangar)
        spawn_box(hx, 12.5, hz, 30, 1, 18, "static", 0, COL.roof)
    end

    spawn_box(60, 8, 30, 3.5, 16, 3.5, "static", 0, COL.tower)
    spawn_box(60, 17, 30, 7, 3, 7, "static", 0, COL.glass)

    for i = 0, 2 do
        spawn_cyl(-54, 3, 18 + i * 8, 3.0, 6, "dynamic", 40, COL.tank, { tank = true, hp = 70 })
    end

    for i = 1, 10 do
        local x = rnd(-40, 40); if math.abs(x) < 8 then x = x + 14 * (x < 0 and -1 or 1) end
        spawn_box(x, 0.9, rnd(-30, 32), 1.6, 1.6, 1.6, "dynamic", 8, COL.crate)
    end
    for i = 1, 6 do
        spawn_cyl(rnd(-45, 45), 0.6, rnd(-30, 32) , 0.5, 1.2, "dynamic", 8, COL.barrel)
    end

    build_plane()
    wave, wave_timer, banner_t = 0, 1.5, 0
end

-- ---------------------------------------------------------------------------
-- Enemies (For thermal camera, enemies are rendered extremely hot white/yellow)
-- ---------------------------------------------------------------------------
local E_SCALE, E_FOOT, E_ZUP = 1.0, 0.0, false

local function new_animator(model)
    local a = model:createAnimator()
    a:setUpdateRate(15)
    return a
end

local function pick_waypoint(e)
    local side = (e.x >= 0) and 1 or -1
    local wx, wz
    if math.abs(e.z) > 29 and math.random() < 0.6 then
        wx, wz = rnd(-ZONE_X, ZONE_X), rnd(-ZONE_Z, ZONE_Z)
    else
        wx, wz = side * rnd(6, ZONE_X), rnd(-ZONE_Z, ZONE_Z)
    end
    e.wx, e.wz = wx, wz
end

local function set_anim(e, name, speed)
    if e.anim_name == name then return end
    e.anim_name = name
    e.anim:crossFade(name, 0.2, true)
    if speed then e.anim:setSpeed(speed) end
end

local function spawn_enemy(kind)
    local m = (kind == "zombie") and models.zombie or models.soldier
    local side = (math.random() < 0.5) and -1 or 1
    local e = { kind = kind, model = m, anim = new_animator(m), state = "idle",
                x = side * rnd(8, ZONE_X), z = rnd(-ZONE_Z, ZONE_Z), y = 0,
                heading = rnd(0, 6.28), timer = rnd(0.2, 1.5), pitch = 0,
                vx = 0, vy = 0, vz = 0, spin = 0 }
    e.anim:play("Idle", true, 1.0); e.anim_name = "Idle"
    pick_waypoint(e)
    enemies[#enemies + 1] = e
    return e
end

local function alive_count()
    local n = 0
    for _, e in ipairs(enemies) do
        if e.state == "idle" or e.state == "walk" or e.state == "run" then n = n + 1 end
    end
    return n
end

local function kill_enemy(e, how, dx, dy, dz, power)
    if e.state == "dying" or e.state == "flying" or e.state == "dead" then return end
    e.anim:pause()
    if how == "blast" then
        e.state = "flying"
        e.vx, e.vy, e.vz = (dx or 0) * (power or 10), (dy or 0) * (power or 10) + 8, (dz or 0) * (power or 10)
        e.spin = rnd(4, 9)
    else
        e.state, e.timer = "dying", 0
    end
    e.life = 7
    score = score + ((e.kind == "zombie") and 150 or 100)
    for _ = 1, 4 do
        add_fx("spark", e.x, e.y + 1.2, e.z, rnd(-3, 3), rnd(1, 5), rnd(-3, 3), 0.5, 0.12, {1.0, 0.8, 0.4})
    end
end

local function update_enemies(dt)
    for i = #enemies, 1, -1 do
        local e = enemies[i]
        local st = e.state
        if st == "idle" or st == "walk" or st == "run" then
            if st == "idle" then
                e.timer = e.timer - dt
                if e.timer <= 0 then
                    pick_waypoint(e)
                    e.state = (e.kind == "zombie") and "walk" or "run"
                end
            else
                local dx, dz = e.wx - e.x, e.wz - e.z
                local d = math.sqrt(dx*dx + dz*dz)
                if d < 1.0 then
                    e.state, e.timer = "idle", rnd(0.6, 2.2)
                else
                    local spd = (st == "run") and 5.5 or 1.5
                    e.heading = math.atan2(dx, dz)
                    e.x = e.x + dx / d * spd * dt
                    e.z = e.z + dz / d * spd * dt
                    if math.abs(e.z) < 28 and math.abs(e.x) < 5.0 then
                        e.x = (e.x >= 0 and 5.0 or -5.0)
                    end
                    e.x = math.max(-ZONE_X, math.min(ZONE_X, e.x))
                    e.z = math.max(-ZONE_Z, math.min(ZONE_Z, e.z))
                end
            end
            if e.state == "idle" then set_anim(e, "Idle", 1.0)
            elseif e.state == "walk" then set_anim(e, "Walk", e.kind == "zombie" and 0.7 or 1.0)
            else set_anim(e, "Run", 1.0) end
            if e.vis ~= false then
                local ddx, ddz = e.x - cam.x, e.z - cam.z
                local d2 = ddx * ddx + ddz * ddz + cam.y * cam.y
                local rate = (d2 > 6400) and 8 or ((d2 > 2500) and 12 or 20)
                if e.rate ~= rate then e.rate = rate; e.anim:setUpdateRate(rate) end
                e.anim:update(dt)
            end
        elseif st == "dying" then
            e.timer = e.timer + dt
            e.pitch = -math.min(1.0, e.timer / 0.55) * 1.5708
            e.life = e.life - dt
        elseif st == "flying" then
            e.vy = e.vy - 16 * dt
            e.x, e.y, e.z = e.x + e.vx * dt, e.y + e.vy * dt, e.z + e.vz * dt
            e.pitch = e.pitch - e.spin * dt
            if e.y <= 0 then
                e.y, e.state, e.pitch = 0, "dead", -1.5708
            end
        else
            e.life = e.life - dt
        end
        if e.life and e.life <= 0 then table.remove(enemies, i) end
    end
end

local function ray_enemy(ox, oy, oz, dx, dy, dz, maxd)
    local best, bt = nil, maxd
    for _, e in ipairs(enemies) do
        if e.state == "idle" or e.state == "walk" or e.state == "run" then
            for _, h in ipairs(SPHERE_H) do
                local cx, cy, cz = e.x - ox, e.y + h - oy, e.z - oz
                local t = cx*dx + cy*dy + cz*dz
                if t > 0 and t < bt then
                    local px, py, pz = cx - dx*t, cy - dy*t, cz - dz*t
                    if px*px + py*py + pz*pz < 0.36 then best, bt = e, t end
                end
            end
        end
    end
    return best, bt
end

-- ---------------------------------------------------------------------------
-- Explosions
-- ---------------------------------------------------------------------------
trigger_explosion = function(ex, ey, ez, radius, force, dmg, color, hitstop, flash_col, quiet)
    if hitstop and hitstop > 0 then time_scale = hitstop; flash_alpha = 1.0; flash_color = flash_col or {1,1,1} end
    if not quiet then
        cam.shake = cam.shake + force * 0.008
        hud.burst = math.max(hud.burst, 0.5)
    end
    do
        local lobes = {}
        for i = 1, 4 do
            lobes[i] = { rnd(-.5, .5) * radius * 0.5, rnd(0, .4) * radius, rnd(-.5, .5) * radius * 0.5, rnd(.55, 1.0) }
        end
        explosions[#explosions + 1] = { x = ex, y = ey, z = ez, t = 0, size = radius, lobes = lobes }
        if ey < 3 and radius >= 8 then
            scorch_i = scorch_i % 8 + 1
            scorch[scorch_i] = { ex, ez, radius * 0.45 }
        end
    end
    light_t = 0.35
    crayon.graphics.setPointLight(1, ex, ey + 3, ez, color[1], color[2], color[3], radius * 3, 3.0)
    crayon.graphics.setPointLightEnabled(1, true)

    local sp = force * 0.1
    for _ = 1, math.min(16, math.floor(radius * 1.2)) do
        add_fx("spark", ex, ey + 0.4, ez, rnd(-1, 1) * sp, rnd(0.3, 1.2) * sp, rnd(-1, 1) * sp,
               rnd(0.5, 1.1), 0.1, { 1.0, 0.9, 0.6 })
    end
    for _ = 1, math.min(8, math.floor(radius * 0.7)) do
        add_fx("debris", ex, ey + 0.3, ez, rnd(-1, 1) * sp * 0.7, rnd(0.4, 1.0) * sp * 0.7,
               rnd(-1, 1) * sp * 0.7, rnd(0.6, 1.4), rnd(0.15, 0.4), { 0.15, 0.15, 0.2 })
    end
    for i = 1, math.min(7, math.floor(radius * 0.5) + 2) do
        add_fx("smoke", ex + rnd(-1, 1) * radius * 0.3, ey + rnd(0, 1) * radius * 0.3, ez + rnd(-1, 1) * radius * 0.3,
               rnd(-1.5, 1.5), rnd(3, 6), rnd(-1.5, 1.5), rnd(1.4, 2.4), radius * 0.22, COL.smoke)
    end

    for _, body in ipairs(crayon.physics3D.overlapSphere(ex, ey, ez, radius)) do
        if body and body:isValid() then
            local info = info_by_id[body:getId()]
            if info then
                local bx, by, bz = body:getPosition()
                local nx, ny, nz, d = norm(bx - ex, by - ey, bz - ez)
                local fall = 1.0 - math.min(1.0, math.max(0, d - (info.hx or 0.5)) / radius)
                if fall > 0 then
                    if info.kind == "comp" and dmg > 0 then
                        damage_part(info, dmg * fall, ex, ey, ez)
                    end
                    if info.tank and dmg > 0 then
                        info.hp = info.hp - dmg * fall
                        if info.hp <= 0 and not info.boomed then
                            info.boomed = true
                            trigger_explosion(bx, by, bz, 11, 200, 120, {1.0, 0.6, 0.2}, 0.12, {1,0.5,0.2})
                        end
                    end
                    if info.dynamic and body:isValid() then
                        local vx, vy, vz = body:getVelocity()
                        local f = fall * fall * force * 0.14
                        body:setVelocity(vx + nx * f, vy + (ny + 0.9) * f, vz + nz * f)
                        body:setAngularVelocity(rnd(-1, 1) * f * 0.25, rnd(-1, 1) * f * 0.25, rnd(-1, 1) * f * 0.25)
                        body:setActive(true)
                    end
                end
            end
        end
    end

    if dmg > 0 or force > 150 then
        for _, e in ipairs(enemies) do
            if e.state == "idle" or e.state == "walk" or e.state == "run" then
                local nx, ny, nz, d = norm(e.x - ex, e.y + 1 - ey, e.z - ez)
                if d < radius * 0.85 then
                    kill_enemy(e, "blast", nx, math.max(0.3, ny), nz, force * 0.05 * (1 - d / radius) + 3)
                end
            end
        end
    end
end

-- ---------------------------------------------------------------------------
-- Weapons
-- ---------------------------------------------------------------------------
local function fire_cannon(hx, hy, hz)
    local mx, my, mz = cam.x, cam.y - ((pov == 2) and 0.6 or 1.5), cam.z
    local dx, dy, dz = norm(hx - mx, hy - my, hz - mz)
    local sp = WEAPONS.cannon.spread
    dx, dy, dz = norm(dx + rnd(-sp, sp), dy + rnd(-sp, sp), dz + rnd(-sp, sp))

    local hit, px, py, pz, nx, ny, nz, dist, body = crayon.physics3D.raycast(mx, my, mz, dx, dy, dz, 400)
    local maxd = hit and dist or 400
    local enemy, et = ray_enemy(mx, my, mz, dx, dy, dz, maxd)

    local endd = maxd
    if enemy then
        endd = et
        kill_enemy(enemy, "shot")
        add_fx("spark", mx + dx*et, my + dy*et, mz + dz*et, rnd(-2, 2), rnd(1, 4), rnd(-2, 2), 0.4, 0.12, {1.0, 0.9, 0.6})
    elseif hit then
        for _ = 1, 3 do
            add_fx("spark", px, py + 0.1, pz, nx * 4 + rnd(-3, 3), ny * 4 + rnd(1, 4), nz * 4 + rnd(-3, 3), 0.35, 0.1, {1, 0.9, 0.7})
        end
        local info = body and info_by_id[body:getId()]
        if info then
            if info.kind == "comp" then damage_part(info, WEAPONS.cannon.damage, px, py, pz)
            elseif info.tank then
                info.hp = info.hp - 9
                if info.hp <= 0 and not info.boomed then
                    info.boomed = true
                    trigger_explosion(px, py, pz, 11, 200, 120, {1.0, 0.6, 0.2}, 0.12, {1,0.5,0.2})
                end
            end
            if info.dynamic then
                local vx, vy, vz = body:getVelocity()
                body:setVelocity(vx + dx * 3.2, vy + dy * 3.2 + 0.4, vz + dz * 3.2)
                body:setActive(true)
            end
        end
    end
    tracers[#tracers + 1] = { x = mx, y = my, z = mz, dx = dx, dy = dy, dz = dz, d = 0, max = endd }
end

local function fire_missile(hx, hy, hz)
    missile_side = -missile_side
    local yaw = math.rad(cam.yaw)
    local rx, rz = -math.sin(yaw), math.cos(yaw)
    local so = (pov == 2) and 0.6 or 1.8
    local mx, my, mz = cam.x + rx * so * missile_side, cam.y - so, cam.z + rz * so * missile_side
    local dx, dy, dz = norm(hx - mx, hy - my, hz - mz)
    local b = crayon.physics3D.createSphere(mx, my, mz, 0.4, "dynamic", 0.2, 0.1, 6.0)
    b:setMotionQuality(true)
    b:setGravityFactor(0.1)
    b:setVelocity(dx * 25, dy * 25, dz * 25)
    local p = { body = b, id = b:getId(), tx = hx, ty = hy, tz = hz, age = 0, spd = 25,
                trail = 0, hit = false }
    proj_by_id[p.id] = p
    projectiles[#projectiles + 1] = p
    add_fx("fire", mx, my, mz, dx*2, dy*2, dz*2, 0.15, 0.7, {1.0, 0.8, 0.4})
end

local function update_projectiles(dt)
    for i = #projectiles, 1, -1 do
        local p = projectiles[i]
        local done = false
        if not (p.body and p.body:isValid()) then
            done = true
        else
            p.age = p.age + dt
            local px, py, pz = p.body:getPosition()
            p.spd = math.min(115, 25 + p.age * 95)
            local dx, dy, dz = norm(p.tx - px, p.ty - py, p.tz - pz)
            local vx, vy, vz = p.body:getVelocity()
            local k = math.min(1, dt * 2.5)
            p.body:setVelocity(vx + (dx * p.spd - vx) * k, vy + (dy * p.spd - vy) * k, vz + (dz * p.spd - vz) * k)

            p.trail = p.trail - dt
            if p.trail <= 0 then
                p.trail = 0.05
                add_fx("trail", px, py, pz,
                       rnd(-0.25, 0.25), rnd(0.05, 0.35), rnd(-0.25, 0.25),
                       rnd(0.75, 1.15), rnd(0.42, 0.62), nil)
            end

            if py <= 0.5 or p.age > 6 then p.hit = true end
            for _, e in ipairs(enemies) do
                if (e.state == "idle" or e.state == "walk" or e.state == "run")
                   and math.abs(e.x - px) < 1.2 and math.abs(e.z - pz) < 1.2 and py < e.y + 2.2 then p.hit = true end
            end
            if p.hit then
                local w = WEAPONS.missile
                trigger_explosion(px, math.max(py, 0.3), pz, w.radius, w.force, w.damage, w.color, 0.1, {1, 0.6, 0.2})
                done = true
            end
        end
        if done then
            if p.body and p.body:isValid() then p.body:destroy() end
            proj_by_id[p.id] = nil
            table.remove(projectiles, i)
        end
    end
end

function crayon.onCollisionEnter(a, b)
    local p = proj_by_id[a] or proj_by_id[b]
    if p then p.hit = true end
end

-- ---------------------------------------------------------------------------
-- Init
-- ---------------------------------------------------------------------------
local function apply_fx_mode()
    local g = crayon.graphics
    if fx_mode == 0 then
        g.setRetroEffects({ jitterResolution = false, affine = 0, dither = false, colorDepth = 32,
            crt = { scanlines = 0, curvature = 0, vignette = 0 },
            fog = { startDist = 10000, endDist = 10001, color = {0,0,0} } })
    elseif fx_mode == 1 then
        g.setRetroEffects({ jitterResolution = false, affine = 0, dither = true, colorDepth = 32,
            crt = { scanlines = 0.25, curvature = 0.0, vignette = 0.35 },
            fog = { startDist = 90, endDist = 220, color = {0.02, 0.04, 0.08} } })
    else
        -- White-hot FLIR infrared camera look: heavy grain, strong CRT scanlines, cold bluish/dark fog
        g.setRetroEffects({ jitterResolution = {320, 240}, affine = 0, dither = true, colorDepth = 8,
            crt = { scanlines = 0.65, curvature = 0.08, vignette = 0.55 },
            fog = { startDist = 80, endDist = 200, color = {0.02, 0.05, 0.10} } })
    end
end

function crayon.config(t)
    t.graphics.renderer = "gl"
end

function crayon.init()
    crayon.window.setResolution(320, 240)
    crayon.window.setTitle("FLIR Thermal Air Strike")
    crayon.window.setScalingMode("integer")
    math.randomseed(os.time and os.time() or 12345)

    models.cube = crayon.graphics.loadModel("cube")
    models.cylinder = crayon.graphics.loadModel("cylinder")
    models.sphere = crayon.graphics.loadModel("sphere")
    for _, d in ipairs(PART_DEFS) do
        models["c17_" .. d.n] = crayon.graphics.loadModel("c17_" .. d.n .. ".obj")
    end
    models.soldier = crayon.graphics.loadModel("Soldier.glb")
    models.zombie  = crayon.graphics.loadModel("Soldier.glb")
    tint_model(models.zombie, {0.9, 0.8, 0.5}) -- zombies also hot in thermal view
    tex_white = crayon.graphics.getWhiteTexture()
    tex_smoke = crayon.graphics.loadTexture("smoke.png")
    tex_glow  = crayon.graphics.loadTexture("glow.png")
    if tex_smoke and not tex_smoke:isValid() then tex_smoke = nil end
    if tex_glow and not tex_glow:isValid() then tex_glow = nil end

    local x0, y0, z0, x1, y1, z1 = models.soldier:getBounds()
    local sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    E_ZUP = sz > sy * 1.5
    local h = E_ZUP and sz or sy
    if h > 0 then E_SCALE = 1.8 / h end
    E_FOOT = -(E_ZUP and z0 or y0) * E_SCALE

    crayon.graphics.setLight(0.4, -0.9, -0.3, 0.9, 0.95, 0.85, 0.12, 0.08, 0.1)
    apply_fx_mode()
    for i = 1, 8 do hud.bands[i] = math.random() * 240 end
    build_base()
end

-- ---------------------------------------------------------------------------
-- Update
-- ---------------------------------------------------------------------------
local function update_waves(dt)
    if alive_count() == 0 then
        wave_timer = wave_timer - dt
        if wave_timer <= 0 then
            wave = wave + 1
            local total = math.min(MAX_ENEMIES_CAP, MAX_ENEMIES_BASE + (wave - 1) * 2)
            for i = 1, total do spawn_enemy((i % 3 == 0) and "zombie" or "soldier") end
            banner, banner_t, wave_timer = "SECTOR " .. wave, 2.5, 2.5
        end
    end
end

local function set_pov(n)
    if pov == 1 then saved_view = { y = cam.y, pitch = cam.pitch, fov = cam.fov } end
    pov = n
    if n == 2 then cam.y, cam.pitch, cam.fov = 2.2, -3, 75
    else cam.y, cam.pitch, cam.fov = saved_view.y, saved_view.pitch, saved_view.fov end
end

function crayon.update(raw_dt)
    if time_scale < 1.0 then time_scale = math.min(1.0, time_scale + raw_dt * 1.5) end
    local dt = raw_dt * time_scale

    if crayon.key.isPressed("tab") then debug_draw = not debug_draw end
    if crayon.key.isPressed("f1") then fx_mode = (fx_mode + 1) % 3; apply_fx_mode() end
    if crayon.key.isPressed("r") then build_base() end
    if crayon.key.isPressed("v") then set_pov(pov % 3 + 1) end

    hud.tc, hud.blink = hud.tc + raw_dt, hud.blink + raw_dt
    hud.burst = math.max(0, hud.burst - raw_dt * 2.5)
    glitch.t = glitch.t + raw_dt
    if fx_mode == 2 then
        glitch.intensity = math.max(0, glitch.intensity - raw_dt * 5)
        glitch.next_spike = glitch.next_spike - raw_dt
        if glitch.next_spike <= 0 then
            glitch.intensity = 0.4 + math.random() * 0.4
            glitch.next_spike = 4 + math.random() * 6
        end
        glitch.whisper_t = glitch.whisper_t - raw_dt
        if glitch.whisper_t <= 0 then
            glitch.whisper = WHISPERS[math.random(#WHISPERS)]; glitch.whisper_t = 3 + math.random() * 4
        end
        for i = 1, #hud.bands do
            hud.bands[i] = hud.bands[i] + (30 + i * 5) * raw_dt
            if hud.bands[i] > 260 then hud.bands[i] = -20 end
        end
    else glitch.intensity = 0 end

    if flash_alpha > 0 then flash_alpha = math.max(0, flash_alpha - raw_dt * 2) end
    if cam.shake > 0 then cam.shake = math.max(0, cam.shake - raw_dt * 6) end
    if banner_t > 0 then banner_t = banner_t - raw_dt end
    if light_t > 0 then
        light_t = light_t - raw_dt
        if light_t <= 0 then crayon.graphics.setPointLightEnabled(1, false) end
    end

    local sp = ((pov == 2) and 10 or 22) * raw_dt
    local yaw = math.rad(cam.yaw)
    local fx_, fz_ = math.cos(yaw), math.sin(yaw)
    if crayon.key.isDown("w") then cam.x, cam.z = cam.x + fx_ * sp, cam.z + fz_ * sp end
    if crayon.key.isDown("s") then cam.x, cam.z = cam.x - fx_ * sp, cam.z - fz_ * sp end
    if crayon.key.isDown("a") then cam.x, cam.z = cam.x + fz_ * sp, cam.z - fx_ * sp end
    if crayon.key.isDown("d") then cam.x, cam.z = cam.x - fz_ * sp, cam.z + fx_ * sp end
    if pov ~= 2 then
        if crayon.key.isDown("q", "space") then cam.y = cam.y + 22 * raw_dt end
        if crayon.key.isDown("z", "shift") then cam.y = cam.y - 22 * raw_dt end
    end
    if crayon.key.isDown("left")  then cam.yaw = cam.yaw - 85 * raw_dt end
    if crayon.key.isDown("right") then cam.yaw = cam.yaw + 85 * raw_dt end
    if crayon.key.isDown("up")    then cam.pitch = math.min(cam.pitch + 60 * raw_dt, 80) end
    if crayon.key.isDown("down")  then cam.pitch = math.max(cam.pitch - 60 * raw_dt, -85) end
    cam.x = math.max(-HX, math.min(HX, cam.x)); cam.z = math.max(-HZ - 30, math.min(HZ + 40, cam.z))
    if pov == 2 then
        cam.y = 2.2; cam.pitch = math.max(-45, math.min(45, cam.pitch))
    else cam.y = math.max(12, math.min(120, cam.y)) end

    frame = frame + 1
    local fire1 = crayon.mouse.isDown(1) or crayon.key.isDown("f")
    local fire2 = crayon.mouse.isDown(3) or crayon.key.isDown("g")
    if pov ~= 3 and (fire1 or fire2 or frame % 4 == 0) then
        local mx, my = crayon.mouse.getPosition()
        local ox, oy, oz, dx, dy, dz = crayon.graphics.unproject(mx, my)
        local h, x, y, z = crayon.physics3D.raycast(ox, oy, oz, dx, dy, dz, 400)
        cam.hit, cam.tx, cam.ty, cam.tz = h, x, y, z
    end
    local hit, hx, hy, hz = cam.hit, cam.tx, cam.ty, cam.tz

    wtimer.cannon  = math.max(0, wtimer.cannon  - dt)
    wtimer.missile = math.max(0, wtimer.missile - dt)
    if hit then
        if fire1 and wtimer.cannon == 0 then
            wtimer.cannon = WEAPONS.cannon.cooldown
            fire_cannon(hx, hy, hz)
            cam.shake = cam.shake + 0.05
        end
        if fire2 and wtimer.missile == 0 and #projectiles < 6 then
            wtimer.missile = WEAPONS.missile.cooldown
            fire_missile(hx, hy, hz)
        end
    end

    update_projectiles(dt)
    local lp = projectiles[#projectiles]
    if lp and lp.body:isValid() then
        local x, y, z = lp.body:getPosition()
        local vx, vy, vz = lp.body:getVelocity()
        local dx, dy, dz = norm(vx, vy, vz)
        mcam.x, mcam.y, mcam.z, mcam.dx, mcam.dy, mcam.dz, mcam.hold = x, y, z, dx, dy, dz, 1.4
    elseif mcam.hold > 0 then mcam.hold = mcam.hold - raw_dt end
    update_enemies(dt)
    update_waves(raw_dt)

    for i = #explosions, 1, -1 do
        local e = explosions[i]; e.t = e.t + raw_dt
        if e.t >= 1.1 then table.remove(explosions, i) end
    end
    hud.lt = (hud.lt or 0) - raw_dt
    if hud.lt <= 0 then
        hud.lt = 0.25
        hud.lines = {
            string.format("SENSOR MODE: WHITE-HOT"),
            string.format("ALTITUDE %5.1f M", cam.y),
            string.format("SECTOR %d  TARGETS %d", wave, alive_count()),
            string.format("AIRFRAME %d/%d", plane_left(), #PART_DEFS),
            string.format("SCORE %d", score),
            string.format("SYS FPS %d", math.floor(crayon.time.getFps() or 0)),
        }
    end

    for i = #tracers, 1, -1 do
        local t = tracers[i]
        t.d = t.d + 420 * dt
        if t.d >= t.max then table.remove(tracers, i) end
    end

    local i = 1
    while i <= #fx do
        local p = fx[i]
        p.life = p.life - dt
        if p.life <= 0 then
            fx[i] = fx[#fx]; fx[#fx] = nil
        else
            if p.k == "debris" or p.k == "spark" then
                p.vy = p.vy - 30 * dt
                if p.y < 0.15 then p.y, p.vy, p.vx, p.vz = 0.15, -p.vy * 0.4, p.vx * 0.7, p.vz * 0.7 end
            elseif p.k == "smoke" then
                p.vx, p.vz = p.vx * 0.97, p.vz * 0.97; p.vy = p.vy * 0.985
            elseif p.k == "trail" then
                p.vx, p.vz = p.vx * 0.90, p.vz * 0.90; p.vy = p.vy * 0.94
                p.size = p.size * (1 + dt * 1.6)
            end
            p.x, p.y, p.z = p.x + p.vx * dt, p.y + p.vy * dt, p.z + p.vz * dt
            p.rx, p.ry = p.rx + dt * 4, p.ry + dt * 3
            i = i + 1
        end
    end

    for _, p in ipairs(parts) do
        if p.pending and p.attached then
            p.pending = p.pending - dt
            if p.pending <= 0 then detach_part(p, p.wx, p.wy - 2, p.wz, 0.7) end
        end
        if not p.attached and p.burn > 0 and p.body:isValid() then
            p.burn = p.burn - dt
            local bx, by, bz = p.body:getPosition()
            p.wx, p.wy, p.wz = bx, by, bz
            if math.random() < dt * 14 then
                smoke_puff(bx + rnd(-1, 1), by + rnd(0, 1.5), bz + rnd(-1, 1), true)
                add_fx("fire", bx + rnd(-1, 1), by + rnd(0, 1), bz + rnd(-1, 1), 0, 2, 0, 0.3, 0.6, {1, 0.6, 0.2})
            end
        end
    end

    for k = #bodies, 1, -1 do
        if frame % 20 ~= 0 then break end
        local b = bodies[k]
        if b.body:isValid() then
            local _, by = b.body:getPosition()
            if by < -15 then info_by_id[b.body:getId()] = nil; b.body:destroy(); table.remove(bodies, k) end
        else table.remove(bodies, k) end
    end
end

-- ---------------------------------------------------------------------------
-- HUD (Military FLIR / Targeting Overlay)
-- ---------------------------------------------------------------------------
local function draw_hud(vw, vh)
    local g = crayon.graphics
    local cx, cy = vw * 0.5, vh * 0.5

    -- Infrared reticle brackets
    g.setColor(0.9, 0.95, 1.0, 0.9)
    g.drawCircle("line", cx, cy, 32); g.drawCircle("line", cx, cy, 14)
    g.drawLine(cx - 55, cy, cx - 12, cy, 1); g.drawLine(cx + 12, cy, cx + 55, cy, 1)
    g.drawLine(cx, cy - 55, cx, cy - 12, 1); g.drawLine(cx, cy + 12, cx, cy + 55, 1)
    g.drawCircle("fill", cx, cy, 1.5)

    -- Dynamic Target Heat Box locked over closest threat/cursor
    g.drawRect("line", cx - 18, cy - 18, 36, 36, 1)

    g.setColor(0.85, 0.95, 1.0, 0.9)
    local lines = hud.lines or {}
    for i, l in ipairs(lines) do g.drawText(l, 8, 6 + (i - 1) * 9, 1.0) end

    local x = 232
    g.drawText("CAN", x, 6, 0.9); g.drawText("MSL", x, 20, 0.9)
    local function bar(y, t, total)
        g.drawRect("line", x, y, 62, 4)
        local w = 60 * (1 - t / total); if w > 0 then g.drawRect("fill", x + 1, y + 1, w, 2) end
    end
    bar(15, wtimer.cannon, WEAPONS.cannon.cooldown); bar(29, wtimer.missile, WEAPONS.missile.cooldown)

    if (math.floor(hud.blink * 2) % 2 == 0) then
        g.setColor(1, 0.2, 0.2, 0.95); g.drawCircle("fill", vw - 46, 42, 3)
    end
    g.setColor(0.9, 0.95, 1.0, 0.9); g.drawText("FLIR-REC", vw - 56, 38, 1.0)

    g.setColor(0.85, 0.95, 1.0, 0.9)
    g.drawText("[FX:THERMAL-HOT]", 8, 220, 0.85)

    if banner_t > 0 then
        local w = g.getTextWidth(banner, 2.0)
        g.setColor(1, 0.9, 0.4, math.min(1, banner_t))
        g.drawText(banner, (vw - w) * 0.5, 40, 2.0)
    end
    if wave > 0 and alive_count() == 0 and plane_left() == 0 then
        g.setColor(1, 1, 1, 0.9); g.drawText("AIRFRAME LOST", cx - 42, 70, 1.0)
    end

    g.setColor(0.85, 0.95, 1.0, 0.5)
    g.drawText("WASD:FLY LMB/F:GUN RMB/G:MSL V:POV F1:FX R:RESET", 8, vh - 8, 0.8)
end

-- ---------------------------------------------------------------------------
-- Draw
-- ---------------------------------------------------------------------------
local function dir_to_euler(ux, uy, uz)
    local yaw = math.atan2(ux, uz)
    local pitch = math.pi * 0.5 - math.asin(clamp(uy, -1, 1))
    return pitch, yaw
end

function crayon.draw()
    local g = crayon.graphics
    -- Deep dark blue-black background typical of night-vision / infrared thermal screens
    g.clear(0.01, 0.03, 0.06)
    local vw, vh = crayon.window.getResolution()
    local gi = glitch.intensity
    local fx_pushes = 0

    -- Heavy Post-Process stack for Thermal Camera grading and bloom
    if fx_mode >= 1 then
        g.pushEffect("vignette", { intensity = 0.55 + gi * 0.3 + hud.burst * 0.15 })
        fx_pushes = fx_pushes + 1
        g.pushEffect("filmGrain", {
            intensity = 0.25 + gi * 0.45 + hud.burst * 0.35 + math.min(0.3, #explosions * 0.06)
        })
        fx_pushes = fx_pushes + 1
        g.pushEffect("chromatic", {
            amount = 0.005 + gi * 0.025 + hud.burst * 0.01 + cam.shake * 0.004
        })
        fx_pushes = fx_pushes + 1
        if fx_mode == 2 then
            g.pushEffect("vhs", { intensity = gi * 0.8 + hud.burst * 0.4 })
            fx_pushes = fx_pushes + 1
        end
        g.pushEffect("bloom2D", {
            intensity = math.min(3.5, 1.2 + hud.burst * 2.2 + #explosions * 0.25),
            threshold = 0.35 -- Lower threshold to make warm bodies/engine exhausts glow bright white-hot
        })
        fx_pushes = fx_pushes + 1
    end

    g.setShadingMode("gouraud")
    local P, T = cam_tbl.position, cam_tbl.target
    if pov == 3 and (#projectiles > 0 or mcam.hold > 0) then
        P[1], P[2], P[3] = mcam.x - mcam.dx * 2.5, mcam.y - mcam.dy * 2.5 + 0.8, mcam.z - mcam.dz * 2.5
        T[1], T[2], T[3] = mcam.x + mcam.dx * 12, mcam.y + mcam.dy * 12, mcam.z + mcam.dz * 12
        cam_tbl.fov = 70
    else
        local mag = cam.shake * cam.shake * 0.5
        local sx, sy, sz = (math.random() - .5) * mag, (math.random() - .5) * mag * .5, (math.random() - .5) * mag
        local ry, rp = math.rad(cam.yaw), math.rad(cam.pitch)
        local px, py, pz = cam.x + sx, cam.y + sy, cam.z + sz
        P[1], P[2], P[3] = px, py, pz
        T[1], T[2], T[3] = px + math.cos(rp) * math.cos(ry), py + math.sin(rp), pz + math.cos(rp) * math.sin(ry)
        cam_tbl.fov = cam.fov + cam.shake * 0.2
    end
    g.setCamera3D(cam_tbl)

    -- Ground terrain (cold terrain rendered dark)
    tint(COL.ground); g.drawPlane(0, 0, 0, HX * 2 + 20, HZ * 2 + 20, tex_white, 0, 0, 0)
    tint(COL.scorch)
    for _, sc in ipairs(scorch) do g.drawCylinder(sc[1], 0.1, sc[2], sc[3], 0.02, tex_white, 0, 0, 0) end

    -- Structures and props
    for _, b in ipairs(bodies) do
        if b.body:isValid() then
            if b.dynamic and b.body:isActive() then
                b.cx, b.cy, b.cz = b.body:getPosition()
                local a1, a2, a3 = b.body:getRotation()
                b.crx, b.cry, b.crz = rot(a1), rot(a2), rot(a3)
            end
            local x, y, z, rx, ryy, rz = b.cx, b.cy, b.cz, b.crx, b.cry, b.crz
            tint(b.color or COL.white)
            if b.shape == "cube" then g.drawCube(x, y, z, b.sx, b.sy, b.sz, tex_white, rx, ryy, rz)
            else g.drawCylinder(x, y, z, b.sx * 0.5, b.sy, tex_white, rx, ryy, rz) end
        end
    end
    g.setModelColor(1, 1, 1)

    -- Plane parts
    for _, p in ipairs(parts) do
        if p.body:isValid() then
            if p.attached then
                g.drawModel(p.model, p.wx, p.wy, p.wz, 0, 0, 0, PLANE_S, PLANE_S, PLANE_S, tex_white)
            else
                local x, y, z = p.body:getPosition()
                local rx, ryy, rz = p.body:getRotation()
                g.drawModel(p.model, x, y, z, rot(rx), rot(ryy), rot(rz), PLANE_S, PLANE_S, PLANE_S, tex_white)
            end
        end
    end

    -- Enemies rendered as blazing hot infrared heat signatures (Bright White/Yellow)
    for _, e in ipairs(enemies) do
        local _, _, vis = g.project(e.x, e.y + 1.0, e.z)
        e.vis = vis
        if vis then
            -- Set glowing hot thermal color signature for living targets
            g.setModelColor(1.0, 0.95, 0.8)
            g.drawModelSkinned(e.model, e.anim, e.x, e.y + E_FOOT, e.z,
                e.pitch or 0, e.heading + ENEMY_YAW, 0, E_SCALE, E_SCALE, E_SCALE, 0)
        end
    end
    g.setModelColor(1, 1, 1)

    -- Effects particles (Thermal explosions and glowing embers)
    if tex_glow or tex_smoke then
        g.setBlendMode("additive"); g.setDepthWrite(false); g.setShadingMode("unlit")
        for _, p in ipairs(fx) do
            local a = p.life / p.max
            if p.k == "fire" then
                local s = p.size * (0.7 + 1.8 * (1 - a))
                local cr, cg, cb = 1.0, 0.85 * a, 0.4 * a
                g.setColor(cr, cg, cb, a)
                g.drawBillboardRot(tex_glow or tex_smoke, p.x, p.y, p.z, s, s, 0, nil, {cr, cg, cb, a})
            elseif p.k == "spark" then
                g.setColor(1.0, 0.9, 0.6, 1)
                g.drawLine3D(p.x, p.y, p.z, p.x - p.vx * 0.06, p.y - p.vy * 0.06, p.z - p.vz * 0.06)
            elseif p.k == "trail" and a > 0.55 then
                local b = (a - 0.55) / 0.45
                local s = p.size * (0.7 + 1.0 * b)
                local cr, cg, cb = 1.0, 0.7 * b, 0.3 * b
                g.setColor(cr, cg, cb, b * 0.9)
                g.drawBillboardRot(tex_glow or tex_smoke, p.x, p.y, p.z, s, s, 0, nil, {cr, cg, cb, b * 0.9})
            end
        end
        g.setBlendMode("alpha"); g.setShadingMode("gouraud")
        for _, p in ipairs(fx) do
            local a = p.life / p.max
            if p.k == "smoke" then
                local s = p.size * (1.6 - 1.1 * a)
                local c = 0.25 + 0.20 * (1 - a)
                local al = math.min(1, (1 - a) * 6) * a * 0.6
                g.setColor(c, c + 0.05, c + 0.1, al)
                g.drawBillboardRot(tex_smoke, p.x, p.y, p.z, s, s, p.rx * 0.25, nil, {c, c + 0.05, c + 0.1, al})
            elseif p.k == "trail" and a <= 0.55 then
                local b = a / 0.55
                local s = p.size * (1.8 - 0.8 * b)
                local c = 0.25 + 0.15 * b
                local al = math.min(1, b * 1.6) * 0.7
                g.setColor(c, c + 0.05, c + 0.1, al)
                local tex = tex_smoke or tex_white
                g.drawBillboardRot(tex, p.x, p.y, p.z, s, s, 0, nil, {c, c + 0.05, c + 0.1, al})
            end
        end
        g.setDepthWrite(true); g.setColor(1, 1, 1, 1)
    end

    for _, p in ipairs(fx) do
        if p.k == "debris" then
            g.setModelColor(0.3, 0.35, 0.4)
            g.drawCube(p.x, p.y, p.z, p.size, p.size, p.size, tex_white, p.rx, p.ry, 0)
        end
    end

    -- Tracers (White-hot ammunition streaks)
    g.setColor(1.0, 0.95, 0.8, 1)
    for _, t in ipairs(tracers) do
        local d0 = t.d; local d1 = math.min(t.max, d0 + 9)
        g.drawLine3D(t.x + t.dx * d0, t.y + t.dy * d0, t.z + t.dz * d0, t.x + t.dx * d1, t.y + t.dy * d1, t.z + t.dz * d1)
    end
    g.setColor(1, 1, 1, 1)

    -- Missiles (Infrared plume tracking)
    for _, p in ipairs(projectiles) do
        if p.body:isValid() then
            local x, y, z = p.body:getPosition()
            local vx, vy, vz = p.body:getVelocity()
            local spd = math.sqrt(vx*vx + vy*vy + vz*vz)
            local ux, uy, uz = 0, 0, 1
            if spd > 0.01 then ux, uy, uz = vx / spd, vy / spd, vz / spd end
            local pitch, yaw = dir_to_euler(ux, uy, uz)

            g.setModelColor(0.8, 0.85, 0.9)
            g.drawCylinder(x, y, z, 0.15, 0.85, tex_white, pitch, yaw, 0)

            local nx = x + ux * 0.55
            local ny = y + uy * 0.55
            local nz = z + uz * 0.55
            g.setModelColor(1.0, 0.6, 0.2)
            g.drawCone(nx, ny, nz, 0.15, 0.28, tex_white, pitch, yaw, 0)

            if tex_glow or tex_smoke then
                local ex = x - ux * 0.42
                local ey = y - uy * 0.42
                local ez = z - uz * 0.42
                local s = 0.8 + math.random() * 0.4
                g.setBlendMode("additive"); g.setDepthWrite(false)
                g.setColor(1, 0.8, 0.4, 0.95)
                g.drawBillboardRot(tex_glow or tex_smoke, ex, ey, ez, s, s, 0, nil, {1, 0.8, 0.4, 0.95})
                g.setBlendMode("alpha"); g.setDepthWrite(true)
            end
        end
    end
    g.setModelColor(1, 1, 1)

    -- Thermal Explosions (Blazing white/orange thermal bloom)
    if #explosions > 0 then
        g.setBlendMode("additive"); g.setDepthWrite(false); g.setShadingMode("unlit")
        for _, e in ipairs(explosions) do
            local t, sz = e.t, e.size
            local f = 1 - t / 1.1
            if t < 0.3 then
                local k = 1 - t / 0.3
                g.setModelColor(1.0, 1.0, 0.9 * k)
                g.drawSphere(e.x, e.y + sz * 0.15, e.z, sz * (0.35 + t * 1.6), tex_white, 0, 0, 0)
            end
            local grow = math.min(1, t * 5)
            g.setModelColor(1.0, 0.6 * f, 0.2 * f * f)
            for _, l in ipairs(e.lobes) do
                local r = sz * 0.55 * l[4] * (0.4 + 0.6 * grow) * (1 + 0.3 * t)
                g.drawSphere(e.x + l[1], e.y + l[2] + t * sz * 0.35, e.z + l[3], r, tex_white, 0, 0, 0)
            end
        end
        g.setBlendMode("alpha"); g.setDepthWrite(true); g.setShadingMode("gouraud")
    end
    g.setModelColor(1, 1, 1)

    if debug_draw then
        g.setDepthTest(true)
        crayon.physics3D.drawDebug({ shapes = true, velocities = true, color = { 1, 0.35, 0.35, 0.9 } })
    end

    for _ = 1, fx_pushes do g.popEffect() end

    -- draw_hud(vw, vh)

    if flash_alpha > 0 then
        g.setColor(flash_color[1], flash_color[2], flash_color[3], flash_alpha)
        g.drawRect("fill", 0, 0, vw, vh)
    end
    
    -- Thermal Scanline and Static Interference Bands
    -- if fx_mode >= 1 then
        -- local n = math.floor(2 + gi * 10 + hud.burst * 8)
        -- for i = 1, math.min(n, #hud.bands) do
            -- g.setColor(0.7, 0.9, 1.0, math.min(0.5, 0.1 + gi * 0.3 + hud.burst * 0.3))
            -- g.drawRect("fill", 0, hud.bands[i], vw, math.random(1, 3))
        -- end
        -- if glitch.whisper_t > 0 and math.floor(glitch.whisper_t * 8) % 2 == 0 then
            -- g.setColor(0.7, 0.9, 1.0, 0.7)
            -- local w = g.getTextWidth(glitch.whisper, 1.0)
            -- g.drawText(glitch.whisper, (vw - w) * 0.5, vh - 18, 1.0)
        -- end
    -- end
end