# Contexto do projeto

## Atualização coordenada — 16 de novembro de 2026

O titular definiu preferência por coleta assistida diretamente das fontes a cada pedido de atualização, sem exportação manual Scopus como rotina. Preparados `scripts/update_sources.py` (entrada única e relatório privado) e `scripts/scopus_client.py` (coleta oficial de perfil, documentos paginados e citações anuais). O fluxo preserva revisão editorial, catálogos aprovados e publicação separada.

A execução real localizou a exportação privada do Lattes e preparou artigos, orientações e funções editoriais sem gravar catálogos. O conector Scopus passou em testes sintéticos, mas não foi validado com acesso real: faltam credenciais API no ambiente. Não houve nova coleta Scopus nem mudança nos números exibidos. Consulte [UPDATE_WORKFLOW.md](UPDATE_WORKFLOW.md) para configuração inicial, inventário de fontes e limites.


## Scopus — 16 de novembro de 2026

Incluído snapshot datado de indicadores no bloco Publicações, nos quatro idiomas. Perfil confirmado por Scopus ID 57195100508, nome, UnB e ORCID. Última observação acessível em 15/11/2026: 87 documentos, 1.243 citações, 572 documentos citantes, H=22. Nova consulta em 16/11 exigiu login; o titular confirmou acesso institucional. A data anterior foi mantida, sem alegação de atualização em tempo real.

Fonte agregada em `content/scopus.json`, validação no build e componente `site/scopus-metrics.js`. Estrutura de gráficos e tabelas acessíveis preparada, mas séries anuais continuam ausentes e não são estimadas. Aguarda exportação institucional ou acesso API autorizado. Não foram alterados os 50 artigos do catálogo nem os indicadores do CV. Consulte [SCOPUS_METRICS.md](SCOPUS_METRICS.md) para fonte, cobertura, limitações e próximos insumos.


## CV ativo no idioma do visitante — 15 de novembro de 2026

O titular aprovou os cinco artigos discutidos (incluindo a revisão 4E em RSER) e autorizou o link do CV no site local. `content/cv.json` passou para aprovado com referências DOI. O botão da seção Sobre segue EN/PT/FR/ZH e a preferência restaurada ao recarregar. Os documentos imprimíveis são gerados no mesmo build do site; o visitante usa Imprimir/Salvar como PDF. Títulos originais e ano editorial de 2022 preservados; citações do CV usam primeiro autor e et al., sem alterar o catálogo.

A auditoria abriu os quatro documentos pelo endereço correspondente ao seletor, conferiu idioma HTML, cinco artigos e estilo de impressão. Os 50 testes Python e a auditoria completa do site passaram. Isso autoriza a prévia local, não a publicação no GitHub Pages. A paginação final do PDF continua sujeita à revisão de impressão.


## Arquitetura do CV resumido — 15 de novembro de 2026

Preparada a geração conjunta do CV e do site a partir dos catálogos aprovados. `content/cv.json` mantém apenas estado editorial e seleção de referências, atualmente rascunho sem artigos selecionados. `scripts/cv_document.py` projeta campos públicos permitidos, calcula indicadores, resolve referências bibliográficas e gera documentos de impressão EN/PT/FR/ZH. `scripts/preview_cv.py` produz a revisão fora do repositório; o build só gera `dist/cv/` e inclui o link na seção Sobre quando o CV estiver explicitamente aprovado e tiver seleção válida.

O fluxo é XML privado → simulação/comparação → aprovação → catálogos revisados → build conjunto. Importadores permanecem inalterados; simulação não modifica o CV. Novos artigos alteram o total sem substituir a seleção. Metadados corrigidos são reutilizados, e referências ausentes ou ambíguas exigem revisão. A exportação PDF usa a impressão do navegador sobre HTML estático A4; não há novo serviço ou dependência de build. Conteúdo, seleção de até cinco artigos e paginação final aguardam revisão. Consulte [SHORT_CV.md](SHORT_CV.md) para fontes, comandos, limites e critérios.


## Francês e chinês simplificado — 15 de novembro de 2026

O titular autorizou francês e chinês simplificado como idiomas adicionais. O site agora oferece EN / PT / FR / 中文 com bandeiras SVG decorativas e nomes acessíveis. Inglês permanece padrão; a preferência local inclui os quatro idiomas. `siteLanguage()` centraliza a seleção e o HTML utiliza en, pt-BR, fr e zh-Hans.

Foram traduzidas 288 entradas da interface por idioma, quatro projetos, áreas e 14 resumos temáticos de orientações em andamento, programas de pós-graduação e descrições/papéis das quatro cooperações. Títulos originais de artigos, teses e dissertações, nomes de pessoas, DOIs e URLs foram preservados. Nomes próprios institucionais podem permanecer em sua forma original. Não houve alteração no importador ou nos registros bibliográficos.

Os renderizadores de mapas, projetos, orientações e atividades editoriais usam o idioma central. A validação do build verifica paridade de chaves e marcadores de interpolação nos quatro idiomas. Os esquemas permitem os campos traduzidos sem liberar dados privados adicionais. O cabeçalho usa menu recolhido até 1450 pixels e duas linhas em telas pequenas; o chinês utiliza fontes CJK do sistema.

Validação: 39 testes Python aprovados, build e sintaxe JavaScript; auditoria Chrome com interface e conteúdos dinâmicos FR/ZH, preferência persistida, preservação dos títulos, filtros, mapas, rede interativa, teclado, toque e larguras de 320 a 1920 pixels nos quatro idiomas. Prévia permanece local. Traduções elaboradas nesta etapa ainda devem receber conferência editorial do titular e, especialmente para o chinês, revisão por pessoa fluente antes da publicação. Esta atualização amplia a decisão bilíngue original, mantida no histórico abaixo.


## Revisão dos temas da rede — 15 de novembro de 2026

Aprovada pelo titular a revisão dos cinco temas centrais: Bioenergia; Conversão termoquímica; Modelagem e otimização; Hidrogênio e biocombustíveis; Avaliação energética e ambiental. Os quatro primeiros exibem cinco conceitos secundários cada. O último exibe seis: análise exergética e 4E, ACV, contabilidade de carbono, pegada de carbono, quantificação de emissões e créditos de carbono/CBIOs. Rótulos com paridade EN/PT em `content/translations.json`.

A proposta foi baseada nos títulos dos 50 registros do catálogo e em PDFs correspondentes a 34 artigos da pasta privada Publicacoes, com palavras-chave extraídas de 31 deles. A cobertura não foi exaustiva; referências de terceiros e pareceres foram excluídos. Carbono e CBIOs foram acrescentados por orientação explícita do titular, sem atribuir esses temas a artigos específicos. A rede continua conceitual; não oferece calculadora, geração ou certificação de créditos. Nenhum PDF ou arquivo privado foi incorporado ao repositório.


## Movimento e arraste da rede — 15 de novembro de 2026

A rede ganhou deslocamento suave com molas ancoradas, repulsão entre temas e conexões que acompanham os pontos. O arraste por Pointer Events fica restrito aos botões dos temas; o restante da página mantém a rolagem. Ao soltar, o tema permanece selecionado; outros nós se acomodam. As setas movem o tema em foco, e Escape ou Visão geral restauram as posições. O botão Pausar/Retomar permite interromper a animação. A preferência `prefers-reduced-motion` desativa o movimento automático, mantendo a exploração e o arraste manual. A animação também para fora da área visível, em aba oculta e no diagrama original. As palavras-chave acompanham o deslocamento, com limites na área do gráfico.

Testes de navegador ampliados: flutuação real, pausa, mudança dinâmica da preferência de movimento, arraste por mouse e toque, rastreamento das arestas, movimento por setas e restauração após o arraste. Os controles da rede tratam a ativação por toque sem depender de um clique de compatibilidade após a captura do ponteiro. Catálogos e relações acadêmicas permanecem inalterados; não houve publicação.

## Protótipo de rede de pesquisa — 15 de novembro de 2026

A apresentação inicial inclui uma rede conceitual explorável de cinco temas: bioenergia, conversão termoquímica, hidrogênio, modelagem numérica e avaliação ambiental. `site/research-network.js` controla seleção, prévia por mouse e foco, palavras-chave, Escape, redefinição e comparação com o diagrama original preservado no HTML. Os textos e palavras-chave bilíngues ficam em `content/translations.json` (prefixo `graph`). A geometria é estável e usa SVG e botões HTML, sem biblioteca ou serviço externo. O movimento respeita a preferência por redução de animações.

As arestas são relações temáticas conceituais do protótipo; não comprovam associações entre publicações, projetos ou orientações. Nenhum catálogo foi alterado. O controle “Original diagram / Diagrama original” permite comparar as versões; sem JavaScript, o diagrama original permanece disponível. A adoção definitiva depende da avaliação visual do titular.

Validação: 37 testes Python, build e sintaxe JavaScript; auditoria Chrome com seleção, teclado, Escape, EN/PT, toque, alternância de diagrama e responsividade entre 320 e 1920 pixels, além dos filtros e mapas existentes.


## Navegação e consulta V2.7 — 15 de novembro de 2026

O menu agora reúne Orientações e Atuação Editorial em “Academic Activities / Atuação Acadêmica”. O grupo é expansível por teclado e toque, fecha com Escape e direciona o foco para a seção escolhida. Em telas de até 1100 pixels, a navegação usa o menu móvel. A consulta bibliográfica combina texto (título, autor, periódico ou DOI), ano e categoria, mantendo as seleções ao alternar EN/PT.

As áreas das orientações continuam sem associações individuais aprovadas. O filtro fica desativado nesse estado e a interface explica o critério. O ano filtra os trabalhos concluídos. Os catálogos acadêmicos permanecem com 50 artigos, 27 orientações, quatro projetos, quatro vínculos e sete registros editoriais e de revisão. Consulte a [auditoria V2.7](REVISAO_NAVEGACAO_V27.md) para os testes e os limites da conferência.

## Orientações em andamento aprovadas em 15 de novembro de 2026

O titular confirmou os 14 registros em andamento e os resumos temáticos bilíngues apresentados para revisão. O catálogo passou a reunir 27 orientações de pós-graduação, com 13 concluídas e 14 em andamento (cinco mestrados e nove doutorados). Ricardo Barbosa Scalabrini consta como coorientação. Os demais registros em andamento são orientações. Foram usados os resumos aprovados em lugar dos títulos provisórios. Datas e associações a áreas, projetos e publicações continuam sem preenchimento nesses registros, pois não fizeram parte da aprovação.

## Orientações aprovadas em 15 de novembro de 2026

O catálogo local reúne 13 orientações concluídas, sendo 12 mestrados e um doutorado. Os oito casos antes pendentes foram confirmados pelo titular. Há 12 links permanentes da UnB. O mestrado de Genilson Maia Corrêa, coorientado na UFLA, permanece sem link. Foram adotados os títulos das fichas institucionais da UnB e preservado o nome Isabella de Andrade Sá. Paloma é apresentada como Paloma Fachinelli de Oliveira. Valtrudes Pereira Franco está classificado como doutorado por confirmação do titular. A aprovação abrange os trabalhos concluídos.

## Estado bibliográfico em 14 de novembro de 2026

O catálogo local contém 50 artigos, após a incorporação aprovada de 45 novos registros. Os cinco artigos anteriores mantêm seus metadados e categorias. O DOI 10.1016/j.energy.2021.122208 conserva o ano bibliográfico 2022. O artigo de 2017 sem DOI foi incluído. Dois registros de 2027 continuam reservados no relatório de conferência. As categorias dos novos registros são as sugestões temáticas do importador e podem receber revisão editorial. O site permanece em desenvolvimento local.

## Identidade acadêmica

Edgar A. Silveira (Edgar Amaral Silveira) é professor da Universidade de Brasília (UnB), vinculado ao Departamento de Engenharia Mecânica, ao Programa de Pós-Graduação em Ciências Mecânicas (PCMEC) e ao Laboratório de Energia e Ambiente (LEA). Suas áreas de pesquisa incluem bioenergia, conversão termoquímica, hidrogênio, modelagem numérica, transferência de calor, análise exergética e avaliação ambiental.

## Decisões aprovadas

- Site acadêmico profissional e bilíngue, com inglês como padrão e português do Brasil como alternativa.
- Identidade visual V2 preservada na V2.1. O site reúne apresentação, trajetória acadêmica, pesquisa, publicações, projetos, rede institucional, cooperação e internacionalização, e contato.
- Mapas interativos do Brasil e do mundo para explorar instituições, pessoas e tipos de vínculo.
- Atualização de publicações com exportações locais do Currículo Lattes, separando metadados públicos de arquivos originais e dados privados.
- Conteúdo acadêmico separado da apresentação, controle de versões pelo Git e hospedagem gratuita prevista no GitHub Pages.

## Arquitetura da V2.1

| Componente | Responsabilidade |
| --- | --- |
| `content/profile.json` | Nomes, e-mail institucional, links e URL-base usada pelo build. |
| `content/translations.json` | Textos gerais EN/PT, ligados ao HTML por `data-i18n`. |
| `content/publications.json` | Catálogo bibliográfico, categorias e DOIs. |
| `content/projects.json` | Temas e projetos com campos bilíngues, status e indicação de divulgação. |
| `content/collaborations.json` | Vínculos, instituições, pessoas, coordenadas, idiomas, escopo e status. |
| `site/index.html`, `site/styles.css`, `site/assets/` | Estrutura da página, identidade V2, responsividade, mapas SVG incorporados, favicon e capa social. A página solicita fontes ao Google Fonts. |
| `site/app.js` | Idioma, preferência em `localStorage`, menu móvel, estado dos filtros, título e descrição da página. |
| `site/site-data.js`, `site/project-cards.js` | Renderização dos mapas, publicações e cartões bilíngues de projetos. |
| `scripts/build.py` | Valida os JSONs. Copia `site/` para a saída, gera os dados JS, preenche marcadores do HTML e cria `robots.txt`, `sitemap.xml` e `.nojekyll`. |
| `scripts/import_lattes.py` | Extrai metadados de artigos publicados de um XML ou ZIP com exatamente um XML, com opção de prévia. |
| `tests/test_pipeline.py` | Sete testes de integridade, privacidade básica, estrutura, tradução e importação sintética. |
| `.github/workflows/pages.yml`, `.gitignore` | Pipeline de testes, build e deploy, e exclusões locais para saídas geradas e formatos comuns de arquivos privados. |
| `dist/` | Artefato gerado que pode ser servido como site estático. |

## Operação

O build usa a biblioteca padrão do Python. O navegador carrega os dados gerados em `dist/data/` e os scripts do site. Inglês é o padrão quando não há preferência salva. O mapa mundial destaca e permite selecionar países com vínculos públicos. O mapa brasileiro agrupa as instituições por cidade e o marcador leva ao primeiro cartão do grupo na lista do Brasil. Os controles de país e cidade têm handlers de clique, Enter e Espaço. O build inclui apenas colaborações e projetos marcados para divulgação. O catálogo de publicações é enviado integralmente ao navegador.

Para preparar uma atualização bibliográfica, execute `python scripts/import_lattes.py "CAMINHO_PRIVADO" --dry-run`. O importador lê apenas artigos publicados e usa DOI normalizado ou, na ausência de DOI, título normalizado. Na operação padrão, mantém registros antigos sem correspondência. Nos itens correspondentes, copia um conjunto fixo de campos editoriais. Execute a importação com escrita somente no escopo autorizado e revise o JSON resultante antes de versionar.

O fluxo local usa `python -B -m unittest discover -s tests -v` e `python -B scripts/build.py --check`. Em uma tarefa que autorize a regeneração de `dist/`, execute `python scripts/build.py` e sirva a saída com `python -m http.server 8000 --directory dist`.

O workflow executa testes e build com Python 3.12 em Ubuntu. Pull requests para `main` passam pela validação. Pushes e execuções manuais em `main` podem publicar o artefato no ambiente `github-pages`. A configuração planejada usa o repositório `EdUnB/edunb.github.io`, o endereço `https://edunb.github.io/` e GitHub Actions como origem do Pages. A URL no perfil é uma configuração, sem comprovação de publicação.

## Auditoria local de 8 de novembro de 2026

- A pasta aberta contém a V2.1 e uma cópia do build, sem repositório Git detectado. A configuração remota e o estado de publicação ficaram sem verificação.
- O conteúdo tem cinco publicações selecionadas, quatro temas de pesquisa e quatro vínculos sinalizados para divulgação. Há dois vínculos em Brasília e dois na França. Os registros de pesquisadores estão no vínculo acadêmico histórico com a Université de Lorraine. Os vínculos e perfis requerem revisão do titular para o lançamento.
- Os sete testes passaram com Python 3.14 após redirecionar `TMPDIR` para uma pasta temporária gravável. A primeira execução esbarrou na permissão do diretório temporário padrão. A validação sem escrita e a sintaxe dos JavaScripts passaram. O build isolado reproduziu os 15 arquivos de `dist/`, com diferenças apenas nas quebras de linha de oito arquivos.
- As 111 chaves EN/PT coincidem. Todas as 95 chaves distintas usadas pelo HTML têm entradas em ambos os idiomas. Há 16 chaves sem uso no HTML. Permanecem em inglês rótulos acessíveis de navegação e mapas, rótulos de categorias bibliográficas e outros textos fixos. Os países do catálogo estão no SVG, e nomes traduzidos no painel estão cadastrados apenas para Brasil, França e Portugal.
- O importador aceitou um ZIP sintético com um XML e rejeitou um ZIP com dois. O catálogo local permaneceu intacto. Um XML sintético com DTD foi rejeitado em UTF-8 e aceito em UTF-16, pois a checagem procura tokens ASCII no arquivo bruto. O XML real do Lattes e a importação com escrita ficaram fora da verificação.
- A deduplicação usa chaves distintas para registros com e sem DOI. Um artigo anterior sem DOI pode ser mantido em duplicidade ao receber um DOI em outra importação. O filtro aceita categorias específicas no HTML, mas `other`, categoria de fallback do importador, só aparece em “Todos”. O importador preserva `title_override` e `journal_override` quando presentes, mas a página exibe `title` e `journal`.
- O cartão de um vínculo histórico usa o rótulo de vínculo acadêmico antes de avaliar o escopo. Assim, parcerias institucionais históricas recebem o rótulo de vínculo acadêmico no cartão, embora a descrição identifique o projeto do LEA. Os links de perfis individuais do LEA e PCMEC no contato são fixos no build, enquanto as URLs institucionais vêm do JSON do perfil.
- A revisão da interface foi feita no código e no artefato gerado. Navegação em browser, teclado, responsividade, leitores de tela e resolução de links externos ainda precisam de homologação.

## Próximas etapas sujeitas à aprovação

1. Corrigir a rejeição de DTD e entidades independentemente da codificação e conferir deduplicação e preservação de correções com casos de regressão sintéticos.
2. Homologar a interface em EN/PT, teclado e celular. Priorizar os rótulos acessíveis e a distinção dos vínculos históricos no mapa, preservando a identidade V2.
3. Revisar credenciais, links e DOIs, catálogo, nomes e autorização dos vínculos antes do lançamento.
4. Definir com o titular como conectar esta pasta ao Git e validar o workflow remoto. Configurar o Pages e executar o primeiro deploy após aprovação específica.

## Documentação existente

- [README](../README.md) e [histórico de versões](../CHANGELOG.md)
- [Decisões técnicas](DECISOES_TECNICAS.md)
- [Fluxo de atualização](FLUXO_ATUALIZACAO.md)
- [Guia Windows](GUIA_WINDOWS.md)
- [Instruções do Projeto ChatGPT](INSTRUCOES_PROJETO_CHATGPT.md)

## Registro técnico da V2.3 — Cooperações e revisão bilíngue

Os achados da auditoria V2.1 acima registram o estado daquela versão. Na V2.3, o build valida escopo, situação, divulgação, coordenadas e metadados. O navegador usa os registros públicos para sincronizar o mapa-múndi, os marcadores do Brasil e os seletores de país e cidade. Cada cartão expansível agrupa os vínculos da mesma instituição na cidade selecionada. O seletor de cidades do mapa-múndi oferece acesso a cidades de outros países. Países e marcadores têm suporte a Enter e Espaço, e os seletores e cartões usam controles HTML nativos.

| Escopo | Situações aceitas | Regra editorial |
| --- | --- | --- |
| `personal` | `active`, `completed` | Cooperação científica pessoal confirmada. |
| `institutional` | `active`, `completed`, `historical`, `documented` | Parceria institucional. Informe `institutional_owner` como `LEA` ou `UnB`. |
| `academic` | `active`, `completed`, `historical`, `documented` | Formação acadêmica ou mobilidade. |
| `research` | `documented` | Interação documentada cujo escopo pessoal ou situação atual não foi confirmado. |
| `negotiation` | `pending` | Exige `public: false`. Após aprovação e confirmação, classifique o vínculo antes de marcá-lo para divulgação. Mantenha negociações e dados privados fora do repositório público. |

Cada registro mantém ID, país ISO-3, cidade, coordenadas, nome da instituição, descrição EN/PT e lista `people` (vazia quando não há pessoas confirmadas). A lista aceita nome, `role_en`, `role_pt` e URL HTTPS opcional. Os campos opcionais incluem `topic` com `en` e `pt`, `period` com ano inicial `start` e/ou final `end`, `publications` com `title` e `url`, `website` e `links` com `label` bilíngue e `url`. Use o título original das publicações.

O LPF permanece como interação de pesquisa documentada. Embrapa e CIRAD continuam como parcerias institucionais históricas. Seus campos estruturados de titularidade (LEA) e período (2019–2023) reproduzem as descrições existentes do projeto PODA. A Université de Lorraine permanece como vínculo histórico de formação, com os mesmos pesquisadores e papéis. Nenhum pesquisador ou vínculo foi acrescentado.

Os rótulos estáticos ficam em `content/translations.json` e são associados a `data-i18n` ou `data-i18n-aria-label`. Os textos dinâmicos dos filtros, mapas e detalhes usam as mesmas traduções. A troca de idioma mantém a seleção atual de país e cidade, os cartões abertos e o filtro bibliográfico. O idioma inicial continua sendo inglês.

Validação local da V2.3 em 8 de novembro de 2026. Os 23 testes automatizados, o build e a verificação de sintaxe JavaScript passaram. No Chrome, foram conferidos o percurso por teclado e a troca de idioma a 1440 × 900, e o percurso por toque, o menu e a largura da página a 390 × 844 em emulação móvel. A validação com leitor de tela e aparelho físico permanece pendente.

## Registro técnico da V2.4 — Orientações acadêmicas

A seção `#supervision` apresenta orientações concluídas, orientações em andamento, linhas de pesquisa e atividades complementares de graduação. Os indicadores e filtros de nível, situação, ano e área são calculados a partir dos itens aprovados de pós-graduação. Iniciação científica e TCC aparecem em uma lista separada. As linhas de pesquisa descrevem áreas de atuação.

`scripts/import_supervisions.py` reaproveita o leitor protegido de XML/ZIP do importador bibliográfico. Por padrão, imprime apenas contagens. O comando abaixo gera um novo JSON privado e permite comparar com uma revisão anterior sem sobrescrevê-la.

```powershell
python -B scripts/import_supervisions.py "CAMINHO_PRIVADO_EXPORTACAO.xml" --review-output "CAMINHO_PRIVADO_NOVA_REVISAO.json"
python -B scripts/import_supervisions.py "CAMINHO_PRIVADO_NOVA_EXPORTACAO.xml" --previous "CAMINHO_PRIVADO_REVISAO_ANTERIOR.json" --review-output "CAMINHO_PRIVADO_NOVA_REVISAO.json"
```

A revisão separa `source` (campos extraídos) e `editorial` (correções manuais). O cruzamento usa estudante, nível, instituição e programa, com título, situação e ano para distinguir registros. Uma defesa provável requer correspondência única e ano de conclusão igual ou posterior ao ano em andamento. Mudanças voltam a `pending`. Casos ambíguos e registros ausentes da exportação são preservados na revisão privada. Identificadores Lattes, dados de bolsas e anotações internas são excluídos da extração.

Após aprovação, transfira manualmente os campos públicos revisados para `content/supervisions.json`, com ID estável e `approved: true`. Use `title` original e ano de defesa para concluídas, e `topic` com apenas `en` e `pt` para registros em andamento. Use `areas` para IDs das linhas de pesquisa, `publications` para DOIs do catálogo e `projects` para IDs de projetos públicos. Essas referências são opcionais e exigem confirmação. Links de repositório de trabalhos concluídos exigem `repository_verified: true` e HTTPS. O campo `role` distingue orientação e coorientação e é obrigatório para pós-graduação.

A primeira extração real identificou 12 mestrados e um doutorado concluídos, cinco mestrados e nove doutorados em andamento, 12 iniciações científicas concluídas, 18 TCCs concluídos e dois em andamento. Todos os 59 registros ficaram pendentes de revisão editorial. Três registros de iniciação científica não informam programa. O tipo de orientação não foi indicado para os 32 registros complementares. A exportação não forneceu links de repositório para teses e dissertações concluídas. O catálogo público inicial contém apenas as cinco áreas de pesquisa.

A validação local executou 30 testes e conferiu no Chrome a prévia pública e uma amostra sintética em inglês e português. Os filtros foram acionados por teclado a 1440 × 900, a largura foi conferida a 1024 px e o menu por toque foi testado em emulação de 390 × 844.

## Registro técnico da V2.5 — Atuação editorial e repositório institucional

`scripts/compare_lattes.py ANTIGO NOVO` reutiliza a extração segura de XML/ZIP, o pareamento bibliográfico e a revisão de orientações. A saída padrão mostra contagens e equivalência das seções. `--review-output` guarda detalhes fora do repositório. Use `--manual` com uma lista privada de registros identificados por periódico e papel, com as correções em `editorial`, para sobrepor a referência manual padrão de `content/editorial.json` na revisão. Alterações de período, ausências e mudanças de DOI ficam disponíveis para conferência. O comparador não escreve nos catálogos públicos.

`scripts/find_unb_supervisions.py EXPORTACAO --cache DIRETORIO_PRIVADO` descobre candidatos no índice de orientador da UnB. Consulte `--handle 10482/NUMERO` para acrescentar coorientações ou itens conhecidos que não estejam no índice. A consulta usa OAI-PMH com metadados DIM, com leitura da ficha completa quando faltarem campos estruturados. A busca externa envia somente a consulta pelo orientador e os handles. A comparação com estudante e título ocorre localmente. O cache dura sete dias, com intervalo mínimo de um segundo entre pedidos. Use `--refresh` para atualizar e `--offline` para exigir dados em cache. Repita após defesas, novas exportações e em revisões de itens ainda não encontrados. Uma execução incompleta não deve ser tratada como ausência.

Para transferir links confirmados e aprovados, use a página permanente em `repository_url` e marque `repository_verified: true` no registro aprovado de `content/supervisions.json`. A interface distingue tese e dissertação em EN/PT. `content/editorial.json` aceita somente registros aprovados, agrupados em funções, revisão e contribuições. O campo opcional `logo` referencia imagem autorizada em `site/assets/`.

O menu principal permanece como na V2.4. O acesso à nova seção aparece na área institucional. Como proposta para uma etapa futura, um único grupo “Academic Activities / Atuação Acadêmica” poderia reunir Orientações e Atuação Editorial em uma lista acessível por teclado e toque. A alteração do menu depende de aprovação.

Consulte o [relatório da conferência V2.5](CONFERENCIA_ACADEMICA_V25.md) para os resultados da comparação e da consulta à UnB.


## Mapa individual da França — 16/11/2026

A seção de cooperações mantém mundo e Brasil e acrescenta França metropolitana e La Réunion em quadro separado, com escala e posição próprias. Geometria Natural Earth 1:10m, domínio público (https://www.naturalearthdata.com/about/terms-of-use/), recortada e simplificada em `site/assets/france-map.svg`. As projeções do SVG também posicionam os marcadores. O build incorpora o SVG e valida suas traduções. O campo opcional `territory` aceita MET/REU somente para FRA; registros antigos são classificados pelas coordenadas. Não foram alterados os vínculos públicos. Seleção territorial, cidades e instituições funciona por teclado e toque em EN/PT/FR/ZH. La Réunion permanece sem registros até confirmação.

Levantamento BRAFITEC e coautorias foi guardado fora do repositório para revisão. Participação institucional e afiliação em artigo não comprovam colaboração pessoal ativa. Foram aprovados 75 testes Python, build e auditoria Chrome de 320 a 1920 px. Não houve publicação.


## Coautorias selecionadas no mapa — 16/11/2026

Após aprovação da lista e suas exclusões pelo titular, incorporados 23 registros de coautoria a `content/collaborations.json`, preservando os quatro registros anteriores (27 registros no total). Países: Brasil, França, Portugal, Taiwan e Finlândia. Não incluídos Moçambique, Tailândia, Tunísia, Embrapa Milho e Sorgo, Censipam, Science Inovatech/Florianópolis, Unicamp, USP/Esalq ou UFU. A USP/Escola Politécnica/LaSPE permanece.

Coautorias usam `scope: research` e `status: documented`, com papéis traduzidos, afiliações conforme os artigos e links DOI cujos títulos derivam do catálogo existente. Não são declaradas automaticamente como parcerias institucionais ativas. Instituições com múltiplas unidades são agrupadas quando cidade e nome coincidem; cidades distintas têm entradas próprias. Afiliações múltiplas de uma pessoa são preservadas. O LERMAB aparece em Épinal conforme o artigo; o registro acadêmico histórico de Nancy permanece. BioWooEB/Université de Montpellier é explicitada na descrição da afiliação conjunta ao CIRAD. Não incluídos os nomes ainda sem afiliação conferida (Mounir Chaouch e Jérémy Valette). BRAFITEC e La Réunion aguardam detalhamento aprovado antes de novos registros.

Coordenadas novas representam centros aproximados das cidades, não endereços de campus. Marcadores próximos recebem deslocamento visual com linha até a posição geográfica, para manter a seleção por teclado e toque. No Brasil, com muitas cidades, nomes aparecem ao passar o mouse, focar ou selecionar; os nomes acessíveis e o seletor de cidades permanecem disponíveis.

Validação: 79 testes Python aprovados, `scripts/build.py --check` aprovado e auditoria Chrome EN/PT/FR/ZH com filtros, países, coautores, DOI, teclado, toque e larguras 320–1920 px aprovada. Atualizada somente a prévia local em 127.0.0.1:8000. Sem alteração de publicações, importadores ou publicação remota.


## Simplificação dos pontos e BRAFITEC — 16/11/2026

Por solicitação do titular, retirados números, deslocamentos e linhas conectoras. Pontos pequenos permanecem nas coordenadas aproximadas das cidades; nomes aparecem no hover, foco ou seleção. Verde representa vínculos acadêmicos/científicos; dourado indica cidade com cooperação institucional BRAFITEC. Nancy mantém tanto o vínculo acadêmico anterior quanto Mines Nancy no painel. A identificação textual BRAFITEC e a legenda complementam a cor. Corrigido também o conflito entre seleção territorial e marcadores: somente `.france-territory` recebe o estado do território, preservando seleção e nomes acessíveis das cidades.

Acrescentados três registros institucionais `program: BRAFITEC`, `institutional_owner: UnB`, `status: documented`: ISAT/Nevers, Mines Nancy/Nancy e Arts et Métiers/ENSAM. Os 12 participantes são os identificados na proposta de 2023, com a função de coordenador francês de Antonio Rodriguez de Castro explicitada. Não se presume vigência atual nem coautoria. A autorização do titular abrange inclusão local dos vínculos já identificados; permanece vedada publicação remota sem aprovação.

ENSAM tem `location_pending: true`, coordenadas nulas e cidade interna `campus-pending`, traduzida na interface. Aparece no painel e no seletor como campus a confirmar, sem ponto no mapa. A validação rejeita localização pendente com cidade ou coordenadas inventadas. A proposta cita Bordeaux em um intercâmbio histórico, mas isso não confirma o campus de todos os participantes da equipe de 2023. La Réunion continua sem registro.

Fontes: proposta BRAFITEC 2023 consultada na pasta privada autorizada, sem cópia para o repositório; localização do ISAT confirmada em https://isat.fr/ecole/vie-associative/ e https://www.ube.fr/formation/ma-scolarite/ ; localização de Mines Nancy em https://mines-nancy.univ-lorraine.fr/wp-content/uploads/2022/01/Welcome-Booklet.pdf . Sem dados pessoais de contato, estudantes ou documentos financeiros.

Validação: 82 testes Python e build aprovados; auditoria Chrome nos quatro idiomas, teclado, toque, larguras 320–1920 px, ausência de números/conectores, participantes BRAFITEC e ENSAM sem ponto inventado. Capturas conferidas para Brasil e França. 30 registros no catálogo; prévia local somente.


## Campus ENSAM confirmado e legenda por aba — 16/11/2026

O titular confirmou Bordeaux como campus da colaboração Arts et Métiers/ENSAM. O registro `fr-brafitec-ensam` passou de localização pendente para Bordeaux (coordenadas aproximadas da cidade 44.84, -0.58), com ponto dourado no mapa francês. Pessoas e natureza institucional foram preservadas. A pendência descrita no histórico acima está resolvida para esse registro; a validação de localizações pendentes permanece disponível para casos futuros.

A legenda BRAFITEC aparece somente nas abas individuais Brasil e França. Permanece oculta no mapa mundial, inclusive quando Brasil ou França são selecionados nele. O atributo `hidden` é respeitado explicitamente pelo CSS, e a alternância de idioma mantém o estado. Não foram acrescentadas instituições ou participantes brasileiros nesta alteração. Testes Python (82), validação do build e auditoria de navegador cobrem Bordeaux e a visibilidade da legenda nas três abas e nos quatro idiomas. Sem publicação remota.


## Destaque BRAFITEC no Brasil — 16/11/2026

Por solicitação do titular, incluídos os vínculos institucionais brasileiros documentados na proposta BRAFITEC 2023: UnB/Brasília, UNIFEI/Itajubá e UFBA/Salvador. Coordenadas aproximadas das cidades; sem novos nomes pessoais ou alegação de vigência atual. Registros usam `scope: institutional`, `status: documented`, `program: BRAFITEC` e owner UnB, mantendo coautorias e demais vínculos separados. A UnB compartilha o cartão já existente e apresenta as duas naturezas de vínculo.

O renderizador brasileiro agora aplica o mesmo destaque dourado da França quando a cidade contém registro BRAFITEC. Legenda continua restrita às abas Brasil e França; sem números ou conectores. Catálogo contém 33 registros. Testes: 83 testes Python e validação do build aprovados; auditoria Chrome verifica os três pontos, sua cor efetiva, painel e idiomas. Prévia local somente, sem publicação.


## Zoom navegável do mapa mundial — 16/11/2026

Implementada primeira versão autorizada de zoom somente no mapa mundial: botões +/−, indicação percentual, restauração “Ver mundo inteiro”, barras de rolagem horizontal/vertical quando necessárias, arraste com mouse, caneta ou toque. A área com foco admite setas nativas para rolagem, +/− para zoom e Home para restaurar. Limites de 100% a 800%; visão inicial completa. Selecionar país na lista ou no mapa aproxima e centraliza sua geometria entre 200% e 600%, permitindo visualizar Taiwan. A escala é preservada ao alternar abas e idiomas; controles ocultos no Brasil/França.

Implementação em `site/site-data.js`, HTML/CSS e traduções nos quatro idiomas; sem dependências novas ou alteração de dados acadêmicos. Dimensões do SVG são recalculadas no redimensionamento. Arraste evita clique involuntário em outro país e não interfere na seleção por teclado. Em zoom ampliado, o toque move o mapa sem arrastar a página; na visão completa, a rolagem normal por toque permanece disponível. Testes de navegador cobrem enquadramento de Taiwan, barras nos dois eixos, arraste real por mouse, supressão de clique, limites, restauração, teclado e toque em tela pequena. 83 testes Python e validação do build aprovados; Brasil, França e filtros preservados. Prévia local somente.

A conferência móvel exigiu tratar o arraste por Pointer Events também para toque/caneta e a ativação dos controles por toque sem duplicar cliques. A área interna HTML dimensionada e a observação de seu tamanho garantem centralização após o SVG ser renderizado, inclusive quando o visitante escolhe o país no painel abaixo e retorna ao mapa. A câmera deixa de recentralizar ao iniciar arraste; restaurar limpa o alvo. A auditoria inclui Taiwan visível dentro do quadro móvel, deslocamento por gesto e restauração por toque.


## Diagramas das áreas de pesquisa — 16/11/2026

Substituídas, como experiência visual autorizada, as barras decorativas dos quatro cartões de Research Areas por diagramas SVG: biomassa/conversão/produtos, molécula H₂, malha com linhas de fluxo e ciclo de recursos/energia/emissões. São ilustrações conceituais, sem valores ou alegação de resultados quantitativos. Preservados títulos, descrições, tags, numeração e cores. SVGs inline em `site/index.html`, sem dependências ou imagens externas, ocultos para tecnologia assistiva por repetirem o tema já descrito no cartão. Estilo em `site/styles.css`, escala discreta no hover e respeito a movimento reduzido. Retiradas regras antigas de barras. Sem alteração nos catálogos acadêmicos ou nos mapas. 83 testes Python e build aprovados; auditoria de navegação com capturas desktop/mobile ampliada para conferir os quatro diagramas. Prévia local somente.


### Refinamento dos cartões — 16/11/2026

A pedido do titular, removidos os quatro glifos pequenos antigos do canto dos cartões e sua regra CSS. Mantidos os novos diagramas, numeração, textos e layout. Build validado e prévia local regenerada, sem publicação.


## Orientações com listas recolhíveis — 16/11/2026

Aprovada apresentação inicial de até quatro orientações concluídas e quatro em andamento. Cada grupo tem botão independente para ver todas e mostrar menos, traduzido em EN/PT/FR/ZH, com `aria-expanded` e `aria-controls`. Registros excedentes usam `hidden` (com CSS explícito) para não aparecer visualmente ou na navegação assistiva. As contagens e resultados continuam considerando todos os registros aprovados. Botão desaparece quando o filtro retorna até quatro itens; filtros recolhem ambos os grupos, e troca de idioma preserva a expansão. Ordenação anterior mantida; atividades complementares não foram alteradas. Dados acadêmicos preservados.

Implementação em `site/supervisions.js`, HTML/CSS e traduções. Auditoria Chrome ampliada para quatro iniciais, expansão/recolhimento por teclado, grupos independentes, idioma e filtros. 83 testes Python e validação do build aprovados. Prévia local somente.


## Selos por nível e situação das orientações — 16/11/2026

Experiência visual autorizada pelo titular: mestrado em verde-petróleo e doutorado em azul. Concluídas usam fundo suave preenchido; em andamento usam fundo branco e contorno. Texto completo de nível e situação permanece no selo, traduzido nos quatro idiomas, para identificação independente da cor. `site/supervisions.js` informa nível e situação no cartão por atributos de dados; CSS restrito aos cartões de pós-graduação, sem alterar selos editoriais ou atividades complementares. Contagens, filtros, expansão/recolhimento e catálogos acadêmicos preservados.

Auditoria Chrome ampliada para as quatro combinações nos quatro idiomas, verificando texto, cor, preenchimento e borda. 83 testes Python e build aprovados; prévia local regenerada, sem publicação.


## Graduação: IC e TCC — desenvolvimento e conferência de 16/11/2026

Implementado bloco independente `#undergraduate` dentro da seção de orientações, com listas separadas de iniciação científica e TCC, contagens de concluídos, filtros próprios por atividade/situação/ano e até quatro cartões iniciais por lista. Botões de expansão/recolhimento independentes; filtros de pós-graduação não interferem na graduação. Interface EN/PT/FR/ZH e navegação por teclado/toque. Títulos originais preservados; curso e papel não informados aparecem explicitamente como ausentes, sem inferência.

Reexecutado `scripts/import_supervisions.py` na exportação privada, com a revisão anterior como referência: 59 registros inalterados, dos quais 12 ICs concluídas, 18 TCCs concluídos e dois TCCs em andamento. Os 32 registros complementares não distinguem orientação/coorientação; três ICs de 2020 não informam curso. Dois estudantes distintos têm TCC com mesmo título em 2024; outro caso repete título em IC/2020 e TCC/2021. Não foram eliminados registros nem inferidos vínculos com publicações, projetos ou áreas. Não foram adicionados links de repositório não verificados.

Os 30 concluídos estão em relatório e catálogo candidato fora do repositório, aguardando aprovação explícita. `content/supervisions.json` permanece com as 27 orientações de pós-graduação aprovadas. A prévia editorial separada em 127.0.0.1:8002 serve exclusivamente um artefato de revisão com os candidatos concluídos marcados `approved: false`; não contém XML ou os dois trabalhos em andamento. O site principal em 127.0.0.1:8000 mantém somente o catálogo aprovado. O bundle de revisão não deve ser copiado para o artefato publicável. Após aprovação, incorporar somente os candidatos autorizados ao catálogo e gerar o build normal. A interface está preparada para orientações em andamento somente quando aprovadas e com resumos públicos traduzidos.

Validação: 85 testes Python, incluindo preservação de estudantes/níveis com títulos iguais e bloqueio de candidatos não aprovados no catálogo público. Auditoria Chrome ampliada para graduação, filtros independentes, contagens, quatro itens, expansão, dados ausentes, títulos originais, quatro idiomas e toque em tela pequena. Na auditoria foi corrigida a restauração do mapa mundial para ancorar a origem após recálculo assíncrono de layout, sem mudar a navegação aprovada. Nenhuma publicação remota.


### Incorporação da graduação à versão principal local — 16/11/2026

O titular reiterou que os registros deveriam estar incluídos no site principal, após receber a prévia e o relatório dos 30 concluídos. Incorporados os 12 registros de IC e 18 de TCC a `content/supervisions.json`, marcados como aprovados para inclusão local. Catálogo com 57 orientações: 27 de pós-graduação preservadas e 30 de graduação concluídas. Ausências de curso e papel continuam sinalizadas; os dois TCCs em andamento permanecem reservados fora do catálogo. A pendência de incorporação descrita acima está resolvida; a prévia editorial 8002 é histórica e o endereço de avaliação passa a ser 127.0.0.1:8000/#undergraduate. Build normal regenerado, com 85 testes Python e validação aprovados; sem publicação no GitHub.


### Terminologia da graduação — 16/11/2026

Corrigida a apresentação: Undergraduate Supervision / Orientações de Graduação nomeia a seção; Scientific Initiation (IC) / Iniciação Científica e Final-Year Project / Projeto Final de Graduação (TCC) são as duas categorias. Ajustados títulos, selos, filtros, indicadores e botões por meio das traduções compartilhadas, sem reclassificar registros (12 ICs e 18 projetos finais). FR/ZH mantêm a mesma hierarquia.

O titular definiu o rótulo inglês exato da categoria: **Final-Year Project (Undergraduate)**, compartilhado por título, selo e filtro.


### Papel nas orientações de graduação confirmado — 16/11/2026

O titular confirmou que atuou como orientador principal em todas as 30 orientações de graduação incluídas (12 ICs e 18 projetos finais). Atualizado `role: supervisor` nesses registros. Trata-se de confirmação editorial do titular, que prevalece sobre a ausência do campo no XML; preservar essa correção em futuras revisões do Lattes. Pós-graduação e dois TCCs em andamento reservados permanecem inalterados.


## Publicações com lista compacta — 16/11/2026

A pedido do titular, a lista de artigos mostra inicialmente até quatro resultados e oferece “Ver todas as publicações” / “Mostrar menos”, com total de correspondências no botão, nos quatro idiomas. Botão usa `aria-expanded` e `aria-controls`; resultados excedentes ficam `hidden` com CSS explícito. Contagem, busca, filtro de ano, categorias e links DOI preservados, sem alterações no catálogo. Busca e filtros recolhem a lista; troca de idioma mantém a expansão. Botão oculto quando existem até quatro correspondências.

Implementação em `site/site-data.js`, `site/index.html`, CSS e traduções. Auditoria Chrome cobre quatro iniciais, expansão/recolhimento por teclado nos quatro idiomas, busca DOI com um resultado, contagens e toque em tela pequena. 85 testes Python e validação do build aprovados; prévia principal local atualizada, sem publicação.


## Ordem de conteúdo — 16/11/2026

A pedido do titular, Projects passou imediatamente após Research Areas e antes de Graduate Supervision. Ordem principal: About → Research Areas → Projects → Graduate Supervision (incluindo graduação) → Publications → Institutional Ecosystem → Collaborations → Editorial → Contact. Link Projects reposicionado no menu após Research, preservando o grupo Academic Activities. Numeração visual de Projects/Publications ajustada para 03/04 nos quatro idiomas; âncoras, conteúdo e funcionalidades preservados. Prévia local, sem publicação.


## Protótipo de apresentação de projetos e temas — 16/11/2026

O titular aprovou experimentar um cartão antes de aplicar aos demais. O catálogo atual contém quatro temas/direções de pesquisa (`research_direction`), não quatro projetos formais com financiamento ou coordenação confirmados. Essa natureza foi preservada. Somente `research-01` (biomassa florestal e urbana) recebe protótipo com diagrama conceitual, três temas e abertura nativa de detalhes (questão científica e foco), mantendo título, descrição e link institucional existente. Não atribuídos papel, instituição parceira, período, financiamento, resultados ou vínculos bibliográficos novos.

Campo opcional `story` em `content/projects.json`: diagrama permitido, pergunta, foco e lista de tópicos traduzidos. Build valida estrutura e conteúdo; diagrama SVG local em `site/assets/project-biomass.svg`. Apresentação em `site/project-cards.js`; os outros três cartões permanecem com o formato anterior. `details/summary` oferece teclado e toque; abertura preservada ao trocar idioma. Diagrama decorativo, sem dados quantitativos, e movimento reduzido respeitado.

85 testes Python e build aprovados; auditoria Chrome ampliada para um único cartão experimental, quatro idiomas, abertura por teclado, preservação de estado e toque. Não houve publicação. Esta etapa valida apresentação; cadastro dos projetos formais e de metadados adicionais depende de fontes e confirmação do titular.


## Organização do repositório GitHub — 24/11/2026

O titular solicitou configurar e organizar o repositório antes de publicar. Conta EdUnB confirmada na sessão autenticada; criado repositório público vazio `EdUnB/edunb.github.io`, com descrição acadêmica, sem README automático, licença, arquivos-fonte ou commits remotos. Pages verificado como desativado por ausência de conteúdo; não foi ativado. A criação/configuração do repositório não constitui publicação do site.

Configurações remotas aplicadas pela interface: Wiki desativada (documentação em docs/); Issues e Projects mantidos; somente squash merge, sem merge commit/rebase; remoção automática de branches integradas, recuperáveis no GitHub; automerge permanece desativado. Actions permite ações locais e oficiais do GitHub, não ações genéricas de Marketplace; contribuidores externos exigem aprovação para executar workflows. Permissões padrão de leitura e criação/aprovação de PRs por Actions desativada, preservadas conforme observado. Sem colaboradores, tokens ou permissões amplas novos.

Git inicializado na pasta existente, branch local main sem commits e origin HTTPS associado ao repositório. `user.useConfigOnly=true` evita identidade de commit inferida; nome público configurado e e-mail de commit ainda não definido. Não se fez stage, commit, push ou merge nesta etapa de configuração inicial.

README atualizado e versão anterior preservada em docs/README_HISTORY_2026-11-24.md. Preparados CONTRIBUTING.md, CODEOWNERS do titular, modelos de PR/Issues, Dependabot mensal para GitHub Actions, .gitattributes com LF e exclusões locais adicionais no .gitignore. Nenhuma licença ampla foi escolhida, dadas as diferenças entre direitos de código, textos, imagem pessoal e logos.

Workflow local atualizado para checkout/setup-python v7 conforme documentação oficial consultada; usa Python 3.12 e ações Pages oficiais. Testes/build continuam em pushes e PRs de main. Upload do artefato Pages e job deploy dependem de `PAGES_DEPLOY_ENABLED == 'true'`, branch main e evento diferente de PR. Variável ausente/false impede publicação; ainda não foi criada no GitHub. Permissões elevadas limitadas ao job deploy. Primeira execução na infraestrutura GitHub permanece pendente.

Próximos passos sujeitos a revisão/aprovação: conferir seleção final e identidade de commit antes do primeiro envio público; validar CI remoto; então configurar proteção de main/checks e topics após a primeira branch existir. Ativar Pages, permitir deploy e publicar exigem nova autorização específica. Não foram alterados catálogos acadêmicos nem interface do site.

Validação final da preparação: 87 testes aprovados; `scripts/build.py --check` aprovado; cinco YAMLs analisados com parser local; simulação Git prevê 74 arquivos (~8,2 MB), sem stage, commit ou push. Inspeção não encontrou XML/ZIP/chaves privadas nos arquivos candidatos nem correspondências aos padrões de tokens GitHub verificados. Retrato sem segmento EXIF/GPS. O manifesto de arquivos/hashes permanece fora do repositório. Esses controles não substituem a aprovação editorial final antes da divulgação dos arquivos-fonte.


### Primeiro envio autorizado — 24/11/2026

O titular autorizou expressamente o envio dos 74 arquivos revisados ao repositório público, mantendo o site fora do ar. O seletor de arquivos do navegador não concluiu a transferência; confirmou-se que o remoto permanecia sem commits. O titular concluiu autenticação oficial do Git Credential Manager, e a conta EdUnB foi confirmada. Configurada identidade local de commit com endereço noreply derivado do identificador público da conta, sem expor e-mail pessoal. O envio usa Git para preservar integralmente as subpastas e não inclui dist/, XML/ZIP ou relatórios privados. A publicação Pages permanece bloqueada.


### Resultado do envio e hospedagem suspensa — 24/11/2026

Primeiro envio concluído no commit `ac86a57982981710be23d3c816517f3fb024c5da`, com 74 arquivos. A execução remota https://github.com/EdUnB/edunb.github.io/actions/runs/45446783226 concluiu validação/build com sucesso e ignorou o job deploy. As declarações anteriores sobre remoto vazio e CI pendente descrevem a fase de preparação.

O GitHub disparou também seu workflow nativo pages-build-deployment para main/(root), apesar de a configuração anterior do repositório vazio mostrar branch None. Esse fluxo publicou temporariamente a raiz antes de poder ser cancelado. Foi executado Unpublish site e a origem de Pages foi alterada para GitHub Actions; HTTP 404 confirmado após a retirada. A trava PAGES_DEPLOY_ENABLED protege somente o workflow próprio, não a publicação nativa por branch. Não há autorização para ativá-la. Antes de novos envios, manter a origem Actions e o deploy bloqueado. Não foram enviados XMLs ou arquivos privados. As propostas Dependabot permanecem sem merge.


### Publicação autorizada — 24/11/2026

O titular autorizou expressamente a publicação após confirmar que não há arquivos integrais de artigos hospedados. Ativada a variável PAGES_DEPLOY_ENABLED=true e iniciado workflow_dispatch em main: https://github.com/EdUnB/edunb.github.io/actions/runs/45449877328. Site acessível em https://edunb.github.io/ com HTTP 200, página acadêmica e alternância EN/PT/FR/ZH verificadas no navegador. Os 87 testes locais e build --check passaram novamente. O deploy serve exclusivamente dist/, não a raiz do repositório. As restrições anteriores de hospedagem suspensa são históricas; novas alterações com deploy continuam exigindo aprovação. O repositório-fonte permanece público, sem XMLs e sem cópias integrais dos artigos.
