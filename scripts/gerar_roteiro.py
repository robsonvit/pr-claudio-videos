"""
gerar_roteiro.py
Gera roteiros virais de "verdades duras" via OpenRouter API.
Usa modelos gratuitos (:free) com fallback automático entre eles.
Controla os temas usados para evitar repetições em 20 rodadas.
"""

import os
import json
import random
import sys
import re
from pathlib import Path
from openai import OpenAI

# ── Configurações OpenRouter ───────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Modelos gratuitos em ordem de preferência — sufixo :free = sem custo
# Lista atualizada em 29/08/2026 via API do OpenRouter
MODELOS_GRATUITOS = [
    "minimax/minimax-m3:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "minimax/minimax-m2.7:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "liquid/lfm-2.5-2.6b:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
    "z-ai/glm-5.2:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
    "inclusionai/ling-3.0-flash-fin:free",
    "dots-studio/dots-3-note-preview:free",
    "cohere/north-mini-code:free",
    "openrouter/free"
]

TEMAS_FILE = Path(__file__).parent.parent / "temas_usados.json"
HISTORICO_FILE = Path(__file__).parent.parent / "historico_ganchos.json"

# ── Categorias de temas para garantir variedade ───────────────────────────────
# Cada categoria tem temas distintos. A rotação garante que vídeos consecutivos
# nunca caiam na mesma emoção dominante.

TEMAS_POR_CATEGORIA = {
    "dores_emocionais": [
        "ansiedade que não deixa você dormir e faz sua mente correr à noite",
        "medo paralisante que impede você de dar o próximo passo",
        "tristeza profunda que você carrega sem conseguir explicar para ninguém",
        "insegurança que faz você duvidar de tudo o que você é",
        "culpa que você ainda carrega por algo que já passou",
        "arrependimento por escolhas que não podem mais ser desfeitas",
        "cansaço da alma de quem já lutou muito e ainda não viu resultado",
        "falta de esperança quando tudo parece escuro ao seu redor",
        "sensação de estar completamente perdido sem saber o próximo passo",
        "pessoas que sofrem em silêncio e sorriem por fora",
    ],
    "relacionamentos": [
        "término de relacionamento que deixou uma ferida que não cicatriza",
        "traição de alguém em quem você confiava com o coração aberto",
        "solidão dentro de um relacionamento onde você se sente invisível",
        "amor que você deu sem limite e não foi correspondido",
        "rejeição que fez você acreditar que não é suficiente",
        "decepção com pessoas que você achava que seriam para sempre",
        "abandono de quem prometeu nunca te largar",
        "amizades que desapareceram na hora mais difícil da sua vida",
        "relacionamento tóxico do qual você não sabe como sair",
        "perdão de quem te machucou profundamente mas você ainda ama",
    ],
    "fe_e_espera": [
        "espera pela resposta de Deus que parece não chegar",
        "silêncio de Deus nos momentos em que você mais precisava ouvir",
        "oração que você fez com fé e ainda não foi respondida",
        "dúvida sobre se Deus realmente ouve você",
        "portas fechadas que fizeram você questionar seu propósito",
        "fé abalada por situações que você não consegue entender",
        "confiança em Deus mesmo quando a vida não faz sentido",
        "perseverança quando tudo parece dizer para você desistir",
        "sinal de Deus que você está pedindo e esperando",
        "paz que ultrapassa o entendimento nos momentos mais difíceis",
    ],
    "familia_e_filhos": [
        "família desestruturada que deixou marcas na sua vida",
        "filhos que se afastaram e partiram o coração dos pais",
        "casamento que está passando por uma crise profunda",
        "desejo de ter um filho que ainda não chegou",
        "pais que não souberam expressar amor e deixaram feridas",
        "reconciliação com um familiar com quem você perdeu o contato",
        "proteção dos filhos em um mundo que parece cada vez mais perigoso",
        "mãe ou pai que está doente e você não sabe o que fazer",
        "família unida pela fé mesmo diante das dificuldades",
        "herança de amor que você quer deixar para seus filhos",
    ],
    "superacao_e_recomecos": [
        "recomeço depois de perder tudo o que você havia construído",
        "sonhos frustrados que você não sabe se ainda vale a pena ter",
        "segunda chance que Deus oferece para quem já errou muito",
        "levantando depois de uma queda que parecia definitiva",
        "novo começo quando tudo que era familiar ficou para trás",
        "superação de uma doença que mudou tudo na sua vida",
        "batalha contra vícios que você não consegue vencer sozinho",
        "força para continuar quando todas as forças já se esgotaram",
        "identidade que você perdeu e está tentando encontrar novamente",
        "vitória que está chegando mesmo que você ainda não consiga ver",
    ],
    "noite_e_crise": [
        "noites difíceis em que você chora sem conseguir parar",
        "crise financeira que tirou o sono e a paz da sua família",
        "momento em que você pensou em desistir de tudo",
        "perda de emprego que abalou sua fé e sua esperança",
        "dívidas que parecem uma montanha impossível de escalar",
        "doença que chegou de repente e mudou todos os planos",
        "luto por alguém que partiu cedo demais",
        "situação sem saída que só Deus pode resolver",
        "tempestade que está passando mas que parece que não vai acabar",
        "desespero às três da manhã quando o mundo parece dormir",
    ],
    "gratidao_e_bencaos": [
        "gratidão por ter sobrevivido a uma fase que quase te destruiu",
        "milagre silencioso que Deus fez na sua vida sem você perceber",
        "bênção disfarçada de dificuldade que só mais tarde você entendeu",
        "proteção que Deus exerceu sobre você sem você saber",
        "livramento de algo ruim que poderia ter acontecido",
        "momento em que Deus surpreendeu quando você menos esperava",
        "abundância que chegou depois de um longo tempo de escassez",
        "porta que Deus abriu quando todas as outras foram fechadas",
        "saúde restaurada depois de uma batalha que parecia impossível",
        "gratidão pelas pequenas coisas que você aprendeu a valorizar",
    ],
    "proposito_e_identidade": [
        "propósito de vida que você ainda não encontrou e isso te angustia",
        "talentos que Deus colocou em você e que você ainda não usou",
        "chamado de Deus que você está ignorando por medo",
        "quem você é de verdade além dos seus erros e fracassos",
        "missão que foi colocada em sua vida antes mesmo de você nascer",
        "comparação com os outros que rouba a alegria da sua jornada",
        "autoestima destruída que Jesus quer restaurar completamente",
        "valor que você tem aos olhos de Deus mesmo sem sentir isso",
        "legado que você vai deixar quando não estiver mais aqui",
        "versão de você mesmo que Deus ainda está moldando e preparando",
    ],
}

# Lista plana de todos os temas para controle de uso
TEMAS_BASE = [tema for cat in TEMAS_POR_CATEGORIA.values() for tema in cat]

CATEGORIAS_FILE = Path(__file__).parent.parent / "categoria_atual.json"


def _carregar_categoria_atual() -> str:
    """Retorna a próxima categoria a ser usada, rotacionando entre todas."""
    categorias = list(TEMAS_POR_CATEGORIA.keys())
    if CATEGORIAS_FILE.exists():
        with open(CATEGORIAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        idx_atual = data.get("idx", 0)
    else:
        idx_atual = 0
    proximo_idx = (idx_atual + 1) % len(categorias)
    with open(CATEGORIAS_FILE, "w", encoding="utf-8") as f:
        json.dump({"idx": proximo_idx}, f)
    return categorias[idx_atual]


# ── Prompt Mestre ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """# PROMPT MESTRE — CRIADOR DE ROTEIROS VIRAIS

Atue como um roteirista especialista em vídeos curtos virais de motivação cristã/estoica.

Seu objetivo é escrever um roteiro de 60 segundos com o tom de voz extremamente natural e humanizado. Fuja completamente de textos que pareçam gerados por IA, clichês robóticos ou pregações artificiais. Fale como um amigo sábio e experiente batendo um papo sincero, olho no olho. Use linguagem coloquial, frases do dia a dia e demonstre vulnerabilidade e empatia real.

Estrutura Obrigatória:

1. Gancho (0-3s): Uma frase de impacto, um aviso ou um desabafo em primeira pessoa que soe como o início de uma conversa muito franca. (Ex: "Sabe uma coisa que a vida me ensinou do pior jeito?"). VOCÊ DEVE CRIAR GANCHOS TOTALMENTE INÉDITOS E DIFERENTES a cada geração, fugindo do óbvio.

2. Corpo (4-45s): Fale sobre a realidade nua e crua (decepções, lutas). Mostre empatia. Use frases curtas, pausas naturais e uma estrutura de raciocínio de quem está refletindo em voz alta, e não lendo um teleprompter. Contraste essa dor com sabedoria e paz de uma forma autêntica.

3. Conclusão (45-60s): Uma reflexão final de alívio ou força, dita de forma leve e reconfortante. Encerre obrigatoriamente com a palavra "Amém".

---

# INSTRUÇÕES DE FORMATAÇÃO E EMOÇÃO (FISH AUDIO)
- Retorne APENAS um objeto JSON válido (sem texto fora do JSON).
- O roteiro deve ter o tamanho ideal de 70 a 100 palavras.
- INCLUA emoções do Fish Audio no início de CADA frase usando colchetes (ex: [serious] A vida ensina..., [sad] E isso dói..., [hopeful] Mas Deus restaura...). As emoções devem estar em INGLÊS.
"""

# ── Controle de temas ─────────────────────────────────────────────────────────
def carregar_temas_usados() -> list:
    if TEMAS_FILE.exists():
        with open(TEMAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_tema_usado(tema: str) -> None:
    usados = carregar_temas_usados()
    usados.append(tema)
    if len(usados) >= len(TEMAS_BASE):
        print("Todos os temas foram usados. Reiniciando a lista.")
        usados = []
    with open(TEMAS_FILE, "w", encoding="utf-8") as f:
        json.dump(usados, f, ensure_ascii=False, indent=2)


def escolher_tema() -> str:
    """
    Escolhe um tema garantindo que NENHUM tema será repetido até que todos
    os temas de todas as categorias tenham sido utilizados.
    """
    usados = carregar_temas_usados()
    
    disponiveis = [t for t in TEMAS_BASE if t not in usados]
    
    if not disponiveis:
        print("Todos os temas do projeto foram usados! Reiniciando a memória de temas.")
        usados = []
        with open(TEMAS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        disponiveis = TEMAS_BASE

    categoria = _carregar_categoria_atual()
    temas_cat = TEMAS_POR_CATEGORIA.get(categoria, TEMAS_BASE)
    
    disponiveis_na_cat = [t for t in disponiveis if t in temas_cat]
    
    if disponiveis_na_cat:
        tema = random.choice(disponiveis_na_cat)
        print(f"Categoria: '{categoria}' | Tema escolhido: {tema}")
    else:
        tema = random.choice(disponiveis)
        print(f"Categoria original vazia. Tema aleatório escolhido: {tema}")
        
    return tema


def carregar_historico_ganchos() -> list:
    if HISTORICO_FILE.exists():
        with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_no_historico(roteiro_fala: str) -> None:
    primeira_frase = roteiro_fala.split('.')[0].strip() + '.'
    usados = carregar_historico_ganchos()
    usados.append(primeira_frase)
    if len(usados) > 20:
        usados = usados[-20:]
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(usados, f, ensure_ascii=False, indent=2)



# ── Extrator de JSON robusto ──────────────────────────────────────────────────
def _extrair_json(content: str) -> dict:
    """
    Extrai o JSON da resposta do modelo com múltiplas estratégias.
    Lida com modelos que retornam raciocínio, markdown ou texto extra.
    """
    def is_valid(obj):
        return isinstance(obj, dict) and "titulo" in obj and "roteiro_fala" in obj

    # Estratégia 1: parse direto
    try:
        obj = json.loads(content.strip())
        if is_valid(obj): return obj
    except json.JSONDecodeError:
        pass

    # Estratégia 2: remove blocos markdown ```json ... ```
    limpo = re.sub(r'```(?:json)?\s*', '', content)
    limpo = re.sub(r'```\s*', '', limpo)
    try:
        obj = json.loads(limpo.strip())
        if is_valid(obj): return obj
    except json.JSONDecodeError:
        pass

    # Estratégia 3: maior bloco {...} válido com chaves obrigatórias
    candidatos = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    for cand in sorted(candidatos, key=len, reverse=True):
        try:
            obj = json.loads(cand)
            if is_valid(obj):
                return obj
        except json.JSONDecodeError:
            continue

    # Estratégia 4: greedy do primeiro { ao último }
    primeiro = content.find('{')
    ultimo = content.rfind('}')
    if primeiro != -1 and ultimo != -1 and ultimo > primeiro:
        try:
            obj = json.loads(content[primeiro:ultimo + 1])
            if is_valid(obj): return obj
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Nenhum JSON contendo 'titulo' e 'roteiro_fala' foi encontrado. Conteúdo: {content[:400]}")


# ── Geração de roteiro via OpenRouter ─────────────────────────────────────────
def gerar_roteiro(tema: str) -> dict:
    """
    Gera o roteiro viral via OpenRouter usando modelos gratuitos.
    Tenta cada modelo da lista em ordem até um funcionar.
    """
    global MODELOS_GRATUITOS
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY não definida!")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    historico = carregar_historico_ganchos()
    historico_str = ""
    if historico:
        historico_str = "\n\n⚠️ GANCHOS RECENTEMENTE USADOS (É EXTREMAMENTE PROIBIDO COMEÇAR COM ESTAS FRASES OU ALGO PARECIDO, SEJA CRIATIVO):\n" + "\n".join(f"- {g}" for g in historico)

    user_prompt = f"""Tema: {tema}{historico_str}

Com base no tema acima, crie o roteiro completo seguindo todas as regras do sistema.

CRÍTICO E OBRIGATÓRIO: VOCÊ DEVE RETORNAR APENAS E EXCLUSIVAMENTE O OBJETO JSON.
NÃO ESCREVA NENHUMA PALAVRA ANTES OU DEPOIS. NÃO ESCREVA RACIOCINIOS NEM EXPLICAÇÕES.
SUA RESPOSTA INTEIRA DEVE COMEÇAR COM A CHAVE E TERMINAR COM A CHAVE.

Retorne APENAS um JSON válido com esta estrutura exata (sem markdown, sem texto extra):
{{
    "titulo": "TÍTULO EM MAIÚSCULAS — impactante e curto (máx 55 chars)",
    "roteiro_fala": "Texto completo da narração. Tamanho ideal: 70 a 100 palavras. INCLUA emoções do Fish Audio no início de CADA frase usando colchetes (ex: [serious] A vida ensina..., [sad] E isso dói..., [hopeful] Mas Deus restaura...). Use palavras em INGLÊS para a emoção. Comece com o gancho forte. Encerre com Amém.",
    "b_roll": [
        {{"momento": "gancho (0-3s)", "keyword": "pastor podcast microphone studio"}},
        {{"momento": "corpo 1", "keyword": "lonely man walking road fog"}},
        {{"momento": "corpo 2", "keyword": "friends betrayal coffee shop"}},
        {{"momento": "conclusao", "keyword": "cross mountains sunrise hope"}}
    ],
    "palavras_chave_pexels": ["english keyword 1", "english keyword 2", "english keyword 3", "english keyword 4"],
    "hashtags_tema": ["#palavrachave1", "#palavrachave2", "#palavrachave3"]
}}

Para o campo "b_roll", gere entre 3 e 5 entradas mapeando cada parte do roteiro para uma cena de fundo ideal.
As keywords devem estar em INGLÊS, descritivas o suficiente para buscar no Pexels.

Para "palavras_chave_pexels", use termos em INGLÊS que combinem com o tema visualmente:
- Exemplos: "lonely wolf forest", "person walking alone road", "rainy night city", "dark ocean waves"
- Exatamente 4 palavras-chave

Para "hashtags_tema", gere EXATAMENTE 3 hashtags em português (sem espaços, sem acentos, letras minúsculas):
- Exemplos: #traicao #amizadefalsa #abandono #solidao #superacao #maturidade"""

    print("Chamando OpenRouter para gerar roteiro...")

    last_error = None
    result = None

    for modelo in MODELOS_GRATUITOS:
        try:
            print(f"  Tentando: {modelo}...")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=10.0,
                extra_headers={
                    "HTTP-Referer": "https://github.com/robsonvit/pr-claudio-videos",
                    "X-Title": "Pr Claudio Videos Bot",
                },
            )

            content = (response.choices[0].message.content or "").strip()
            print(f"  Resposta: {content[:200]}...")

            if not content:
                raise ValueError(f"{modelo} retornou conteúdo vazio")

            result = _extrair_json(content)
            print(f"  ✅ Roteiro gerado com sucesso via {modelo}")
            
            # Estratégia de velocidade: Move o modelo que funcionou para o topo da lista
            # Assim, no próximo vídeo dessa mesma rodada, ele será o primeiro a ser testado!
            if modelo in MODELOS_GRATUITOS:
                MODELOS_GRATUITOS.remove(modelo)
                MODELOS_GRATUITOS.insert(0, modelo)
                
            break

        except Exception as e:
            print(f"  ⚠️ Falhou com {modelo}: {e}")
            last_error = e
            continue

    if result is None:
        raise ValueError(f"Todos os modelos OpenRouter falharam. Último erro: {last_error}")

    result["tema"] = tema
    
    # Salva o novo gancho na memória
    if "roteiro_fala" in result:
        salvar_no_historico(result["roteiro_fala"])

    # Monta campo 'hashtags' unificado
    hashtags_tema = result.get("hashtags_tema", [])
    if isinstance(hashtags_tema, list) and hashtags_tema:
        hashtags_str = " ".join(hashtags_tema[:3]) + " #videoparastatus #reflexao"
    else:
        hashtags_str = "#videoparastatus #reflexao"
    result["hashtags"] = hashtags_str

    print(f"Titulo: {result['titulo']}")
    palavras = len(result['roteiro_fala'].split())
    print(f"Roteiro ({palavras} palavras): {result['roteiro_fala'][:80]}...")
    print(f"Keywords Pexels: {result['palavras_chave_pexels']}")
    print(f"Hashtags: {result['hashtags']}")

    return result


# ── Teste standalone ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--test" in sys.argv:
        print("Modo de teste — verificando conexao com OpenRouter...")
        tema = escolher_tema()
        roteiro = gerar_roteiro(tema)
        print("\nResultado:")
        print(json.dumps(roteiro, ensure_ascii=False, indent=2))
