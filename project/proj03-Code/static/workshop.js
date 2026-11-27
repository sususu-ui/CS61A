const local_list = document.querySelector('[data-list="local"]');
const remote_list = document.querySelector('[data-list="remote"]');
const local_pager = document.querySelector('[data-pager="local"]');
const remote_pager = document.querySelector('[data-pager="remote"]');
const signin_button = document.querySelector('[data-action="signin"]');
const signout_button = document.querySelector('[data-action="signout"]');
const publish_button = document.querySelector('[data-action="publish"]');
const identity_label = document.querySelector(".ws-identity");
const list_view = document.querySelector('[data-view="lists"]');
const publish_view = document.querySelector('[data-view="publish"]');
const preview_box = document.querySelector("[data-preview]");
const publish_form = document.querySelector('[data-form="publish"]');
const mine_filter = document.querySelector('[data-action="mine-filter"]');
const mine_only_box = document.querySelector('[data-action="mine-only"]');
const search_form = document.querySelector('[data-form="search"]');
const search_field_box = document.querySelector('[data-action="search-field"]');
const search_text_box = document.querySelector('[data-action="search-text"]');
const search_result = document.querySelector('[data-result="remote"]');
const sort_box = document.querySelector('[data-action="sort"]');

let config = {};
let signed_in = false;
let username = "";
let my_user_id = "";
let mine_only = false;
// the last submit; paging and the empty note both read this
let search = { field: "title", text: "" };

const PAGE_SIZE = 15;      // rows per page, both columns
let local_page = 1;
let remote_page = 1;
let local_levels = [];     // the folder is small, so it is fetched once and sliced here

async function api(method, path, body) {
    const headers = {};
    if(body !== undefined) headers["Content-Type"] = "application/json";

    const res = await fetch(path, {
        method: method,
        headers: headers,
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({
        ok: false, reason: "http", error: `HTTP ${res.status}`,
    }));
    return data;
}

function button(label, className, onclick) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = className;
    el.textContent = label;
    el.addEventListener("click", onclick);
    return el;
}

function note(text) {
    const el = document.createElement("p");
    el.className = "ws-note";
    el.textContent = text;
    return el;
}

// ---- rows ----

function format_date(seconds) {
    const value = Number(seconds);
    if(!Number.isFinite(value) || value <= 0) return "";
    const d = new Date(value * 1000);
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
        `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function make_row(entry, side) {
    const row = document.createElement("article");
    row.className = "ws-row";
    row.dataset.id = entry.id;

    const head = document.createElement("div");
    head.className = "ws-row-head";

    const id = document.createElement("code");
    id.className = "ws-id";
    id.textContent = entry.id;
    // one click leaves the id selected, which is the only reason to aim at it
    id.addEventListener("click", event => {
        event.stopPropagation();
        const range = document.createRange();
        range.selectNodeContents(id);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    });

    const name = document.createElement("span");
    name.className = "ws-name";
    name.textContent = entry.name || "(untitled)";

    const author = document.createElement("span");
    author.className = "ws-author";
    author.textContent = entry.authorName || "unknown";

    const date = document.createElement("span");
    date.className = "ws-date";
    date.textContent = format_date(entry.createdAt);
    if(!date.textContent) date.hidden = true;

    const body = document.createElement("div");
    body.className = "ws-row-body";
    body.hidden = true;

    head.append(id, name, author, date);
    if(side === "remote") head.appendChild(make_like(entry));
    row.append(head, body);

    head.addEventListener("click", () => toggle_row(row, entry, side, body));
    return row;
}

function make_like(entry) {
    const el = document.createElement("button");
    el.type = "button";
    // the server says whether this account already liked it, so a reload keeps it
    el.className = entry.liked ? "ws-like ws-like-on" : "ws-like";
    el.disabled = !signed_in;
    el.title = signed_in ? "like this level" : "sign in to like levels";

    const heart = document.createElement("span");
    heart.className = "ws-like-heart";
    heart.textContent = "\u2764";
    const count = document.createElement("span");
    count.className = "ws-like-count";
    count.textContent = String(entry.likes || 0);

    el.append(heart, count);
    el.addEventListener("click", async event => {
        // the head toggles the row, and liking is not a way to open it
        event.stopPropagation();
        if(!signed_in) return;

        const next = !el.classList.contains("ws-like-on");
        const data = await api(next ? "POST" : "DELETE", "/api/workshop/likes/" + entry.id);
        if(!data.ok) {
            alert(data.error || "could not update the like");
            return;
        }
        // trust the answer: another tab may have voted in the meantime
        const level = data.level || {};
        entry.liked = level.liked ?? next;
        entry.likes = level.likes ?? entry.likes ?? 0;
        el.classList.toggle("ws-like-on", entry.liked);
        count.textContent = String(entry.likes);
    });
    return el;
}

function refresh_likes() {
    for(const el of document.querySelectorAll(".ws-like")) {
        el.disabled = !signed_in;
        el.title = signed_in ? "like this level" : "sign in to like levels";
    }
}

function close_open_rows(except) {
    for(const open of document.querySelectorAll(".ws-row-open")) {
        if(open === except) continue;
        open.classList.remove("ws-row-open");
        const panel = open.querySelector(".ws-row-body");
        if(panel) panel.hidden = true;
    }
}

async function toggle_row(row, entry, side, body) {
    if(row.classList.contains("ws-row-open")) {
        row.classList.remove("ws-row-open");
        body.hidden = true;
        return;
    }

    // one level at a time: opening a row folds whatever was open before
    close_open_rows(row);

    if(!body.dataset.filled) {
        body.appendChild(note("loading..."));
        const path = side === "local"
            ? "/api/workshop/downloads/" + entry.id
            : "/api/workshop/remote/" + entry.id;
        const data = await api("GET", path);
        body.innerHTML = "";
        if(!data.ok) {
            body.appendChild(note(data.error || "could not load this level"));
        } else {
            render_detail(body, data.level, side);
        }
        body.dataset.filled = "1";
    }

    row.classList.add("ws-row-open");
    body.hidden = false;
}

function add_fact(parent, term, value) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    parent.append(dt, dd);
}

// one character per cell so the shape reads at a glance: ~ is water, . is dry
function water_grid(dimensions, water) {
    const rows = Number(dimensions[0]);
    const cols = Number(dimensions[1]);
    if(!Number.isInteger(rows) || !Number.isInteger(cols) || rows <= 0 || cols <= 0) return "";

    const wet = new Set(water.map(p => `${p[0]},${p[1]}`));
    const lines = [];
    for(let r = 0; r < rows; r++) {
        let line = "";
        for(let c = 0; c < cols; c++) line += wet.has(`${r},${c}`) ? "~" : ".";
        lines.push(line);
    }
    return lines.join("\n");
}

function render_summary(parent, plain) {
    const facts = document.createElement("dl");
    facts.className = "ws-facts";
    const dimensions = plain.dimensions || [];
    const water = plain.water_positions || [];

    add_fact(facts, "Initial Food", String(plain.food_initial ?? "?"));
    add_fact(facts, "Deploys Limit",
        plain.max_deploys_per_turn === null || plain.max_deploys_per_turn === undefined
            ? "unlimited" : String(plain.max_deploys_per_turn));
    add_fact(facts, "Available Ants", (plain.available_ants || []).join(", ") || "-");
    add_fact(facts, "Dimensions", `${dimensions[0] ?? "?"} x ${dimensions[1] ?? "?"}`);
    parent.appendChild(facts);
    
    const map = document.createElement("pre");
    map.className = "ws-map";
    map.textContent = water_grid(dimensions, water);
    if(map.textContent) parent.appendChild(map);
    
    const waves = plain.waves || [];
    const list = document.createElement("ul");
    list.className = "ws-waves";
    if(waves.length) {
        for(const wave of waves) {
            const item = document.createElement("li");
            item.textContent = `t=${wave.time} ${wave.bee} (hp ${wave.health}) x${wave.count}`;
            list.appendChild(item);
        }
    } else {
        const item = document.createElement("li");
        item.textContent = "no waves";
        list.appendChild(item);
    }
    parent.appendChild(list);
}

function render_detail(body, record, side) {
    const plain = record.level || {};

    const desc = document.createElement("p");
    desc.className = "ws-desc";
    desc.textContent = record.description || "(no description)";
    body.appendChild(desc);

    render_summary(body, plain);

    const actions = document.createElement("div");
    actions.className = "ws-row-actions";
    body.appendChild(actions);

    if(side === "local") {
        actions.appendChild(button("Play", "ws-button", () => {
            location.href = "/?level=" + encodeURIComponent(record.id);
        }));
        actions.appendChild(button("Delete", "ws-button danger", async () => {
            const label = record.name || record.id;
            if(!confirm(`Delete "${label}" from this computer?`)) return;
            const data = await api("DELETE", "/api/workshop/downloads/" + record.id);
            if(!data.ok) alert(data.error || "delete failed");
            load_local();
        }));
        return;
    }

    actions.appendChild(button("Download", "ws-button", async () => {
        const data = await api("POST", "/api/workshop/downloads", { id: record.id });
        if(!data.ok) alert(data.error || "download failed");
        load_local();
    }));

    // the server also lets staff delete other people's levels; this page is not
    // the place to hand that out, so the button follows ownership only
    if(signed_in && record.userId === my_user_id) {
        actions.appendChild(button("Delete", "ws-button danger", async () => {
            const label = record.name || record.id;
            if(!confirm(`Delete "${label}" from the workshop server?`)) return;
            const data = await api("DELETE", "/api/workshop/remote/" + record.id);
            if(!data.ok) alert(data.error || "delete failed");
            load_remote();
        }));
    }
}

// ---- pager ----

// 1 2 ... 7 8 9 ... 20: a gap remembers the first page it hides
function page_items(page, pages) {
    if(pages <= 7) {
        return Array.from({ length: pages }, (_, index) => ({ page: index + 1 }));
    }

    const shown = new Set([1, pages]);
    for(const near of [page - 1, page, page + 1]) {
        if(near >= 1 && near <= pages) shown.add(near);
    }

    const items = [];
    let previous = 0;
    for(const number of [...shown].sort((a, b) => a - b)) {
        if(number - previous > 1) items.push({ gap: previous + 1 });
        items.push({ page: number });
        previous = number;
    }
    return items;
}

function render_pager(parent, page, pages, go) {
    if(!parent) return;
    parent.innerHTML = "";

    const step = (label, target, disabled) => {
        const el = button(label, "ws-page", () => go(target));
        if(disabled) el.disabled = true;
        return el;
    };

    parent.appendChild(step("<", page - 1, page <= 1));
    for(const item of page_items(page, pages)) {
        if(item.gap !== undefined) {
            const el = button("...", "ws-page ws-page-gap", () => go(item.gap));
            el.title = `go to page ${item.gap}`;
            parent.appendChild(el);
        } else if(item.page === page) {
            const el = document.createElement("span");
            el.className = "ws-page ws-page-current";
            el.textContent = String(page);
            el.setAttribute("aria-current", "page");
            parent.appendChild(el);
        } else {
            parent.appendChild(button(String(item.page), "ws-page", () => go(item.page)));
        }
    }
    parent.appendChild(step(">", page + 1, page >= pages));
}

// ---- lists ----

function render_result(total, known) {
    if(!search_result) return;
    search_result.innerHTML = "";
    search_result.hidden = !search.text || !known;
    if(search_result.hidden) return;

    const text = document.createElement("span");
    text.textContent = `${total} ${total === 1 ? "match" : "matches"} for ` +
        `${search.field} "${search.text}"`;

    const clear = button("clear", "ws-result-clear", () => {
        search.text = "";
        search_text_box.value = "";
        remote_page = 1;
        load_remote();
    });

    search_result.append(text, clear);
}

async function load_local() {
    if(!local_list) return;
    const data = await api("GET", "/api/workshop/downloads");
    local_levels = data.ok ? (data.levels || []) : [];
    local_list.innerHTML = "";
    if(!data.ok) {
        local_list.appendChild(note(data.error || "could not read the local folder"));
        render_pager(local_pager, 1, 1, null);
        return;
    }
    render_local();
}

function render_local() {
    const pages = Math.max(1, Math.ceil(local_levels.length / PAGE_SIZE));
    local_page = Math.min(Math.max(local_page, 1), pages);

    local_list.innerHTML = "";
    if(!local_levels.length) {
        local_list.appendChild(note("Nothing downloaded yet."));
    } else {
        const from = (local_page - 1) * PAGE_SIZE;
        for(const entry of local_levels.slice(from, from + PAGE_SIZE)) {
            local_list.appendChild(make_row(entry, "local"));
        }
    }
    render_pager(local_pager, local_page, pages, target => {
        local_page = target;
        render_local();
    });
}

async function load_remote() {
    if(!remote_list) return;
    remote_list.innerHTML = "";

    if(!config.workshopRemote) {
        remote_list.appendChild(note("No workshop server is configured. Set ANTS_WORKSHOP_URL and restart the game."));
        render_pager(remote_pager, 1, 1, null);
        render_result(0, false);
        return;
    }

    remote_list.appendChild(note("loading..."));
    const params = new URLSearchParams({
        offset: String((remote_page - 1) * PAGE_SIZE),
        limit: String(PAGE_SIZE),
    });
    if(mine_only && my_user_id) params.set("owner", my_user_id);
    if(search.text) params.set(search.field, search.text);
    if(sort_box) params.set("sort", sort_box.value);
    const data = await api("GET", "/api/workshop/remote?" + params.toString());
    remote_list.innerHTML = "";
    if(!data.ok) {
        remote_list.appendChild(note(data.error || "could not reach the workshop server"));
        render_pager(remote_pager, 1, 1, null);
        render_result(0, false);
        return;
    }

    const levels = data.levels || [];
    render_result(Number(data.total) || 0, true);
    const pages = Math.max(1, Math.ceil((Number(data.total) || 0) / PAGE_SIZE));
    if(remote_page > pages) {
        // the last page emptied while we were on it
        remote_page = pages;
        load_remote();
        return;
    }

    if(!levels.length) {
        // the strip above already says what was searched for
        remote_list.appendChild(note(search.text
            ? "No level matches."
            : mine_only
                ? "You have not published a level yet."
                : "The server has no levels yet."));
    } else {
        for(const entry of levels) remote_list.appendChild(make_row(entry, "remote"));
    }
    render_pager(remote_pager, remote_page, pages, target => {
        remote_page = target;
        load_remote();
    });
}

// ---- session ----

function set_session(value, name, id) {
    signed_in = !!value;
    username = name || "";
    my_user_id = id || "";
    if(!signed_in) {
        mine_only = false;
        remote_page = 1;
    }
    if(identity_label) {
        identity_label.textContent = signed_in ? `signed in as ${username}` : "";
        identity_label.hidden = !signed_in;
    }
    if(publish_button) publish_button.hidden = !signed_in;
    if(signout_button) signout_button.hidden = !signed_in;
    if(signin_button) signin_button.hidden = signed_in || !config.ojLoginUrl;
    if(mine_filter) mine_filter.hidden = !signed_in;
    if(mine_only_box && !signed_in) mine_only_box.checked = false;
    refresh_likes();
}

// the gui builds the PKCE pair, so the verifier never reaches this page
function sign_in() {
    if(!config.ojLoginUrl) return;
    api("GET", "/api/workshop/login/start").then(data => {
        if(!data.ok) {
            alert(data.error || "could not start sign in");
            return;
        }
        location.href = data.url;
    });
}

async function load_session() {
    const data = await api("GET", "/api/workshop/session");
    set_session(data.ok && data.signedIn, data.username || "", data.userId || "");
}

async function sign_out() {
    await api("POST", "/api/workshop/logout");
    set_session(false, "");
    load_remote();
}

async function open_publish() {
    if(!signed_in) return;
    const custom = await api("GET", "/api/level/custom-plain");
    if(!custom.ok) {
        alert(custom.error || "could not read the custom level");
        return;
    }

    preview_box.innerHTML = "";
    const hint = document.createElement("p");
    hint.className = "ws-desc";
    hint.textContent = "This is the level the game holds right now.";
    preview_box.appendChild(hint);
    render_summary(preview_box, custom.level || {});

    publish_form.reset();
    list_view.hidden = true;
    publish_view.hidden = false;
    if(publish_button) publish_button.hidden = true;
    const name = publish_form.querySelector('[name="name"]');
    if(name) name.focus();
}

function close_publish() {
    publish_view.hidden = true;
    list_view.hidden = false;
    if(publish_button) publish_button.hidden = !signed_in;
}

async function submit_publish(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const read = key => (form.querySelector(`[name="${key}"]`).value || "").trim();

    const title = read("name");
    if(!title) {
        alert("A title is required.");
        return;
    }
    const author = read("authorName");
    if(!author) {
        alert("An author name is required.");
        return;
    }

    const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    try {
        // read the board again: it may have changed while the preview was open
        const custom = await api("GET", "/api/level/custom-plain");
        if(!custom.ok) {
            alert(custom.error || "could not read the custom level");
            return;
        }
        const data = await api("POST", "/api/workshop/publish", {
            name: title,
            authorName: author,
            description: read("description"),
            level: custom.level,
        });
        if(!data.ok) {
            alert(data.error || "publish failed");
            return;
        }
        close_publish();
        // mine_only = true;
        // if(mine_only_box) mine_only_box.checked = true;
        remote_page = 1;
        load_remote();
    } finally {
        submit.disabled = false;
    }
}

function submit_search(event) {
    event.preventDefault();
    search.field = search_field_box.value;
    search.text = search_text_box.value.trim();
    // a new query means the old page number is meaningless
    remote_page = 1;
    load_remote();
}

if(signin_button) {
    signin_button.addEventListener("click", sign_in);
}

if(signout_button) {
    signout_button.addEventListener("click", sign_out);
}

if(publish_button) {
    publish_button.addEventListener("click", open_publish);
}

if(publish_form) {
    publish_form.addEventListener("submit", submit_publish);
}

if(search_form) {
    search_form.addEventListener("submit", submit_search);
}

if(sort_box) {
    // a new order means the old page number is meaningless
    sort_box.addEventListener("change", () => {
        remote_page = 1;
        load_remote();
    });
}

const cancel_publish = document.querySelector('[data-action="cancel-publish"]');
if(cancel_publish) {
    cancel_publish.addEventListener("click", close_publish);
}

if(mine_only_box) {
    mine_only_box.addEventListener("change", () => {
        mine_only = mine_only_box.checked;
        remote_page = 1;
        load_remote();
    });
}

fetch("/api/config").then(r => r.json()).then(cfg => {
    config = cfg || {};
    set_session(false, "");
    if(new URLSearchParams(location.search).get("login") === "failed") {
        history.replaceState(null, "", location.pathname);
        alert("Sign in did not complete. Please try again.");
    }
    load_local();
    load_remote();
    load_session();
}).catch(() => {
    load_local();
});
