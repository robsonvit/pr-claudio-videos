# 🙏 CRIAÇÃO VÍDEOS PR CLÁUDIO / JESUS

Bot de geração automática de vídeos com narração de pregação/motivacional cristão para YouTube Shorts, Facebook Reels e Telegram.

---

## 📺 Canais Integrados

| Plataforma | Canal / Página | Identificador / Detalhes |
|---|---|---|
| **YouTube** | **JESUS VIVE** | `UCwbKrySHzH-E21DhO-nYKsQ` (OAuth 2.0) |
| **Facebook** | **Enfermagem Curiosa** | ID: `101746485343968` (Meta Graph API Reels) |
| **Telegram** | Bot Canal / Grupo | Envio com tags e confirmação |

---

## ⚙️ Variáveis de Ambiente (.env / GitHub Secrets)

Configure no `.env` para uso local ou no GitHub: **Settings → Secrets and variables → Actions**:

- `OPENROUTER_API_KEY`: Geração de roteiros.
- `PEXELS_API_KEY`: Download dos clipes de fundo.
- `FISH_API_KEY`: Voz Pr. Cláudio / TTS.
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`: Notificações no Telegram.
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`: OAuth do canal **JESUS VIVE**.
- `META_FB_PAGE_ID` & `META_PAGE_ACCESS_TOKEN`: Postagem na página **Enfermagem Curiosa**.

---

## 🗂️ Estrutura de Scripts

```
scripts/
  pipeline.py          → Orquestrador principal (executa etapas 1 a 8)
  gerar_roteiro.py     → Criação de títulos, ganchos e roteiros via IA
  gerar_voz.py         → Síntese de áudio e extração de timings
  buscar_videos_pexels.py → Busca clipes verticais no Pexels
  montar_video.py      → Renderização de vídeo com legendas e áudio
  enviar_telegram.py   → Envio do MP4 para o Telegram
  enviar_youtube.py    → Upload de Shorts no canal JESUS VIVE
  enviar_facebook.py   → Upload de Reels na página Enfermagem Curiosa
.github/workflows/
  gerar_video.yml      → Workflow diário do GitHub Actions
VIDEOS INICIAIS/       → Clipes de abertura (0 a 3s)
musicas/               → Trilhas instrumentais de fundo
```

---

## 🧪 Teste de Conexão Rápido

Para validar os acessos sem precisar gerar um vídeo completo:

```bash
# Valida conexão com o YouTube (Canal JESUS VIVE)
python scripts/enviar_youtube.py

# Valida conexão com o Facebook (Página Enfermagem Curiosa)
python scripts/enviar_facebook.py
```