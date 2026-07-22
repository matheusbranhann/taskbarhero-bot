# Perfis prontos

`profiles.json` — perfis do painel (switches, filtros do fuse, stats e campos de fase forçados).

## Como usar

Copie o `profiles.json` **para a pasta do `TBH_Panel.exe`**. Abra o painel, escolha o perfil no
combo do card *Memory Profiles* e clique **Load**.

Se você já tem um `profiles.json` lá, não sobrescreva: abra os dois num editor e junte as chaves
(o arquivo é um objeto `{"nome": {...}}`).

## O que vem aqui

| perfil | para quê |
|---|---|
| `speed` | foco em velocidade de farm: Attack Damage / Attack Speed / Critical Damage forçados, com auto-box, auto-stash, auto-fuse, auto-boss e auto-restart ligados |
| `braia` | perfil completo de endgame: os 5 stats principais forçados + os mesmos automatismos |

Ambos ligam **ACTk Bypass** e **God Mode**. Nenhum dos dois liga o *Evolution Climb* — ligue à mão
se quiser subir de fase (ele desliga sozinho ao chegar no Torment 3-9).

> Os stats são reaplicados a cada tick; o jogo recalcula e sobrescreveria uma escrita única.
