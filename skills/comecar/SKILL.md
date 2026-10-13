---
name: comecar
description: Configura o canal do usuário a partir da ideia dele ("quero um canal de X com Y"): entrevista curta, cria canal.md e regras.md, sugere legenda, efeitos, formato de vídeo e voz, e instala o motor. Use na primeira conversa ou quando o usuário quiser mudar a cara do canal.
---
# Começar

1. Pergunte, em poucas mensagens (só o que ele ainda não disse):
   - Sobre o que é o canal e para quem (nicho e público). Exemplo de resposta: "motivação com cenas de anime, voz grave".
   - Fonte do conteúdo (Bíblia, animes, futebol, história, ciência...) e o que ele NÃO quer.
   - Tom (íntimo, épico, sombrio, engraçado, direto) e duração preferida.
   - Voz: própria, ElevenLabs ou Fish Audio (skill /voz). Fundo: GIFs/cenas que ele manda ou busca por nome (/edit-musica).
   - Redes e horários em que pretende postar.
2. Sugira o pacote inicial com o motivo de cada escolha: 1 legenda, 1 efeito (opcional) e 1 estilo de vídeo, olhando as skills
   instaladas (`.claude/skills/`) e o `exemplo.jpg` de cada uma. Exemplos:
   cristão → narração ou Shorts de GIF + Sample Yellow; motivação → Red Sharp + efeito sombrio; anime → edit com música + Street;
   futebol → edit com música + 3D Invisível.
3. Escreva `canal.md` (nicho, público, tom, fonte, o que evitar, legenda/efeito/formato padrão, voz, duração, horários) e
   `regras.md` (vazio no começo, com o título "O que o usuário aprovou e rejeitou").
4. Rode `bash motor/setup.sh` e resolva o que faltar.
5. Proponha o primeiro vídeo: chame o fluxo de `/roteiro` com 3 ideias de tema para ele escolher.
