# Atualização assistida e coordenada do site

## Preferência permanente do titular — 16/11/2026

Ao receber o pedido “atualize o site”, o agente deve coletar as informações nas fontes configuradas, preparar diferenças para revisão, aplicar somente mudanças autorizadas e gerar site e CV juntos. Exportar CSVs manualmente do Scopus não é o fluxo de rotina desejado. Não exigir redigitação dos mesmos dados em diferentes seções.

O ciclo distingue coleta, revisão editorial, gravação dos catálogos, build local e publicação. Pedir uma atualização não autoriza publicação no GitHub. Novas orientações em andamento, vínculos e escolhas bibliográficas continuam sujeitos aos critérios editoriais já definidos.

## Entrada única para coleta

```powershell
python -B scripts/update_sources.py --review-dir "PASTA_PRIVADA_FORA_DO_REPOSITORIO/revisoes"
```

O comando valida o estado atual, tenta as fontes configuradas e grava um relatório JSON privado. Ele nunca modifica os catálogos oficiais, credenciais, XMLs, configurações de deploy ou site publicado. O agente examina a proposta e incorpora as alterações autorizadas antes do build. `--offline` impede chamadas externas e registra explicitamente que o Scopus não foi consultado.

## Fontes e responsabilidades

| Fonte | Coleta e atualização |
| --- | --- |
| Lattes | Detectar exportação mais recente por `DATA-ATUALIZACAO` na pasta privada irmã `_edgar-website-privado`, ou usar `LATTES_XML_PATH`/`--lattes`. XML/ZIP passa pelo leitor seguro já existente. Preparar propostas de artigos, orientações e funções editoriais. |
| Revisão privada de orientações | Reutilizar `LATTES_SUPERVISIONS_REVIEW`, ou a revisão `orientacoes-revisao*.json` mais recente junto ao XML, preservando correções e identificando alterações. |
| Scopus | `scripts/scopus_client.py`: Author Retrieval METRICS, busca paginada de documentos do autor e Citation Overview para obter as séries anuais. Sem CSV como dependência de rotina. |
| Perfil e formação | Preservar texto aprovado e comparar evidências em atualização editorial. Não substituir automaticamente a biografia por texto bruto do Lattes. |
| Projetos e cooperações | Consultar fontes institucionais e preservar escopo, status e aprovação. Coautoria não cria parceria automaticamente. |
| Idiomas | Manter paridade EN/PT/FR/ZH após alterações aprovadas, preservando títulos originais. |
| CV resumido | Recalculado pelo mesmo build a partir dos catálogos revisados, com seleção bibliográfica mantida. |
| Interface e links | Executar testes, build e auditoria de navegador; revisar links alterados e fontes citadas. |

O agente localiza os arquivos e executa os comandos. O titular não precisa preencher esses relatórios. Um novo XML precisa estar disponível na fonte privada: a obtenção automática de uma nova exportação no portal Lattes não foi implementada ou prometida.

## Acesso Scopus: configuração inicial ainda pendente

O ambiente foi verificado sem imprimir valores de credenciais. Não há `SCOPUS_API_KEY`, `ELSEVIER_API_KEY` ou `SCOPUS_INST_TOKEN` configurados. A sessão web do perfil passou a exigir login. O acesso institucional confirmado pelo titular não equivale, por si só, ao acesso autorizado à API.

Configurar a chave e, se exigido pela Elsevier, o token/rede institucional em ambiente privado. Nunca colocar credenciais no chat, em arquivos versionados ou no JavaScript público. Chaves podem expirar ou precisar de renovação. A concessão de acesso e o uso público das métricas devem corresponder à modalidade autorizada pela Elsevier; não automatizar contorno de autenticação ou CAPTCHA.

O conector foi implementado com base nos endpoints e exemplos oficiais, mas **ainda não foi validado com uma credencial real**. Os testes usam respostas sintéticas. A coleta efetiva pode revelar restrições de permissão, escopo temporal ou formato que exijam ajuste.

- https://dev.elsevier.com/documentation/AuthorRetrievalAPI.wadl
- https://dev.elsevier.com/documentation/AbstractCitationAPI.wadl
- https://dev.elsevier.com/support.html
- https://dev.elsevier.com/policy.html

## Garantias da coleta

- Segredos são enviados somente em cabeçalhos para `api.elsevier.com`; redirecionamentos são recusados.
- Há limite de tamanho de resposta e tempo de conexão. Mensagens de erro não reproduzem credenciais, URLs autenticadas ou corpos de resposta.
- O autor retornado deve coincidir com 57195100508. Busca paginada deve corresponder à contagem do perfil, sem documentos duplicados.
- Cada lote de citações deve conter exatamente os documentos e os anos esperados. A soma anual deve concordar com o total do perfil. Dados incompletos não geram atualização parcial silenciosa.
- Anos sem documentos podem receber zero somente após coleta completa comprovada. Colunas ausentes na resposta de citações não são interpretadas como zero.
- Datas futuras de publicação, citações anteriores ao intervalo ou divergências de totais exigem revisão. Não corrigir automaticamente anos bibliográficos.
- Falha de acesso conserva o snapshot anterior e sua data; um erro não zera métricas nem troca a data por uma consulta que não ocorreu.

## Estado atual

Em 16/11/2026, a execução real encontrou e processou a fonte privada do Lattes, preparando as três seções para revisão sem alterar o catálogo. O Scopus foi registrado como `initial_setup_required`, pois não há chave disponível. Os indicadores do site continuam com a consulta anteriormente confirmada, e os gráficos continuam aguardando séries verificadas. Não houve publicação.

Depois de configurar e validar o acesso, o ciclo esperado é: pedido do titular → coleta automatizada → revisão das diferenças → atualização autorizada → testes/build → site e CV sincronizados. A publicação continua sendo uma etapa separada, com aprovação explícita.
