# Indicadores Scopus e séries anuais

## Identidade e observação confirmada

Perfil fornecido pelo titular: https://www.scopus.com/authid/detail.uri?authorId=57195100508. A visualização Preview mostrou Silveira, Edgar A., Universidade de Brasília, e ORCID 0000-0002-7582-5010, coincidindo com a identidade do site.

A consulta de 15/11/2026 exibiu 87 documentos, 1.243 citações, 572 documentos citantes e índice H 22. Em 16/11/2026, a tentativa de atualização redirecionou para autenticação Elsevier. Os valores mantêm a data da observação anterior e não são apresentados como leitura ao vivo. O titular confirmou possuir acesso institucional pela UnB.

## Implementação

- `content/scopus.json`: snapshot público agregado e datado, separado de `content/publications.json`. Documentos indexados no Scopus e artigos do catálogo Lattes têm coberturas diferentes.
- `scripts/build.py`: valida identidade, URL, fonte, data, campos permitidos, contagens e estrutura das séries; gera `dist/data/scopus.js`. Credenciais e campos inesperados não são aceitos.
- `site/scopus-metrics.js`: indicadores, consulta datada, link ao perfil e renderização EN/PT/FR/ZH. Não faz chamadas externas ou autenticação no navegador do visitante.
- O componente possui dois gráficos anuais de barras, com legendas e tabelas acessíveis: documentos por ano de publicação e citações recebidas por ano. Hoje `annual_series` é `null`, e nenhum gráfico anual é exibido. Ausência de dados não vira zero.
- As métricas Scopus não alteram o catálogo Lattes nem os indicadores do CV resumido nesta etapa.

## Preferência operacional atual

Em 16/11/2026 o titular definiu que exportação manual não deve ser o fluxo regular. O conector API e a entrada única de coleta foram preparados em `scripts/scopus_client.py` e `scripts/update_sources.py`; a validação real aguarda credenciais. Consulte [UPDATE_WORKFLOW.md](UPDATE_WORKFLOW.md). A orientação anterior de exportação abaixo fica registrada como alternativa pontual, sem obrigação de rotina.

## Alternativa de diagnóstico por exportação

Com acesso institucional, obter do perfil a análise de produção e a visão geral de citações, com séries anuais. A disponibilidade e os nomes dos controles de exportação podem variar. Guardar as exportações originais fora do repositório público e informar o caminho para revisão local. Confirmar intervalo de anos, cobertura de documentos e inclusão/exclusão de autocitações antes de comparar os totais.

Após conferir o arquivo real, normalizar para:

```json
{
  "documents": [{"year": 2020, "value": 2}],
  "citations": [{"year": 2020, "value": 3}]
}
```

Os números do exemplo são sintéticos e não correspondem ao pesquisador. Não foram incorporados ao catálogo. A série real deve vir de exportação revisada ou acesso API autorizado, sem estimar distribuição anual a partir dos totais. Anos fora de um intervalo exportado não são implicitamente anos com zero ocorrências.

## Atualização automática

A configuração de acesso real ainda está pendente. O conector automático já foi implementado e testado com respostas sintéticas. Visualizar o perfil não concede acesso à API nem garante permissão para republicar séries obtidas por ela. A elegibilidade institucional, os endpoints e a modalidade de exibição devem ser conferidos segundo as regras vigentes da Elsevier antes de automatizar. Uma chave isolada não garante acesso; pode haver autenticação por rede institucional ou token institucional. Não inserir segredos em HTML, JavaScript ou JSON público.

Documentação oficial consultada:

- https://dev.elsevier.com/support.html
- https://dev.elsevier.com/policy.html
- https://dev.elsevier.com/sc_api_spec.html

O caminho inicial é uma atualização por snapshot/exportação revisada, seguida do build. A data de consulta permanece visível. Nenhum agendamento, autenticação automatizada ou publicação foi realizado.

## Validação

Seis testes específicos verificam identidade, campos indevidos, contagens, datas, consistência básica e séries ausentes/duplicadas. A auditoria de navegador verifica os indicadores e traduções, ausência de gráficos sem dados e renderização dos dois gráficos/tabelas com dados sintéticos isolados na página de teste, removidos antes das demais verificações. Os demais mapas, filtros, CV e rede continuam cobertos pela auditoria.
