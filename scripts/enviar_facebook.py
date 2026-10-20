"""
enviar_facebook.py
Módulo responsável por publicar vídeos (Reels) na página do Facebook.
Página padrão: Enfermagem Curiosa
API: Meta Graph API (v19.0)
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Força o encoding UTF-8 no stdout para suportar emojis no console do Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Carrega variáveis locais se existirem
load_dotenv()

GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = os.environ.get("META_FB_PAGE_ID", "")


def _verificar_status_processamento(video_id: str, access_token: str, max_tentativas: int = 15, intervalo: int = 6) -> bool:
    """Verifica se o vídeo foi processado pela Meta antes da publicação final."""
    url = f"{BASE_URL}/{video_id}?fields=status&access_token={access_token}"
    
    for i in range(max_tentativas):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                status_info = data.get("status", {})
                if isinstance(status_info, dict):
                    st = status_info.get("video_status")
                    if st == "ready":
                        print("  ✓ Vídeo processado com sucesso na Meta (status: ready).")
                        return True
                    elif st == "error":
                        print(f"  ❌ Erro no processamento do vídeo pela Meta: {data}")
                        return False
                elif status_info == "ready":
                    return True
                
                print(f"  ⏳ Aguardando processamento da Meta... ({i+1}/{max_tentativas})", end="\r")
        except Exception as e:
            print(f"  ⚠️ Aviso ao checar status: {e}")
        
        time.sleep(intervalo)
    
    print("\n  ⚠️ Tempo limite de espera atingido; prosseguindo para fase finish...")
    return False


def enviar_facebook_reels(video_path: str, caption: str) -> bool:
    """
    Publica um vídeo como Facebook Reel na página configurada.

    Args:
        video_path: Caminho completo para o arquivo de vídeo MP4.
        caption: Texto de descrição e hashtags do vídeo.

    Returns:
        True se a publicação foi realizada com sucesso, False caso contrário.
    """
    token = os.environ.get("META_PAGE_ACCESS_TOKEN") or PAGE_ACCESS_TOKEN
    page_id = os.environ.get("META_FB_PAGE_ID") or FB_PAGE_ID

    if not token or not page_id:
        print("  ⚠️ META_PAGE_ACCESS_TOKEN ou META_FB_PAGE_ID não configurados — pulando Facebook.")
        return False

    video_file = Path(video_path)
    if not video_file.exists():
        print(f"  ❌ Arquivo de vídeo não encontrado: {video_path}")
        return False

    file_size = video_file.stat().st_size
    print(f"\n[Facebook] Iniciando upload para Facebook Reels (Página ID: {page_id})...")
    print(f"  Tamanho do arquivo: {file_size / (1024 * 1024):.2f} MB")

    try:
        # 1. Iniciar sessão de upload (upload_phase = start)
        init_url = f"{BASE_URL}/{page_id}/video_reels"
        init_payload = {
            "upload_phase": "start",
            "access_token": token,
            "file_size": file_size,
        }
        init_res = requests.post(init_url, data=init_payload, timeout=30)
        init_data = init_res.json()

        if "video_id" not in init_data or "upload_url" not in init_data:
            print(f"  ❌ Erro ao iniciar sessão no Facebook: {init_data}")
            return False

        video_id = init_data["video_id"]
        upload_url = init_data["upload_url"]
        print(f"  ✓ Sessão de upload iniciada. Video ID: {video_id}")

        # 2. Transferir arquivo binário
        headers = {
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(file_size),
        }

        print("  ⬆️ Enviando arquivo de vídeo para a Meta...")
        with open(video_file, "rb") as f:
            upload_resp = requests.post(upload_url, headers=headers, data=f, timeout=300)

        if upload_resp.status_code not in (200, 201):
            print(f"  ❌ Falha no upload binário: {upload_resp.status_code} {upload_resp.text[:300]}")
            return False

        print("  ✓ Arquivo enviado com sucesso.")

        # 3. Verificar processamento
        _verificar_status_processamento(video_id, token)

        # 4. Finalizar e Publicar (upload_phase = finish)
        print("  📢 Concluindo publicação do Reel...")
        finish_url = f"{BASE_URL}/{page_id}/video_reels"
        finish_payload = {
            "access_token": token,
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            "description": caption,
            "share_to_feed": True,
        }

        finish_res = requests.post(finish_url, data=finish_payload, timeout=30)
        finish_data = finish_res.json()

        if finish_data.get("success"):
            print(f"  ✅ Facebook Reel publicado com sucesso na página! Video ID: {video_id}")
            return True
        else:
            print(f"  ❌ Erro na finalização da publicação no Facebook: {finish_data}")
            return False

    except Exception as e:
        print(f"  ❌ Exceção ao postar no Facebook: {e}")
        return False


def testar_conexao_facebook() -> bool:
    """Verifica se as credenciais da página estão funcionando e têm acesso válido."""
    token = os.environ.get("META_PAGE_ACCESS_TOKEN") or PAGE_ACCESS_TOKEN
    page_id = os.environ.get("META_FB_PAGE_ID") or FB_PAGE_ID

    if not token or not page_id:
        print("❌ Variáveis META_PAGE_ACCESS_TOKEN ou META_FB_PAGE_ID não encontradas.")
        return False

    try:
        url = f"{BASE_URL}/{page_id}?fields=id,name,category,link&access_token={token}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            info = resp.json()
            print("✅ Conexão com a Página do Facebook validada com sucesso!")
            print(f"  Nome da Página: {info.get('name')}")
            print(f"  ID: {info.get('id')}")
            print(f"  Categoria: {info.get('category')}")
            return True
        else:
            print(f"❌ Erro ao validar página: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False


if __name__ == "__main__":
    testar_conexao_facebook()
