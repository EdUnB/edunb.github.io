# Revisão de navegação V2.7

**15 de novembro de 2026**

## Melhorias implementadas

- O grupo “Academic Activities / Atuação Acadêmica” reúne Orientações e Atuação Editorial. O menu usa um controle HTML nativo, com suporte a teclado, toque, Escape, fechamento ao clicar fora e foco na seção escolhida.
- O cabeçalho adota navegação móvel até 1100 pixels para acomodar os rótulos nos dois idiomas. Os controles têm altura mínima de 44 pixels.
- A lista bibliográfica permite buscar título, autor, periódico ou DOI, ignorando diferenças de acentos e caixa. A busca combina ano e categoria. Há contagem dos resultados, mensagem para buscas vazias e botão para limpar os filtros.
- O filtro por área das orientações fica desativado enquanto não houver associações cadastradas nos registros. A interface explica o comportamento. O filtro de ano é identificado como ano de conclusão.
- O diagrama inicial, a localização e as etiquetas de pesquisa receberam traduções. Os textos da bibliografia agora descrevem o catálogo ampliado, sem instruções internas de importação.
- Textos auxiliares de autores, datas, notas, cartões e mapas receberam ajustes de contraste dentro da paleta existente. O foco dos países usa o contorno SVG, evitando um retângulo que cruzava o mapa quando o país tinha territórios separados.

## Verificações

| Área | Resultado |
| --- | --- |
| Testes Python | 37 testes passaram, incluindo importação segura, revisão incremental, privacidade, catálogos e correspondência institucional. |
| Build | Gerado e validado com 50 artigos, 27 orientações, quatro projetos, quatro vínculos e sete registros editoriais e de revisão. |
| Navegadores | Chrome e Microsoft Edge em modo headless. |
| Idiomas | Percursos completos em inglês e português, preservando filtros e seleções. |
| Teclado | Grupo do menu, Escape e foco após navegação, seleção de países e marcador do Brasil. |
| Toque | Menu móvel e acesso a Orientações pelo grupo de atividades acadêmicas. |
| Telas | 1920, 1440, 1280, 1101, 1100, 1024, 768, 390, 360 e 320 pixels, em EN/PT, sem transbordamento horizontal. |
| Publicações | Busca por texto e DOI, digitação, combinação com ano e categoria, estado vazio e limpeza dos filtros. |
| Orientações | Indicadores de 13 concluídas e 14 em andamento, filtros de nível, situação e ano, 12 links institucionais e rótulo de tese. |
| Cooperações | Seleção de França, Nancy, Brasil e Brasília, cartões e pesquisadores associados. |
| Estrutura | Uma ocorrência de H1, IDs únicos, âncoras válidas, referências ARIA existentes e controles com nomes acessíveis. |
| Contraste | Os textos auxiliares amostrados atingiram pelo menos 4,5:1 após a correção. |
| Prévia HTTP | Recursos locais carregaram sem erros. Código-fonte, arquivos privados e configuração Git responderam 404 nas rotas testadas. |
| JavaScript | Nenhuma exceção observada nos percursos automatizados. |

Os testes de navegação estão em `tests/browser_navigation.cjs`, com instruções no README. Foram inspecionadas capturas da página inicial, mapas, orientações, publicações e seção editorial.

## Links externos

Foram consultados 78 endereços públicos. Os 49 DOIs retornaram redirecionamento válido, e 19 páginas responderam HTTP 200, incluindo os 12 registros da UnB. CIRAD e Université de Lorraine também puderam ser consultados pelo navegador de pesquisa, após falharem no verificador HTTP.

Cinco endereços de editoras retornaram HTTP 403 no verificador automatizado (MDPI e quatro páginas da ScienceDirect). As duas páginas do LEA e o Lattes ficaram sem confirmação por falha de acesso ou tempo de resposta. Esses resultados exigem conferência manual e não demonstram remoção das páginas. Os endereços institucionais foram mantidos.

## Limites e pendências

- A revisão foi feita com emulação móvel. Aparelho físico e leitor de tela ainda precisam de avaliação.
- A medição de contraste cobriu os textos auxiliares definidos no teste. Esta auditoria não certifica conformidade integral com WCAG.
- Dois artigos de 2027, o link da UFLA e as atividades complementares de graduação continuam nas respectivas etapas de revisão.
- O filtro de área das orientações depende de associações aprovadas. A busca bibliográfica usa as categorias editoriais existentes.
- A prévia está disponível apenas localmente. A configuração de Git e o lançamento no GitHub Pages permanecem para etapa posterior.
