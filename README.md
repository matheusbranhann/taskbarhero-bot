# tbh_bot — TaskBarHero / Task Bar Hero trainer, cheat & bot

A single-window **trainer, cheat panel and automation bot** for the offline Unity/IL2CPP idle game
**TaskbarHero** (a.k.a. *Task Bar Hero* / *TBH*, on Steam). It reads and writes the running game's memory to
give you a trainer, a live inventory value viewer, a Steam market price browser, and a set of hands-off
automations (open boxes, auto-stash, auto-fuse/synthesize, auto-boss, stage teleport). **Self-updating.**

> **Precision-instrument UI:** deep-black theme, hairline borders, monospace data, a single orange accent.

---

## ⚠️ Disclaimer

- For the **offline, single-player** game **you own**, on **your own machine**. Educational / personal use.
- It attaches to the game process and edits memory (like Cheat Engine). Use at your own risk.
- Item **grant/use and synthesis are validated server-side** — the bot only performs **legit game actions**
  (it clicks boxes, moves items, and triggers the cube exactly like the game does). It never forges items.

---

## ✨ Features

| Tab / Feature | What it does |
|---|---|
| **Trainer** | Toggle protection (ACTk bypass, God Mode), edit 25+ stats by category, edit stage fields, save/load **profiles**. |
| **Inventory** | Lists every item (inventory + stash) with grade, quantity, and **Steam market value**, sorted by worth. |
| **Market** | Browse/search live Steam Community Market prices for game items. |
| 🎁 **Auto-box** | Opens boxes automatically the moment they drop (normal / boss / act-boss). |
| 📦 **Auto-stash** | Moves items from the inventory into the stash automatically. |
| ⚗️ **Auto-fuse (synthesis)** | Auto-opens the cube and fuses **9 of a grade** at **Lv.65~80**, cycling Equipment / Accessory / Material by itself. Pick the **max grade** and **types** — a hard cap **never fuses above your choice**. |
| 🗡 **Auto-boss** | Spends a soulstone on the act boss (x-10) of a difficulty and returns automatically. |
| 📈 **Evolution** | Always keeps you on your newest unlocked stage (1-1 → Torment 3-9). Free stage **teleport** to any stage too. |
| 🏷 **Price overlay** | Optional on-screen overlay that shows an item's Steam price on hover (native Windows OCR). |
| 🔄 **Auto-offsets** | If the game updates, the panel **re-resolves all memory offsets by itself** (via a bundled Il2CppDumper), so it keeps working across builds. |
| ⬆️ **Auto-update** | Checks GitHub on startup and **updates itself in one click** when a new version ships. |

---

## 🚀 Run it

### Option A — the release .exe (no Python needed)
1. Download `TBH_Panel.exe` from the [Releases](../../releases) page.
2. Start **TaskbarHero** and get in-game.
3. Double-click `TBH_Panel.exe`. It finds the game automatically and connects.

### Option B — from source (Windows, no commands to type)
1. Double-click **`INSTALL.bat`**. It finds a suitable **64-bit Python** (offers to install it via `winget`
   if missing), creates an isolated `.venv`, and installs every dependency for you.
2. Double-click **`TBH.bat`** to launch the panel.

> Don't run `pip install -r requirements.txt` by hand — `INSTALL.bat` does it safely (isolated `.venv`,
> and a failure of the optional overlay packages never blocks the panel).

**Requirements:** Windows 10/11 and **64-bit Python 3.9+** (the installer can install it for you). The
optional price-overlay needs `winsdk`, `pillow`, `numpy`; if those can't install on a very new Python,
the panel still runs — only the overlay is skipped.

<details><summary>Advanced / manual install</summary>

```bash
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-core.txt      # core (required)
.venv\Scripts\python -m pip install -r requirements-optional.txt  # overlay (optional)
.venv\Scripts\python tbh_panel.py
```
</details>

---

## 🔨 Build the standalone .exe

```bash
build_exe.bat            # wraps the PyInstaller command below
```
or manually:
```bash
python -m PyInstaller --onefile --windowed --name TBH_Panel --noconfirm \
  --collect-all customtkinter --collect-all winsdk --collect-submodules pymem \
  --hidden-import tbh_core --hidden-import tbh_overlay --hidden-import market_db \
  --add-data "item_prices.json;." --add-data "market_prices.json;." \
  --add-data "tools/Il2CppDumper/Il2CppDumper.exe;tools/Il2CppDumper" \
  --add-data "tools/Il2CppDumper/config.json;tools/Il2CppDumper" \
  tbh_panel.py
```
Output: `dist/TBH_Panel.exe`.

Tip: run `TBH_Panel.exe --selftest` to write a `tbh_selftest.log` that verifies attach, offsets,
inventory, dispatcher, and the auto-box / auto-stash / auto-fuse loop — handy after a game update.

---

## 🧩 How it works (short version)

- **`tbh_core.py`** — the engine. Attaches with `pymem`, resolves symbols per build (fast path from a
  known-builds table, otherwise re-dumps with Il2CppDumper and caches the result), and reads/writes memory.
- **Main-thread dispatcher.** Unity async/UI calls (opening a box, moving items, the cube) must run on the
  game's main thread. The engine installs a tiny code-cave hook on `InputManager.Update` and dispatches
  numbered commands to it each frame — so every action is a real, legit game call.
- **Single automation loop.** One thread runs, in priority order: **open boxes → stash items → synthesize**.
  (Auto-box has priority so boxes always open promptly, even while the cube is fusing.)
- **`tbh_panel.py`** — the CustomTkinter UI. **`tbh_overlay.py`** — the price overlay. **`market_db.py`** —
  fetches Steam market prices.

Everything is memory-only; no files in the game folder are modified.

---

## 📝 Notes & limitations

- **Auto-fuse is level- and grade-safe:** it opens the cube, sets **Lv.65~80**, and cycles the **types**
  by itself. Choose the **max grade** and which **types** to fuse in the panel — a hard cap reads the actual
  filled grade and **never fuses above your choice** (default `Rare`, so it never touches legendary+).
- Auto-offsets covers renamed/obfuscated symbols, but a very large game update may need a fresh Il2CppDumper.

---

## 🙏 Credits

- **[Il2CppDumper](https://github.com/Perfare/Il2CppDumper)** by Perfare — bundled in `tools/` and used for
  auto-resolving offsets when the game updates.
- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) and [Pymem](https://github.com/srounet/Pymem).

## 📄 License

MIT — see [LICENSE](LICENSE). The bundled Il2CppDumper keeps its own license.

---

<sub>**Keywords:** TaskBarHero · Task Bar Hero · TBH · taskbarhero cheat · task bar hero trainer · TBH bot · idle game trainer · Steam cheat · Unity IL2CPP trainer · game hacking · memory editor · auto-fuse · auto-box · godmode · pymem · Python game bot.</sub>
