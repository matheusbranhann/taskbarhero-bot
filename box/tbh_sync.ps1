# tbh_sync.ps1 -- coloca a box em dia SEM abrir o jogo: painel + tbh_core + offsets do build instalado.
# Extraido do tbh_start.ps1 (passo 3) e corrigido:
#   - tbh_core.py mudou de lugar no repo na v4.0 (raiz -> python_old_project/); a URL antiga da 404
#     e o catch engolia o erro, entao a box ficava com o core velho pra sempre.
#   - offsets NAO dependem mais do jogo aberto: vem do FEED (offsets/offsets_<hash>.json no repo),
#     com o hash calculado do GameAssembly.dll NO DISCO. Antes exigia rodar o painel com o jogo
#     carregado pra "materializar", o que impedia preparar uma box sem ligar o jogo.
$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference    = "SilentlyContinue"
$DL   = "C:\tbh_auto"
$REPO = "matheusbranhann/taskbarhero-bot"
$UA   = @{ "User-Agent" = "tbh" }
$LOG  = "$DL\sync.log"
function Log($m) { $l = "[{0}] {1}" -f (Get-Date -Format HH:mm:ss), $m; $l | Add-Content $LOG; Write-Output $l }
New-Item -ItemType Directory -Force -Path $DL, "$DL\cache" | Out-Null

# ---------- 1) acha o GameAssembly.dll (sem precisar do jogo rodando) ----------
$cands = @(
  "C:\Program Files (x86)\Steam\steamapps\common\TaskbarHero\GameAssembly.dll",
  "C:\Program Files\Steam\steamapps\common\TaskbarHero\GameAssembly.dll",
  "D:\SteamLibrary\steamapps\common\TaskbarHero\GameAssembly.dll"
)
$ga = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ga) { Log "GameAssembly.dll nao encontrado - sem offsets"; }

# ---------- 2) hash do build: md5 dos 2.000.000 PRIMEIROS bytes (mesma regra do painel) ----------
$hash = $null
if ($ga) {
  $fs = [IO.File]::OpenRead($ga)
  $buf = New-Object byte[] 2000000
  $n = $fs.Read($buf, 0, 2000000); $fs.Close()
  $md5 = [Security.Cryptography.MD5]::Create().ComputeHash($buf, 0, $n)
  $hash = (([BitConverter]::ToString($md5) -replace "-", "").ToLower()).Substring(0, 12)
  Log "build do jogo instalado: $hash"
}

# ---------- 3) painel + tbh_core da release mais nova ----------
try {
  $r = Invoke-RestMethod "https://api.github.com/repos/$REPO/releases/latest" -Headers $UA
  $tag = $r.tag_name
  $asset = $r.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1
  $have = if (Test-Path "$DL\ver.txt") { Get-Content "$DL\ver.txt" } else { "" }
  if ($have -ne $tag -or -not (Test-Path "$DL\tbh_core.py")) {
    Log "baixando painel $tag (tinha: '$have')"
    Invoke-WebRequest $asset.browser_download_url -OutFile "$DL\panel.zip" -Headers $UA
    Expand-Archive "$DL\panel.zip" $DL -Force
    # CAMINHO NOVO do core. Tenta o atual e cai no antigo (releases <= v3.x tinham na raiz).
    $okCore = $false
    foreach ($u in @("https://raw.githubusercontent.com/$REPO/$tag/python_old_project/tbh_core.py",
                     "https://raw.githubusercontent.com/$REPO/$tag/tbh_core.py")) {
      try {
        Invoke-WebRequest $u -OutFile "$DL\tbh_core.py.new" -Headers $UA
        if ((Get-Item "$DL\tbh_core.py.new").Length -gt 100000) {
          Move-Item "$DL\tbh_core.py.new" "$DL\tbh_core.py" -Force; $okCore = $true
          Log "tbh_core.py atualizado de $u"; break
        }
      } catch { }
    }
    if (-not $okCore) { Log "AVISO: nao consegui baixar o tbh_core.py (mantive o que ja tinha)" }
    Set-Content "$DL\ver.txt" $tag
    Remove-Item "$DL\cache\offsets_*.json" -Force -ErrorAction SilentlyContinue   # offsets de build/extrator antigo
  } else { Log "painel ja esta na $tag" }
} catch { Log "download do release falhou: $($_.Exception.Message)" }

# ---------- 4) offsets do build instalado, direto do FEED (nao precisa do jogo aberto) ----------
if ($hash) {
  $dest = "$DL\cache\offsets_$hash.json"
  if (Test-Path $dest) {
    Log "offsets do build $hash ja estao no cache"
  } else {
    try {
      Invoke-WebRequest "https://raw.githubusercontent.com/$REPO/main/offsets/offsets_$hash.json" `
        -OutFile $dest -Headers $UA
      $j = Get-Content $dest -Raw | ConvertFrom-Json
      if ($j._ver -ge 7 -and $j.gra) { Log "offsets do build $hash baixados do feed (_ver=$($j._ver))" }
      else { Remove-Item $dest -Force; Log "AVISO: json do feed invalido/antigo - descartado" }
    } catch {
      Log "AVISO: build $hash ainda nao esta no feed (offsets/) - o painel roda so com AOB ate publicar"
    }
  }
}

# ---------- 5) deps do python ----------
python -m pip install --quiet --disable-pip-version-check pymem capstone 2>&1 | Out-Null
Log "sync completo"
