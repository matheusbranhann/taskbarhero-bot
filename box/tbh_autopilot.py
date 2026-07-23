"""
TBH AUTOPILOT (headless) — roda na box, dirige o motor tbh_core direto.
Automacao TOTAL (auto-box/stash/fuse/boss, actk/god, stats do braia, auto-restart) +
auto-evolution CONDICIONAL: so liga se o Torment 3-9 (4309) ainda nao estiver liberado
(evolve leva o player ate la; ao chegar, troca pra endgame = auto-boss).
NAO modifica o painel; usa o tbh_core baixado do GitHub + offsets do cache do exe.
"""
import sys, time, json, threading, os
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
HERE = r"C:\tbh_auto"
sys.path.insert(0, HERE)
import tbh_core as C

PROFILE_PATH = os.path.join(HERE, "profiles.json")
PROFILE_NAME = "braia"
LOGF = os.path.join(HERE, "autopilot.log")
CONTROLS_PATH = os.path.join(HERE, "controls.json")   # escrito pelo dashboard (SandGate)
TORMENT39 = 4309                     # StageKey do Torment 3-9 (o teto da evolucao)

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    try: open(LOGF, "a", encoding="utf-8").write(line + "\n")
    except Exception: pass

def load_profile():
    try:
        return json.load(open(PROFILE_PATH, encoding="utf-8")).get(PROFILE_NAME, {})
    except Exception as ex:
        log("profiles.json erro: %s" % ex); return {}

def apply_profile(e, prof):
    """Carrega stats + stage edits do perfil no motor (aplicados a cada tick por apply_stats/apply_stage)."""
    st = {}
    for name, d in (prof.get("stats") or {}).items():
        if d.get("on"):
            try: st[name] = float(d.get("val"))
            except Exception: pass
    e.stats = st
    sg = {}
    for k, d in (prof.get("stage") or {}).items():
        if d.get("on"):
            try: sg[k] = int(float(d.get("val")))
            except Exception: pass
    e.stage = sg
    return st, sg

def load_controls():
    """Mascara do dashboard: {"autobox": false, ...}. Chave ausente ou True = o autopilot decide como
    sempre; False = DESLIGADO a forca. Sem o arquivo, nada muda (comportamento historico)."""
    try:
        with open(CONTROLS_PATH, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

_MASKABLE = ("actk", "god", "autobox", "autoitem", "autosynth", "autoboss", "evolve", "watchdog")

def mask_wants(e, ctl):   # mantido por compatibilidade; o set_mode ja aplica a mascara
    """Aplica a mascara POR CIMA do que o set_mode decidiu. So DESLIGA -- religar e voltar a chave
    pra True, que devolve a decisao pro autopilot (nao inventa combinacao invalida de evolve/boss)."""
    off = []
    for k in _MASKABLE:
        if ctl.get(k) is False:
            e.want[k] = False
            off.append(k)
    if ctl.get("stats") is False:
        e.stats = {}; off.append("stats")
    if ctl.get("stage") is False:
        e.stage = {}; off.append("stage")
    return off

def set_mode(e, prof, unlocked):
    """Automacao total; evolve/autoboss sao exclusivos pelo 4309 (autoboss tem prioridade no loop,
    entao durante a subida so evolve; no endgame so autoboss)."""
    p = prof.get("prot", {})
    w = {
        "actk": bool(p.get("actk", True)),
        "god": bool(p.get("god", True)),
        "autobox": True, "autoitem": True, "autosynth": True, "watchdog": True,
        "autoboss": bool(unlocked),        # endgame: farma o boss (soulstone)
        "evolve": (not unlocked),          # subindo: evolve leva ate o 4309
        "synth_maxgrade": 2, "synth_types": {0, 1, 2},
    }
    # MASCARA ANTES de publicar. Aplicar depois de e.want.update abria uma janela em que autobox
    # ficava True: o _auto_loop roda a cada 0.12s noutra thread e abria caixa nesse intervalo
    # (medido: 3 caixas abertas com o autobox "desligado" pelo dashboard).
    ctl = load_controls()
    off = [k for k in _MASKABLE if ctl.get(k) is False]
    for k in off: w[k] = False
    e.want.update(w)
    if ctl.get("stats") is False: e.stats = {}; off.append("stats")
    if ctl.get("stage") is False: e.stage = {}; off.append("stage")
    return off

# ---------------------------------------------------------------------------------------------
# POPUPS BLOQUEANTES: o jogo TRAVA ate serem fechados e ele e click-through, entao so o
# _click_real (mouse_event / raw input) alcanca o botao. Todos abaixo devem ser dispensados.
POPUP_CONFIRM = (
    "game will close",             # servidor rejeitou add item -> o jogo FECHA; o watchdog reabre
    "cannot add item",
    "no response from the server",
    "validation results",          # validacao de itens do servidor -> so dispensa e o jogo segue
    "not held on the server",
    "cleaned up",
    "update is required",          # "An update is required / Verify integrity of game files".
    "verify integrity",            # MEDIDO ao vivo: Confirm FECHA o jogo e o watchdog reabre limpo.
)                                  # Sem tratar este, uma box ficou 2h44 parada na tela de titulo.
POPUP_CLOSE = ("offline", "last login", "reward")     # OFFLINE REWARDS -> botao Close
# ---------------------------------------------------------------------------------------------

def popup_guard(e):
    """DONO UNICO do OCR: a cada ciclo tira 1 screenshot + 1 OCR da janela do jogo e trata os
    popups que TRAVAM o jogo (o jogo e click-through: so mouse_event/_click_real clica). Como e a
    unica thread que chama _ocr_lines, nao ha corrida com o antigo close_offline_popup (removido).
      1) WARNING 'The game will close' (servidor rejeitou add item/inventario) -> clica 'Confirm'.
         O jogo fecha -> o watchdog reabre -> a box VOLTA A UPAR. Sem esse clique fica travado.
      2) OFFLINE REWARDS / last login -> clica 'Close' (aparece a cada abertura e trava ate fechar).
    Roda pra sempre: cobre tanto o boot quanto os popups que surgem no meio do farm."""
    def btn(lines, org, word):
        for t, (x0, y0, x1, y1) in lines:
            if word in t.lower():
                return org[0] + int((x0 + x1) / 2), org[1] + int((y0 + y1) / 2)
        return None
    desconhecido = [0.0]          # ultimo aviso de popup nao catalogado (rate-limit de 5 min)
    while True:
        try:
            if e.pm and e._proc_alive():
                hw = e._game_hwnd()
                if hw:
                    img, org = e._win_shot(hw)
                    if img is not None:
                        lines = e._ocr_lines(img)
                        if lines:
                            txt = " | ".join(t.lower() for t, _ in lines)
                            # 1) popups com botao Confirm: erro do servidor (fecha o jogo; watchdog reabre)
                            #    OU validacao de itens do servidor (so dispensa e o jogo segue)
                            hit = next((k for k in POPUP_CONFIRM if k in txt), None)
                            if hit:
                                pos = btn(lines, org, "confirm")
                                if pos:
                                    log("popup bloqueante [%s] -> Confirm em %d,%d" % (hit, pos[0], pos[1]))
                                    e._click_real(*pos); time.sleep(3); continue
                            # 2) offline/reward -> Close
                            if any(k in txt for k in POPUP_CLOSE):
                                pos = btn(lines, org, "close")
                                if pos:
                                    log("popup OFFLINE REWARDS -> Close em %d,%d" % pos)
                                    e._click_real(*pos); time.sleep(1.5); continue
                            # 3) DESCONHECIDO: NAO clico as cegas (um Confirm tambem aparece em dialogo
                            #    legitimo do jogo, e aceitar por engano pode custar item). Mas AVISO:
                            #    sem esta linha um popup novo trava a box em SILENCIO -- foi assim que
                            #    uma ficou 2h44 parada e so descobrimos olhando print de tela.
                            if btn(lines, org, "confirm"):
                                agora = time.time()
                                if agora - desconhecido[0] > 300:
                                    desconhecido[0] = agora
                                    log("popup DESCONHECIDO com botao Confirm (nao cliquei): %s" % txt[:300])
        except Exception as ex:
            log("popup_guard err: %s" % ex)
        time.sleep(4)

def main():
    log("========== TBH AUTOPILOT ==========")
    try: open(os.path.join(HERE, "autopilot.pid"), "w").write(str(os.getpid()))   # PID file (Sandboxie bloqueia WMI -> startup mata duplicata por aqui)
    except Exception: pass
    prof = load_profile()
    log("perfil '%s': stats_on=%d stage_on=%d prot=%s" % (
        PROFILE_NAME,
        sum(1 for d in (prof.get("stats") or {}).values() if d.get("on")),
        sum(1 for d in (prof.get("stage") or {}).values() if d.get("on")),
        prof.get("prot")))
    e = C.Engine(log=lambda m: log("[eng] %s" % m))

    def eng_loop():                       # como o engine-loop do painel
        while True:
            try: e.tick()
            except Exception: pass
            try: e.apply_watchdog()
            except Exception: pass
            time.sleep(1.2)
    threading.Thread(target=eng_loop, daemon=True).start()
    threading.Thread(target=lambda: popup_guard(e), daemon=True).start()   # WARNING(Confirm)+OFFLINE(Close), pra sempre

    applied = False; last_mode = None; last_off = None
    while True:
        try:
            if e.pm and e._proc_alive():
                if not applied:
                    apply_profile(e, prof); applied = True
                    log("braia aplicado: stats=%d stage=%d" % (len(e.stats), len(e.stage)))
                mx = e.stage_progress()[0] or 0
                unlocked = mx >= TORMENT39
                # re-aplica o perfil TODO ciclo: se o dashboard desligar 'stats' e religar depois,
                # os valores precisam voltar (o apply_profile de cima so roda uma vez).
                apply_profile(e, prof)
                off = set_mode(e, prof, unlocked)   # ja devolve o que a mascara desligou
                if off != last_off:
                    log("dashboard: desligado -> %s" % (", ".join(off) if off else "(nada)"))
                    last_off = off
                mode = "ENDGAME (auto-boss)" if unlocked else "SUBINDO (evolve -> 4309)"
                if mode != last_mode:
                    log("modo=%s | maxStage=%s | 4309 liberado=%s" % (mode, mx, unlocked))
                    last_mode = mode
            else:
                applied = False   # jogo caiu; watchdog reabre, re-carrega ao voltar
        except Exception as ex:
            log("loop err: %s" % ex)
        time.sleep(8)

def _safe(fn, *a):
    try: fn(*a)
    except Exception as ex: log("popup close err: %s" % ex)

if __name__ == "__main__":
    main()
