# Scripts das sandboxes (Box2 / Sandboxie)

Rodam **dentro** de cada sandbox, em `C:\tbh_auto`.

| script | o que faz |
|---|---|
| `tbh_sync.ps1` | põe a box em dia **sem abrir o jogo**: baixa o painel da release mais nova, o `tbh_core.py` e os offsets do build instalado |
| `tbh_start.ps1` | start completo do clone: abre a Steam da box, lança o jogo, chama o `tbh_sync.ps1` e sobe o supervisor |

## Por que o sync é separado

Duas coisas quebravam o fluxo antigo:

1. O `tbh_start.ps1` baixava o `tbh_core.py` da **raiz** do repo. Esse caminho morreu na v4.0, quando o
   projeto Python foi pra `python_old_project/` — a URL passou a dar 404 e o `catch` engolia o erro, então
   a box ficava com o core velho para sempre, sem avisar.
2. Os offsets eram "materializados" rodando o painel **com o jogo carregado**. Isso impedia preparar uma
   box sem ligar o jogo, e falhava calado se o jogo não subisse.

Agora o `tbh_sync.ps1` calcula o hash do build direto do `GameAssembly.dll` **no disco** (MD5 dos
2.000.000 primeiros bytes) e baixa `offsets/offsets_<hash>.json` do feed. Nada disso precisa do jogo aberto,
então dá para preparar/atualizar uma box a qualquer momento.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\tbh_auto\tbh_sync.ps1
```

O script só aceita offsets com `_ver >= 7` (a versão do extrator que corrigiu o alvo do ACTk). Se o build
instalado ainda não estiver publicado em `offsets/`, ele avisa e a box segue só com os cheats por AOB.
