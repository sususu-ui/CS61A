const board = document.querySelector('.board');
const selector = document.querySelector('.selector');
const timer_el = document.querySelector('.hud-timer');
const timer_dial_el = document.querySelector('.hud-timer-dial');
const timer_text_el = document.querySelector('.hud-timer-text');
const game_over_el = document.querySelector('.game-over-alert');
const boss_bar = document.querySelector('.boss-bar');
const boss_bar_fill = document.querySelector('.boss-bar-fill');
const bgm = document.getElementById('backgroundmusic');
let to_deploy = null;
let to_remove = false;
// placing ants is a player-turn move; the bee phase locks the board
let my_turn = true;

const ANT_ACTION_WAITING_BASE = 3500; // ms
const BEE_ACTION_WAITING_BASE = 1000; // ms
const HEALTH_BAR_TTL = 5;    // actions
const THROW_DURATION = 500;  // ms
const HIT_DURATION = 300;    // ms
const DAMAGE_TEXT_DURATION = 1000;  // ms
const MOVE_DURATION = 500;   // ms
const DIE_DURATION = 500;    // ms
const HARVEST_DURATION = 1000;// ms
const HIVE_FADE_DURATION = 500;// ms

const insectElems = new Map();
let actionTimer = null;
let actionBusy = false;
let actionOver = false;
let game_result = null;      // true = ants won, false = ants lost
let lastSnapshotSeq = -1;
let pendingSnapshot = null;

// the frontend drives the beat: the bar fills up until the next action fires
let action_started_at = 0;
let timer_raf = null;

let play_speed = 1;
const PLAY_SPEEDS = [1, 1.25, 1.5, 2];

function timer_start(at) {
    action_started_at = at;
    timer_paint(0);
    if(timer_raf === null) timer_raf = requestAnimationFrame(timer_frame);
}

function timer_frame() {
    timer_raf = null;
    const progress = Math.min(1, (performance.now() - action_started_at) / get_action_waiting());
    timer_paint(progress);
    if(progress < 1) timer_raf = requestAnimationFrame(timer_frame);
}

function timer_stop(progress) {
    if(timer_raf !== null) cancelAnimationFrame(timer_raf);
    timer_raf = null;
    timer_paint(progress);
}

function timer_paint(progress) {
    if(timer_el) timer_el.style.setProperty("--p", progress);
}

function get_action_waiting() {
    // the player can only act on their own turn, so the bee phase just needs
    // enough time to read what happened
    return (my_turn ? ANT_ACTION_WAITING_BASE : BEE_ACTION_WAITING_BASE) / play_speed;
}

const speed_btn = document.querySelector(".hud-speed-btn");
const skip_btn = document.querySelector(".hud-skip-btn");

function set_play_speed(next) {
    const now = performance.now();
    const before = get_action_waiting();
    const progress = before > 0 ? Math.min(1, (now - action_started_at) / before) : 0;

    play_speed = next;
    const after = get_action_waiting();

    // keep the dial where it is: same fraction of the new round length
    action_started_at = now - progress * after;
    if(speed_btn) speed_btn.textContent = `${play_speed}x`;

    if(!actionBusy && !actionOver) {
        clearTimeout(actionTimer);
        actionTimer = setTimeout(action_run, Math.max(0, after * (1 - progress)));
    }
    if(!actionOver && timer_raf === null) timer_raf = requestAnimationFrame(timer_frame);
}

if(speed_btn) {
    speed_btn.addEventListener("click", () => {
        const i = PLAY_SPEEDS.indexOf(play_speed);
        set_play_speed(PLAY_SPEEDS[(i + 1) % PLAY_SPEEDS.length]);
    });
}

// skip the remaining wait, or cut a running animation short
let skipping = false;

function skip_to_next_action() {
    if(actionOver) return;
    if(actionBusy) {
        skipping = true;
        cancel_all_animations();   // aborts the awaits inside play_events
        return;
    }
    clearTimeout(actionTimer);
    action_run();
}

if(skip_btn) skip_btn.addEventListener("click", skip_to_next_action);

// board has two extra columns: base on the left, hive on the right
let tunnelCols = 0;
let centerRow = 1;

const dyingIds = new Set();

function cell_col(col, place) {
    if(place === "base") return 1;
    if(place === "hive") return tunnelCols + 2;
    return Number(col) + 2;
}

function cell_row(row, place) {
    // if(place === "base" || place === "hive") return "var(--center-row)";
    return Number(row) + 1;
}

const runningAnims = new Set();
const transientElems = new Set();

function ant_at(row, col) {
    for (const el of insectElems.values()) {
        if(el.dataset.isAnt === "true" &&
           Number(el.dataset.row) === row && Number(el.dataset.col) === col) return el;
    }
    return null;
}

board.addEventListener('click', (e) => {
    const place = e.target.closest('.place');

    if(!place) return;
    const place_data = {
        kind: place.dataset.kind,
        row: Number(place.dataset.row),
        col: Number(place.dataset.col),
    }

    if(!my_turn) return;

    if(to_remove) {
        remove(place_data);
    } else {
        if(to_deploy === null) return;
        deploy(place_data, to_deploy);
    }
});

// right-click removes the ant in that cell, under the same turn rules
board.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    if(!my_turn || actionOver) return;

    const place = e.target.closest('.place');
    if(!place) return;

    const row = Number(place.dataset.row);
    const col = Number(place.dataset.col);
    if(!ant_at(row, col)) return;   // nothing to remove, skip the round trip
    remove({ kind: place.dataset.kind, row: row, col: col });
});

// a faint copy of the ant the next click would place, drawn in the hovered cell
let ghost = null;
let ghost_place = null;

function ghost_hide() {
    ghost_place = null;
    if(ghost !== null && ghost.parentElement !== null) ghost.remove();
}

function ghost_show(place) {
    if(ghost === null) {
        ghost = document.createElement("div");
        ghost.className = "insect ghost";
    }
    ghost.style.setProperty("--row", place.style.getPropertyValue("--row"));
    ghost.style.setProperty("--col", place.style.getPropertyValue("--col"));
    ghost.style.setProperty("--img", get_insect_img(true, to_deploy));
    if(ghost.parentElement !== board) board.appendChild(ghost);
}

board.addEventListener("pointermove", (e) => {
    const place = e.target.closest(".place");
    if(place === null || to_deploy === null || actionOver) {
        ghost_hide();
        return;
    }
    if(place === ghost_place) return;   // same cell, nothing to redraw
    ghost_place = place;
    ghost_show(place);
});

board.addEventListener("pointerleave", ghost_hide);

selector.addEventListener('click', (e) => {
    if(actionOver) return;

    const item = e.target.closest('.selector-item');
    if(!item) return;
    if(item.dataset.remove === "false") {
        to_deploy = (to_deploy === item.dataset.name) ? null : item.dataset.name;
        to_remove = false;
    } else {
        to_deploy = null;
        to_remove = !to_remove;
    }
    selector_set_selected(to_deploy, to_remove);
});

function build_board(data) {
    board.innerHTML = "";
    const dimensions = data.dimensions;

    tunnelCols = Number(dimensions[1]);
    centerRow = Math.ceil(Number(dimensions[0]) / 2);

    board.style.setProperty("--rows", dimensions[0]);
    board.style.setProperty("--cols", tunnelCols + 2);
    board.style.setProperty("--center-row", centerRow);

    for(const place_data of data.places) {
        if(place_data.kind !== "tunnel" && place_data.kind !== "water") continue;

        const place = document.createElement("div");
        place.className = "place";
        place.style.setProperty("--row", Number(place_data.row) + 1);
        place.style.setProperty("--col", cell_col(place_data.col, place_data.kind));

        const file_name = place_data.kind === "tunnel" ? String(place_data.col % 3) : "wet";
        place.style.setProperty("--img", `url("/assets/tiles/${file_name}.png")`);

        place.dataset.kind = place_data.kind;
        place.dataset.row = place_data.row;
        place.dataset.col = place_data.col;

        board.appendChild(place);
    }

    // the base column is tiled too, but it takes no ant and has no place under it
    for(let row = 1; row <= Number(dimensions[0]); row++) {
        const end = document.createElement("div");
        end.className = "place place-end";
        end.style.setProperty("--row", row);
        end.style.setProperty("--col", cell_col(0, "base"));
        end.style.setProperty("--img", 'url("/assets/tiles/end.png")');
        board.appendChild(end);
    }

    // const base_zone = document.createElement("div");
    // base_zone.className = "base-zone";
    // const base_art = document.createElement("div");
    // base_art.className = "zone-art";
    // base_zone.appendChild(base_art);
    // board.appendChild(base_zone);

    const hive_zone = document.createElement("div");
    hive_zone.className = "hive-zone";

    const hive_art = document.createElement("div");
    hive_art.className = "zone-art";
    hive_zone.appendChild(hive_art);

    const hive_body = document.createElement("div");
    hive_body.className = "hive-body";

    const hive_count = document.createElement("div");
    hive_count.className = "hive-count";
    hive_count.textContent = "x0";

    const hive_label = document.createElement("div");
    hive_label.className = "hive-label";
    hive_label.textContent = "BEES";

    hive_body.appendChild(hive_count);
    hive_body.appendChild(hive_label);
    hive_zone.appendChild(hive_body);
    board.appendChild(hive_zone);
}

function get_insect_img(is_ant, name) {
    const folder = is_ant ? "ants" : "bees";
    return `url("/assets/${folder}/${name}.gif")`;
}

function build_selector(data, has_remove=false) {
    selector.innerHTML = ""
    for(const [name, cost] of Object.entries(data)) {        
        const selector_item_cost = document.createElement("div");
        selector_item_cost.className = "selector-item-cost";
        selector_item_cost.innerHTML = `(${cost})`
        const selector_item_name = document.createElement("div");

        selector_item_name.className = "selector-item-name";
        selector_item_name.innerHTML = name;

        const selector_item_img = document.createElement("div");
        selector_item_img.className = "selector-item-img";
        selector_item_img.style.setProperty("--img", get_insect_img(true, name))

        const selector_item = document.createElement("div");
        selector_item.className = "selector-item";
        selector_item.dataset.name = name;
        selector_item.dataset.cost = cost;
        selector_item.dataset.available = false;
        selector_item.dataset.remove = false;
        selector_item.dataset.selected = false;
        selector_item.appendChild(selector_item_cost);
        selector_item.appendChild(selector_item_img);
        selector_item.appendChild(selector_item_name);

        selector.appendChild(selector_item)
    }
    if(has_remove) {
        const remove_cost = document.createElement("div");
        remove_cost.className = "selector-item-cost";
        remove_cost.innerHTML = ""
        const remove_name = document.createElement("div");

        remove_name.className = "selector-item-name";
        remove_name.innerHTML = "REMOVE";

        const remove_img = document.createElement("div");
        remove_img.className = "selector-item-img";
        remove_img.style.setProperty("--img", null);

        const remove_item = document.createElement("div");
        remove_item.className = "selector-item";
        remove_item.dataset.remove = true;
        remove_item.dataset.cost = 0;
        remove_item.dataset.available = false;
        remove_item.dataset.selected = false;
        remove_item.appendChild(remove_cost);
        remove_item.appendChild(remove_img);
        remove_item.appendChild(remove_name);

        selector.appendChild(remove_item)
    }
}

function selector_set_available(food, deploysLeft) {
    const out_of_deploys = deploysLeft !== null && deploysLeft !== undefined && deploysLeft <= 0;
    for (const item of document.getElementsByClassName("selector-item")) {
        const is_remove = item.dataset.remove === "true";
        item.dataset.available = !actionOver && my_turn
                                 && food >= Number(item.dataset.cost)
                                 && (is_remove || !out_of_deploys);
    }
}

function selector_disable_all() {
    for (const item of document.getElementsByClassName("selector-item")) {
        item.dataset.available = false;
    }
}

// ported from the legacy showEndGameAlert
function game_over(win) {
    if(game_over_el) {
        game_over_el.textContent = win ? "You Won!" : "You Lost!";
        game_over_el.dataset.result = win ? "win" : "lose";
    }
    document.body.classList.add("game-over");

    to_deploy = null;
    selector_set_selected(null, false);
    selector_disable_all();
    ghost_hide();
}

function selector_set_selected(target, remove) {
    for (const item of document.getElementsByClassName("selector-item")) {
        if(item.dataset.remove === "true") {
            item.dataset.selected = remove;
        } else {
            item.dataset.selected = target === item.dataset.name;
        }
    }
    ghost_hide();   // the selection changed, the next hover draws it again
}

function apply_snapshot(snapshot) {
    if(!snapshot) return;
    const seq = Number(snapshot.seq);
    if(seq <= lastSnapshotSeq) return;   // a newer state already landed
    lastSnapshotSeq = seq;
    apply_snapshot_hud(snapshot)
    apply_snapshot_insects(snapshot)
    apply_snapshot_boss(snapshot)
}

function apply_snapshot_hud(snapshot) {
    if(!snapshot) return;
    document.querySelector(".hud-food").textContent = `Food: ${snapshot.food}`;
    document.querySelector(".hud-turn").textContent = `Turn: ${snapshot.turn}`;

    const deploys_el = document.querySelector(".hud-deploys");
    if(deploys_el) {
        const limit = snapshot.maxDeploys;
        if(limit === null || limit === undefined) {
            deploys_el.hidden = true;
        } else {
            deploys_el.hidden = false;
            deploys_el.textContent = `Deploys: ${snapshot.deploysLeft}/${limit}`;
        }
    }

    const hive_count = document.querySelector(".hive-count");
    if(hive_count) hive_count.textContent = `x${snapshot.hive ?? 0}`;

    // who acts once the bar is full, and the dial takes that side's colour
    if(snapshot.next) {
        my_turn = snapshot.next !== "bee";
        if(timer_text_el) timer_text_el.textContent = snapshot.next;
        // it has to land on the dial itself: its own --color beats an inherited one
        if(timer_dial_el) {
            timer_dial_el.style.setProperty("--color",
                snapshot.next === "ant" ? "var(--color-ant)" : "var(--color-bee)");
        }
    }

    selector_set_available(snapshot.food, snapshot.deploysLeft)
}

function apply_snapshot_insects(snapshot) {
    if(!snapshot) return;
    if(actionOver) return;   // the board is frozen once the game ends
    const seen_id = new Set();
    for(const [id, data] of Object.entries(snapshot.insects)) {
        seen_id.add(id);
        let elem = insectElems.get(id);
        if(!elem) {
            make_insect(id, data);
        } else {
            update_insect(elem, data);
        }
    }
    for(const [id, elem] of insectElems) {
        if(!seen_id.has(id) && !dyingIds.has(id)) remove_insect(elem);
    }
    reassign_slots(snapshot);
}

// the boss gets a bar of its own: one pip per point needs more room than a cell
function apply_snapshot_boss(snapshot) {
    const boss = Object.values(snapshot.insects).find(data => data.tags.includes("boss"));
    if(boss === undefined) {
        boss_bar.hidden = true;
        return;
    }
    paint_boss_bar(boss.health, boss.maxHealth);
}

function paint_boss_bar(health, maxHealth) {
    const max = Number(maxHealth) || 1;
    boss_bar.hidden = false;
    boss_bar.style.setProperty("--boss-max", max);
    boss_bar_fill.style.setProperty("--fill", clamp(health / max, 0, 1));
}

function remove_insect(elem) {
    elem.remove();
    insectElems.delete(elem.dataset.id);
}

function make_insect(id, data) {
    const insect = document.createElement("div");
    insect.className = "insect";
    set_insect_img(insect, data)
    insect.dataset.id = String(id);
    insect.dataset.kind = String(data.kind);
    insect.dataset.isAnt = Boolean(data.isAnt);
    insect.dataset.isContainer = Boolean(data.tags.includes("container"));
    insect.dataset.maxHealth = Number(data.maxHealth);
    if(Boolean(data.randomlized_offset)) {
        insect.style.setProperty("--spr-xoff", `${-25 + 50 * Math.random()}%`);
        insect.style.setProperty("--spr-yoff", `${-25 + 50 * Math.random()}%`);
    }

    set_insect_cell(insect, data);
    set_insect_status_condition(insect, data)

    const health_bar = document.createElement("div");
    health_bar.className = "insect-health";
    insect.appendChild(health_bar);
    show_insect_health(insect);

    set_insect_health(insect, Number(data.health));

    insectElems.set(String(id), insect);
    board.appendChild(insect);
    return insect;
}

function update_insect(elem, data) {
    set_insect_cell(elem, data);
    set_insect_health(elem, Number(data.health));
    set_insect_status_condition(elem, data);
    set_insect_img(elem, data);
}

function set_insect_img(elem, data) {
    const chewing = data.tags.includes("chewing");
    if(elem.dataset.isChewing === Boolean(chewing)) return;
    elem.dataset.isChewing = Boolean(chewing);
    elem.style.setProperty("--img", chewing
        ? `url("/assets/ants/HungryChewing.gif")`
        : get_insect_img(Boolean(data.isAnt), data.kind));
}

function set_insect_cell(elem, data) {
    const place = data.place || "tunnel";
    elem.style.setProperty("--row", cell_row(data.row, place));
    elem.style.setProperty("--col", cell_col(data.col, place));
    elem.dataset.row = Number(data.row);
    elem.dataset.col = Number(data.col);
    elem.dataset.place = place;
}

function set_insect_status_condition(elem, data) {
    // forced, not toggled: the snapshot re-applies the same value every phase
    // and an unforced toggle would flip the class off right after the event set it
    elem.classList.toggle("slow", data.tags.includes("slow"));
    elem.classList.toggle("scare", data.tags.includes("scare"));
    elem.classList.toggle("poison", data.tags.includes("poison"));
    elem.classList.toggle("buffed", data.tags.includes("buffed"));
    elem.classList.toggle("boss", data.tags.includes("boss"));
    elem.classList.toggle("queen", data.tags.includes("queen"));

    const wax = data.tags.find(t => t.startsWith("wax"));
    elem.classList.toggle("wax", wax !== undefined);
    if(wax) {
        const [layer, layer_max] = wax.split("_").slice(-2).map(Number);
        elem.style.setProperty("--wax-ratio", layer / layer_max);
    }
}

// insects sharing a cell share the same box, so give each one a stacking slot
function reassign_slots(snapshot) {
    const buckets = new Map();
    for(const [id, data] of Object.entries(snapshot.insects)) {
        const key = `${data.place || "tunnel"}_${data.row}_${data.col}`;
        if(!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(id);
    }

    for(const ids of buckets.values()) {
        ids.sort((a, b) => Number(a) - Number(b));   // stable: don't reshuffle every turn
        for(let slot = 0; slot < ids.length; slot++) {
            const elem = insectElems.get(ids[slot]);
            if(elem) elem.style.setProperty("--slot", slot);
        }
    }
}

function show_insect_health(elem, ttl=HEALTH_BAR_TTL) {
    const health_bar = elem.querySelector(".insect-health");
    // the queen keeps hers up: she is the thing the bees are here to kill
    const permanent = elem.classList.contains("queen");
    health_bar.dataset.ttl = ttl;
    health_bar.classList.toggle("is-visible", permanent || ttl > 0);
}

function tick_insect_health(elem) {
    const health_bar = elem.querySelector(".insect-health");
    const ttl = Number(health_bar.dataset.ttl ?? 0);
    show_insect_health(elem, ttl - 1);
}

function set_insect_health(elem, health) {
    if(Number(elem.dataset.health) === health) return;
    elem.dataset.health = health;

    const max_health = Number(elem.dataset.maxHealth);
    const health_bar = elem.querySelector(".insect-health");
    health_bar.innerHTML = "";

    for(let i = 0; i < max_health; i++) {
        const health_fill = document.createElement("div");
        health_fill.className = "insect-health-fill";
        health_fill.style.setProperty("--fill", Math.max(0, Math.min(1, health - i)));
        health_fill.style.setProperty("--color", elem.dataset.isAnt === "true" ? "var(--color-ant)" : "var(--color-bee)");
        health_bar.appendChild(health_fill);
    }
}

async function new_game(level) {
    const res = await fetch("/api/new", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(level ?? {}),
    });
    const data = await res.json();
    if (!data.ok) return console.error(data.error);

    clearTimeout(actionTimer);
    cancel_all_animations();
    actionOver = false;
    game_result = null;
    document.body.classList.remove("game-over");
    document.body.classList.remove("menu");
    lastSnapshotSeq = -1;
    pendingSnapshot = null;
    if(bgm) bgm.play()
    build_board(data.board);
    build_selector(data.availableAnts);
    apply_snapshot(data.snapshot);
    action_run();
}

async function action_run() {
    if(actionBusy || actionOver) return;
    actionBusy = true;

    const started = performance.now();
    timer_start(performance.now());
    let snapshot = null;
    try {
        const res = await fetch("/api/action", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await res.json().catch(() => ({
            ok: false, reason: "http", error: `HTTP ${res.status}`,
        }));

        if(!data.ok) {
            snapshot = data.snapshot;   // final state before the game stops
            actionOver = true;
            return;
        }

        cancel_all_animations();
        for(const elem of insectElems.values()) tick_insect_health(elem);
        apply_snapshot_hud(data.snapshot);
        await play_events(data.events);
        snapshot = data.snapshot;
        actionOver = Boolean(data.over);
        if(actionOver) game_result = Boolean(data.win);
    } catch(e) {
        // the server went away mid-round: stop the loop instead of retrying forever
        console.warn("action failed:", e);
        actionOver = true;
    } finally {
        // deploy during the animation stores its snapshot here; it is newer
        // than this round's, so it must be applied first
        const pending = pendingSnapshot;
        pendingSnapshot = null;
        apply_snapshot(pending);
        apply_snapshot(snapshot);

        actionBusy = false;
        const skipped = skipping;
        skipping = false;
        if(actionOver) {
            timer_stop(0);
            if(game_result !== null) game_over(game_result);
        } else {
            let rest = get_action_waiting() - (performance.now() - action_started_at);
            if(skipped) rest = 0;   // the player asked to jump straight to the next action
            clearTimeout(actionTimer);
            actionTimer = setTimeout(action_run, Math.max(0, rest));
        }
    }
}

async function deploy(place, ant_type_name) {
    if(actionOver || !my_turn) return false;

    const res = await fetch("/api/deploy", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ant: ant_type_name, place: place })
    });

    const data = await res.json().catch(() => ({
        ok: false, reason: "http", error: `HTTP ${res.status}`,
    }));

    if(!data.ok) {
        console.warn("deploy rejected:", data.reason, data.error);
        return false;
    }
    play_events(data.events);

    // an action is playing: let it finish, its snapshot is applied at the end
    if(actionBusy) {
        queue_snapshot(data.snapshot);
    } else {
        apply_snapshot(data.snapshot);
    }
    return true;
}

async function remove(place) {
    if(actionOver || !my_turn) return false;

    const res = await fetch("/api/remove", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ place: place })
    });

    const data = await res.json().catch(() => ({
        ok: false, reason: "http", error: `HTTP ${res.status}`,
    }));

    if(!data.ok) {
        console.warn("remove rejected:", data.reason, data.error);
        return false;
    }
    play_events(data.events);

    if(actionBusy) {
        queue_snapshot(data.snapshot);
    } else {
        apply_snapshot(data.snapshot);
    }
    return true;
}

async function play_events(events) {
    if(!events || !events.length) return;
    // every bullet uses THROW_DURATION, so awaiting one waits for all of them
    const shots = [];
    for(const ev of events) {
        if(ev.event === "deploy") handle_event(ev);
        if(ev.event === "remove") handle_event(ev);
        if(ev.event === "harvest") handle_event(ev);
        if(ev.event === "buffed") handle_event(ev);
        if(ev.event === "throw_at") shots.push(ev_throw_at(ev));
    }
    const landed = Promise.all(shots);

    try {
        const anim_list2 = []
        for(const ev of events) {
            if(ev.event === "deploy") continue;
            if(ev.event === "remove") continue;
            if(ev.event === "harvest") continue;
            if(ev.event === "throw_at") continue;
            // a leaf in this batch holds back every bit of damage, not just its own,
            // so that hit order on screen matches hit order in the game.
            // debuffs deal no damage, so they need the same wait
            if((ev.event === "reduce_health" || ev.event === "slow" || ev.event === "scare" || ev.event === "rh_wax") && shots.length) await landed;
            anim_list2.push(handle_event(ev));
        }
        // a throw that lands neither damage nor a debuff still waits for its leaf
        if(shots.length) await landed;
        await Promise.all(anim_list2);
    } catch(e) {
        if(e && e.name !== "AbortError") console.warn("animation failed", e);
    }
}

async function handle_event(ev) {
    switch(ev.event) {
        case "hive_fade": return ev_hive_fade(ev);
        case "deploy": return ev_deploy(ev);
        case "remove": return ev_remove(ev);
        case "reduce_health": return ev_reduce_health(ev);
        case "throw_at": return ev_throw_at(ev);
        case "harvest": return ev_harvest(ev);
        case "move": return ev_move(ev);
        case "die": return ev_die(ev);
        case "slow": return ev_status(ev, "slow");
        case "scare": return ev_status(ev, "scare");
        case "poison": return ev_status(ev, "poison");
        case "buffed": return ev_status(ev, "buffed");
        case "wax": return ev_wax(ev);
        case "rh_wax": return ev_wax(ev);
        case "feed": return ev_feed(ev);
    }
}

function ev_hive_fade(ev) {
    const hive_zone = document.querySelector(".hive-zone")
    const anim = hive_zone.animate([
        { opacity: "100%", transform: "translate(0, 0) rotate(0deg)",  },
        { opacity: "0%", transform: "translate(5cqi, 5cqi) rotate(10deg)" },
    ], { duration: HIVE_FADE_DURATION / play_speed, easing: "ease-out" });
    return anim.finished.then(() => {
        anim.commitStyles();
        anim.cancel();
    });
}

function ev_deploy(ev) {
    make_insect(ev.id, ev.info);
}

function ev_remove(ev) {
    const elem = insectElems.get(String(ev.id));
    if(!elem) return Promise.resolve();
    remove_insect(elem);
}

function ev_status(ev, name) {
    const elem = insectElems.get(String(ev.id));
    if(elem) elem.classList.add(name);
}

function ev_wax(ev) {
    const elem = insectElems.get(String(ev.id));
    if(elem) {
        const layer = Number(ev.layer);
        const layer_max = Number(ev.layer_max);
        elem.classList.toggle("wax", layer > 0);
        if(layer > 0) {
            elem.style.setProperty("--wax-ratio", layer / layer_max);
        }
    }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function ev_harvest(ev) {
    const src = insectElems.get(String(ev.source));
    if(!src) return Promise.resolve();

    const food = document.createElement("div")
    food.className = "food"
    food.style.setProperty("--row", src.style.getPropertyValue("--row"));
    food.style.setProperty("--col", src.style.getPropertyValue("--col"));
    board.appendChild(food);

    const frames = [];

    const STEPS = 8;
    for(let i = 0; i <= STEPS; i++) {
        const t = i / STEPS;
        const y = -0.3 * t;
        const scale = Math.pow(clamp(t / 0.4, 0, 1), 1/2);
        const opacity = Math.pow(clamp(t / 0.4, 0, 1), 1/2) * 0.7 * clamp(1 - (t - 0.6) / 0.4, 0, 1);

        frames.push({
            translate: `0 calc(${y} * (100% + var(--row-gap)))`,
            offset: t,
            opacity: opacity,
            scale: scale * 0.75
        });
    }

    const anim = food.animate(frames, {
        duration: HARVEST_DURATION / play_speed,
        easing: "linear",
        fill: "forwards",
    });
    track(anim, food);

    return anim.finished.catch(() => {}).finally(() => food.remove());
}

function ev_throw_at(ev) {
    const src = insectElems.get(String(ev.source));
    if(!src) return Promise.resolve();

    const dst = insectElems.get(String(ev.target));
    if(!dst) return Promise.resolve();

    const drow = Number(dst.dataset.row) - Number(src.dataset.row);
    const dcol = Number(dst.dataset.col) - Number(src.dataset.col);

    const bullet = document.createElement("div");
    bullet.className = "bullet";
    bullet.style.setProperty("--row", src.style.getPropertyValue("--row"));
    bullet.style.setProperty("--col", src.style.getPropertyValue("--col"));
    bullet.style.setProperty("--damage", Number(ev.damage));
    let img;
    switch(ev.source_kind) {
        case "Slow": img = "url('/assets/leaf-slow.png')"; break;
        case "Scary": img = "url('/assets/leaf-scary.png')"; break;
        default: img = "url('/assets/leaf.png')"
    }
    bullet.style.setProperty("--img", img);
    board.appendChild(bullet);
    
    const STEPS = 8;
    const ARC = 1;

    const frames = [];
    const angle_offset = Math.random() * 360;
    for(let i = 0; i <= STEPS; i++) {
        const t = i / STEPS;
        const x = dcol * t;
        const y = drow * t - 4 * t * (1 - t) * ARC;

        frames.push({
            translate: `calc(${x} * (100% + var(--col-gap))) calc(${y} * (100% + var(--row-gap)))`,
            offset: t,
            rotate: `${t * 180 + angle_offset}deg`,
        });
    }

    const anim = bullet.animate(frames, {
        duration: THROW_DURATION / play_speed,
        easing: "linear",
        fill: "forwards",
    });

    track(anim, bullet);
    return anim.finished.catch(() => {});
}

function ev_reduce_health(ev) {
    const insect = insectElems.get(String(ev.id));
    if(!insect) return Promise.resolve();
    set_insect_health(insect, ev.health);
    show_insect_health(insect);
    // the hud bar has to move on the same frame as the hit, not one snapshot later
    if(insect.classList.contains("boss")) paint_boss_bar(ev.health, insect.dataset.maxHealth);
    show_damage_number(insect, ev.amount);
    return flash_hit(insect);
}

function ev_feed(ev) {
    const insect = insectElems.get(String(ev.id));
    if(!insect) return Promise.resolve();
    if(insect.classList.contains("boss")) paint_boss_bar(ev.health, insect.dataset.maxHealth);
    return flash_hit(insect, true);
}

function ev_move(ev) {
    let insect = insectElems.get(String(ev.id));
    if(!insect && ev.info) {
        // first time on screen: coming from the hive starts at its own cell,
        // anything else starts where the move began so the slide is visible
        const start = (ev.fromPlace && ev.fromPlace !== "hive")
            ? { ...ev.info, place: ev.fromPlace, row: ev.old[0], col: ev.old[1] }
            : ev.info;
        insect = make_insect(ev.id, start);
    }
    if(!insect) return Promise.resolve();

    for(const a of insect.getAnimations()) a.cancel();

    // entering from the hive: fade in from the right edge of its own cell
    if(ev.fromPlace === "hive") {
        const anim = insect.animate([
            { translate: "100% 0", opacity: 0 },
            { translate: "0% 0", opacity: 1 },
        ], { duration: MOVE_DURATION / play_speed, easing: "ease-out" });
        track(anim);
        return anim.finished.catch(() => {});
    }

    // scared all the way back into the hive: slide right, then fade out
    if(ev.toPlace === "hive") {
        const anim = insect.animate([
            { translate: "0 0", opacity: 1 },
            { translate: "calc(100% + var(--col-gap)) 0", opacity: 0 },
        ], { duration: MOVE_DURATION / play_speed, easing: "ease-in" });
        track(anim);
        return anim.finished.catch(() => {}).then(() => remove_insect(insect));
    }

    
    const intoBase = ev.toPlace === "base";
    const newRow = intoBase ? Number(insect.dataset.row) : Number(ev.new[0]);
    const newCol = intoBase ? 1 : Number(ev.new[1]);
    const drow = intoBase ? 0 : newRow - Number(insect.dataset.row);
    const dcol = intoBase ? -1 - Number(insect.dataset.col) : newCol - Number(insect.dataset.col);
    const shift = `calc(${dcol} * (100% + var(--col-gap))) calc(${drow} * (100% + var(--row-gap)))`;

    // the bee that reaches the home base ends the game: walk it in, then fade out
    // if(intoBase) {
    //     const anim = insect.animate([
    //         { translate: "0 0", opacity: 1 },
    //         { translate: shift, opacity: 1, offset: 0.7 },
    //         { translate: shift, opacity: 0 },
    //     ], { duration: MOVE_DURATION, easing: "ease-in" });
    //     return anim.finished.catch(() => {}).then(() => remove_insect(insect));
    // }

    const anim = insect.animate([
        { translate: "0 0" },
        { translate: shift },
    ], { duration: MOVE_DURATION / play_speed, easing: "ease-in-out" });
    track(anim);

    return anim.finished.catch(() => {}).then(() => {
        anim.cancel();
        set_insect_cell(insect, { row: newRow, col: newCol, place: ev.toPlace });
    });
}

function ev_die(ev) {
    const insect = insectElems.get(String(ev.id));
    if(!insect) return Promise.resolve();

    const anim = insect.animate([
        { opacity: "100%" },
        { opacity: "0%" },
    ], { duration: DIE_DURATION / play_speed, easing: "ease-out" });

    // tracked so a skip can cut the fade short; the chain below still tidies up
    track(anim, insect);
    const id = String(ev.id);
    dyingIds.add(id);
    return anim.finished.catch(() => {}).then(() => {
        anim.cancel();
        dyingIds.delete(id);
        remove_insect(insect);
    });
}

function show_damage_number(insect, amount) {
    if(!(amount > 0)) return;

    const label = document.createElement("div");
    label.className = "insect-damage";
    label.textContent = round_damage(amount);
    insect.appendChild(label);

    const anim = label.animate([
        { opacity: 0, translate: "80% 30%" },
        { opacity: 1, translate: "80% 0%", offset: 0.2 },
        { opacity: 1, translate: "80% -30%", offset: 0.75 },
        { opacity: 0, translate: "80% -60%" },
    ], { duration: DAMAGE_TEXT_DURATION / play_speed, easing: "ease-out", fill: "forwards" });
    track(anim, label);

    anim.finished.catch(() => {}).finally(() => label.remove());
}

function round_damage(amount) {
    return Number(amount.toFixed(2)).toString();
}

function queue_snapshot(snapshot) {
    if(!snapshot) return;
    apply_snapshot_hud(snapshot);
    const seq = Number(snapshot.seq);
    if(!pendingSnapshot || seq > Number(pendingSnapshot.seq)) {
        pendingSnapshot = snapshot;
    }
}

function flash_hit(insect, recover=false) {
    const hit = document.createElement("div");
    hit.className = "insect-hit";
    hit.classList.toggle("recover", recover)
    insect.appendChild(hit);

    const anim = hit.animate(
        [{ opacity: 1 }, { opacity: 0 }],
        { duration: HIT_DURATION / play_speed, easing: "ease-out", fill: "forwards" }
    );

    track(anim, hit);
    return anim.finished.catch(() => {});
}

function track(anim, el) {
    runningAnims.add(anim);
    if(el) transientElems.add(el);
    anim.finished.catch(() => {}).finally(() => {
        runningAnims.delete(anim);
        if(el) { el.remove(); transientElems.delete(el); }
    });
    return anim;
}

function cancel_all_animations() {
    for(const anim of runningAnims) {
        try { anim.cancel(); } catch(e) { /* already finished */ }
    }
    runningAnims.clear();
    for(const el of transientElems) el.remove();
    transientElems.clear();
}

// ---- menu ----

function build_level_grid(names) {
    const grid = document.querySelector(".level-grid");
    if(!grid) return;
    grid.innerHTML = "";
    names.forEach((name, i) => {
        const btn = document.createElement("button");
        btn.className = "menu-button level-button";
        btn.textContent = String(i + 1);
        btn.addEventListener("click", () => new_game({ level: name }));
        grid.appendChild(btn);
    });

    // a short last row is centred rather than hugging the left edge
    const cols = Number(getComputedStyle(grid).getPropertyValue("--levels-per-row")) || 5;
    const leftover = names.length % cols;
    if(leftover > 0) {
        const first = grid.children[names.length - leftover];
        first.style.gridColumnStart = String(Math.floor((cols - leftover) / 2) + 1);
    }
}

fetch("/api/config").then(r => r.json()).then(cfg => {
    if(!cfg.levelPage) {
        // no level page: the difficulty came from the command line
        document.body.classList.remove("menu");
        new_game({});
        return;
    }

    // arriving from the workshop: jump straight into the picked level
    const wanted = new URLSearchParams(location.search).get("level");
    if(wanted) {
        new_game({ levelFile: wanted });
        return;
    }

    build_level_grid(cfg.builtinLevels || []);

    const custom_start = document.querySelector(".menu-start-custom");
    if(custom_start) {
        custom_start.addEventListener("click", () => new_game({ level: cfg.customLevel }));
    }

    const workshop_link = document.querySelector(".menu-workshop");
    if(workshop_link) {
        workshop_link.hidden = false;
        workshop_link.addEventListener("click", () => { location.href = "/workshop.html"; });
    }
}).catch(() => {});