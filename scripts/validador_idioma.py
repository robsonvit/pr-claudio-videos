"""
validador_idioma.py
Módulo responsável por aplicar a trava rígida de idioma Português do Brasil (PT-BR).
Impede terminantemente que qualquer roteiro, narração ou áudio em inglês (ou outro idioma)
seja processado, sintetizado ou postado pelo pipeline.
"""

import re
import sys
import unicodedata
from typing import Tuple, Dict, Any

# Força UTF-8 no stdout para evitar erros com emojis no console do Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Stopwords e palavras funcionais e comuns de alta frequência no Português do Brasil
STOPWORDS_PT = {
    # Artigos e pronomes
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "eu", "tu", "ele", "ela", "nos", "nós", "vos", "vós", "eles", "elas",
    "você", "voce", "vocês", "voces", "me", "te", "se", "lhe", "lhes", "nos",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "dele", "dela", "deles", "delas", "este", "esta", "estes", "estas",
    "esse", "essa", "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
    "isto", "isso", "aquilo", "quem", "que", "qual", "quais", "quanto", "quanta",
    # Preposições e conjunções
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "pelo", "pela", "pelos", "pelas", "para", "pra", "pro", "pras", "pros",
    "com", "sem", "sob", "sobre", "entre", "ate", "até", "desde",
    "e", "ou", "mas", "porem", "porém", "contudo", "todavia", "porque", "por que",
    "pois", "como", "se", "quando", "onde", "enquanto",
    # Verbos comuns e auxiliares
    "é", "e", "era", "foi", "ser", "sendo", "sido", "sou", "somos", "sao", "são",
    "está", "esta", "estava", "estar", "estou", "estamos", "estao", "estão",
    "tem", "têm", "tinha", "ter", "tenho", "temos", "tinham", "teve",
    "vai", "vou", "vamos", "vao", "vão", "foi", "foram", "ia", "ir",
    "pode", "podem", "podia", "posso", "podemos", "fazer", "faz", "fazem",
    "dizer", "diz", "dizem", "disse", "sabe", "sabem", "soube", "sei",
    "olha", "olhe", "presta", "preste", "escuta", "ouve", "ouça", "deixa",
    # Palavras do contexto evangélico / reflexão
    "deus", "senhor", "jesus", "cristo", "fé", "fe", "oracao", "oração", "amém", "amen",
    "coração", "coracao", "vida", "dor", "alma", "paz", "força", "forca", "esperança", "esperanca",
    "silêncio", "silencio", "noite", "dia", "medo", "verdade", "tempo", "mundo", "caminho",
    "bênção", "bencao", "milagre", "irmão", "irmao", "família", "familia", "filho", "filha",
    # Advérbios e outros
    "não", "nao", "sim", "mais", "muito", "pouco", "bem", "mal", "ja", "já",
    "ainda", "sempre", "nunca", "jamais", "aqui", "ali", "la", "lá", "agora", "hoje",
    "depois", "tudo", "nada", "alguém", "alguem", "ninguém", "ninguem", "algo", "coisa"
}

# Stopwords e palavras funcionais de alta frequência em Inglês
STOPWORDS_EN = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year",
    "your", "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also", "back",
    "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "god", "lord", "heart", "prayer", "amen", "faith", "hope", "walk", "walking",
    "night", "life", "pain", "today", "tomorrow", "never", "always", "stop", "listening",
    "remember", "hear", "listen", "silence", "father", "son", "family", "blessing"
}

# Caracteres acentuados fortemente característicos do Português
CARACTERES_PT = set("áéíóúâêôãõàüçÁÉÍÓÚÂÊÔÃÕÀÜÇ")


def remover_tags_emocao(texto: str) -> str:
    """Remove marcadores de emoção do Fish Audio como [serious], [sad], [hopeful]."""
    return re.sub(r'\[.*?\]', ' ', texto)


def extrair_tokens(texto: str) -> list[str]:
    """Extrai palavras limpas em minúsculas preservando acentos."""
    texto_sem_tags = remover_tags_emocao(texto)
    # Extrai tokens alfanuméricos incluindo letras com acentos
    palavras = re.findall(r'\b[a-zA-ZáéíóúâêôãõàüçÁÉÍÓÚÂÊÔÃÕÀÜÇ]+\b', texto_sem_tags.lower())
    return palavras


def analisar_idioma(texto: str) -> Dict[str, Any]:
    """
    Analisa a composição léxica do texto para distinguir Português vs Inglês.
    """
    texto_sem_tags = remover_tags_emocao(texto)
    palavras = extrair_tokens(texto)
    total_palavras = len(palavras)

    if total_palavras == 0:
        return {
            "valido": False,
            "motivo": "Texto vazio ou composto apenas por tags de emoção.",
            "total_palavras": 0,
            "palavras_pt": 0,
            "palavras_en": 0,
            "score_pt": 0.0,
        }

    # Contagem de palavras exclusivas ou fortemente indicativas de cada idioma
    # Palavras que existem nos dois conjuntos (ex: 'a', 'no', 'me', 'amen') não desempatam sozinhas
    ambiguas = STOPWORDS_PT.intersection(STOPWORDS_EN)
    
    palavras_pt = sum(1 for p in palavras if p in STOPWORDS_PT and p not in ambiguas)
    palavras_en = sum(1 for p in palavras if p in STOPWORDS_EN and p not in ambiguas)
    
    # Detecção de caracteres com acentos do português
    acentos_encontrados = sum(1 for char in texto_sem_tags if char in CARACTERES_PT)

    return {
        "valido": True,
        "total_palavras": total_palavras,
        "palavras_pt": palavras_pt,
        "palavras_en": palavras_en,
        "acentos_pt": acentos_encontrados,
    }


def validar_roteiro_ptbr(roteiro_fala: str, titulo: str = "") -> Tuple[bool, str]:
    """
    TRAVA OBRIGATÓRIA PT-BR:
    Valida se o roteiro da narração (e título opcional) está em Português do Brasil.
    
    Retorna:
        (True, "OK") se o texto for validado como Português do Brasil.
        (False, motivo) se for detectado em Inglês ou outro idioma inválido.
    """
    if not roteiro_fala or not roteiro_fala.strip():
        return False, "O texto do roteiro de fala está completamente vazio."

    analise = analisar_idioma(roteiro_fala)
    if not analise["valido"]:
        return False, analise["motivo"]

    total = analise["total_palavras"]
    pt = analise["palavras_pt"]
    en = analise["palavras_en"]
    acentos = analise["acentos_pt"]

    # 1. Checagem de tamanho mínimo
    if total < 20:
        return False, f"Roteiro muito curto ({total} palavras). Esperado no mínimo 30 palavras."

    # 2. Se as palavras em inglês superarem as em português, é inglês com certeza
    if en > pt:
        return False, f"DETECTADO INGLÊS: Encontradas {en} palavras funcionais em inglês contra apenas {pt} em português."

    # 3. Se tiver palavras em inglês significativas e quase nada em português
    if en >= 5 and pt < 3:
        return False, f"DETECTADO INGLÊS: Alta densidade de termos em inglês ({en}) e quase nenhum termo em português ({pt})."

    # 4. Deve conter um número mínimo aceitável de palavras em português
    # Para um texto de 50-100 palavras, espera-se pelo menos 6-8 palavras funcionais de PT
    limite_minimo_pt = max(4, int(total * 0.08))
    if pt < limite_minimo_pt and acentos == 0:
        return False, f"Poucos indicadores de português ({pt} palavras funcionais, 0 acentos). Texto suspeito de não ser PT-BR."

    # 5. Validação do título (se fornecido)
    if titulo:
        titulo_tokens = extrair_tokens(titulo)
        ambiguas = STOPWORDS_PT.intersection(STOPWORDS_EN)
        tit_pt = sum(1 for p in titulo_tokens if p in STOPWORDS_PT and p not in ambiguas)
        tit_en = sum(1 for p in titulo_tokens if p in STOPWORDS_EN and p not in ambiguas)
        if tit_en > tit_pt and tit_en >= 3:
            return False, f"DETECTADO TÍTULO EM INGLÊS: '{titulo}' contém termos em inglês."

    return True, "Texto validado com sucesso em Português do Brasil (PT-BR)."


def validar_ou_levantar_erro(roteiro_fala: str, titulo: str = "") -> None:
    """
    Dispara RuntimeError se o texto não passar na trava PT-BR.
    Útil como guardrail imediato antes de invocar APIs de voz ou renderização.
    """
    valido, motivo = validar_roteiro_ptbr(roteiro_fala, titulo)
    if not valido:
        raise RuntimeError(
            f"🚨 [TRAVA PT-BR ATIVADA - EXECUÇÃO ABORTADA]:\n"
            f"O conteúdo foi rejeitado porque NÃO está em Português do Brasil!\n"
            f"Motivo: {motivo}\n"
            f"Texto recebido (primeiros 200 caracteres): {roteiro_fala[:200]!r}"
        )


if __name__ == "__main__":
    # Testes unitários para validar a trava
    print("Executando testes do validador de idioma...")
    
    # Exemplo 1: Texto legítimo em PT-BR com tags Fish Audio
    exemplo_pt = (
        "[serious] Sabe aquele silêncio que pesa mais que a culpa? [sad] Eu fico à noite, "
        "olhando pro teto, perguntando se alguém me ouve. [hopeful] Mas Deus está preparando "
        "uma resposta para você. Aguenta firme e confia. Amém."
    )
    ok, mot = validar_roteiro_ptbr(exemplo_pt, "O SILÊNCIO QUE CURA")
    assert ok, f"Falha no teste PT: {mot}"
    print("  ✅ Teste PT-BR legítimo: APROVADO")

    # Exemplo 2: Texto em Inglês com tags Fish Audio
    exemplo_en = (
        "[serious] Do you know that silence that hurts more than guilt? [sad] I stay up at night, "
        "looking at the ceiling, wondering if anyone hears me. [hopeful] But God is preparing "
        "an answer for you. Hold on tight and trust. Amen."
    )
    ok_en, mot_en = validar_roteiro_ptbr(exemplo_en, "THE SILENCE THAT HEALS")
    assert not ok_en, "Falha: Texto em inglês deveria ser rejeitado!"
    print(f"  ✅ Teste Inglês bloqueado com sucesso: {mot_en}")

    # Exemplo 3: Texto misturado que tenta burlar
    exemplo_misto = (
        "You need to know that your life is hard. Sometimes you feel alone. "
        "God is always with you in the darkest night."
    )
    ok_misto, mot_misto = validar_roteiro_ptbr(exemplo_misto)
    assert not ok_misto, "Falha: Texto em inglês sem tags deveria ser rejeitado!"
    print(f"  ✅ Teste Inglês puro bloqueado com sucesso: {mot_misto}")

    print("\n🎉 Todos os testes unitários do validador PT-BR passaram com sucesso!")
