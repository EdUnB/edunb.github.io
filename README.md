# Edgar A. Silveira — Academic Website

Site acadêmico pessoal de Edgar Amaral Silveira, professor da Universidade de Brasília (UnB), com conteúdo em **inglês, português, francês e chinês simplificado**. Inglês é o idioma inicial.

## Estado atual

Repositório oficial: [EdUnB/edunb.github.io](https://github.com/EdUnB/edunb.github.io).

**O site ainda não está publicado.** O repositório oficial foi criado e o primeiro envio dos arquivos foi autorizado pelo titular em 24/11/2026, mantendo a publicação bloqueada. O endereço planejado é `https://edunb.github.io/`. Consulte Actions e o CHANGELOG para o resultado da validação remota; a entrada no ar depende de autorização específica.

Conteúdo local: 50 artigos; 27 orientações de pós-graduação (13 concluídas, 14 em andamento); 30 de graduação concluídas (12 iniciações científicas e 18 projetos finais); 33 registros de vínculos acadêmicos, institucionais e coautorias documentadas; quatro temas de pesquisa; sete registros editoriais/de revisão. Não confundir temas de pesquisa com projetos formais ou coautorias com parcerias ativas. Os trabalhos de graduação em andamento permanecem reservados fora do repositório.

## Organização

| Pasta/arquivo | Responsabilidade |
|---|---|
| `content/` | Catálogos acadêmicos aprovados e traduções EN/PT/FR/ZH |
| `site/` | HTML, CSS, JavaScript e imagens autorizadas |
| `scripts/` | Build, revisão de fontes e importadores locais |
| `tests/` | Validação de dados, privacidade e navegação |
| `docs/` | Contexto, decisões, guias e histórico técnico |
| `.github/` | Validação/deploy, responsáveis e modelos de contribuição |
| `dist/` | Artefato gerado; nunca editar nem versionar |
| `AGENTS.md` | Instruções permanentes do projeto |
| `CHANGELOG.md` | Histórico das modificações |

XML/ZIP Lattes, relatórios de revisão, credenciais e documentos privados ficam **fora desta pasta e do repositório público**. `public: false` não torna um arquivo-fonte privado.

## Construção e prévia local

Python 3.12 ou superior, sem dependências Python externas para testes/build. Node.js e Chrome/Edge são necessários somente para a auditoria de navegador.

```powershell
python -B -m unittest discover -s tests -v
python -B scripts/build.py --check
python -B scripts/build.py
python -B -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Abra `http://127.0.0.1:8000/`. Se o servidor estiver usando `dist/` e impedir a limpeza da pasta, encerre-o antes de reconstruir; reinicie-o em seguida.

```powershell
node tests/browser_navigation.cjs http://127.0.0.1:8000/
```

A auditoria verifica quatro idiomas, teclado/toque, filtros, listas recolhíveis, mapas e larguras de 320 a 1920 px. Defina `AUDIT_SCREENSHOTS` com uma pasta externa existente para guardar capturas. Validação local da preparação em 24/11/2026: 87 testes Python aprovados; consulte o registro mais recente no CHANGELOG.

## Atualizar o conteúdo

Siga [o fluxo coordenado](docs/UPDATE_WORKFLOW.md). Revisões do Lattes começam em simulação e permanecem fora do repositório. Preserve correções editoriais confirmadas pelo titular. Incorporar dados ao site não autoriza publicá-los na internet.

- [Contexto e decisões](docs/PROJECT_CONTEXT.md)
- [Contribuições e revisão](CONTRIBUTING.md)
- [CV resumido](docs/SHORT_CV.md)
- [Scopus: fonte, data e limites](docs/SCOPUS_METRICS.md)
- [Histórico de versões](CHANGELOG.md)

## Publicação controlada

O workflow `.github/workflows/pages.yml` valida testes e build em pushes/PRs para `main`. **Não publica por padrão.** O upload do artefato Pages e o deploy exigem a variável de repositório `PAGES_DEPLOY_ENABLED` exatamente igual a `true`, execução em `main` e evento diferente de pull request. Variável ausente ou `false` mantém o deploy bloqueado.

Depois da autorização para entrar no ar, configure Pages com fonte **GitHub Actions**, autorize a variável e execute o workflow em `main`. Só depois confirme o endereço público e HTTPS. Enviar o código a um repositório público já divulga os arquivos-fonte, mesmo com Pages desativado; esse envio também exige revisão e aprovação.

Antes do primeiro envio, conferir a seleção de arquivos, metadados aprovados, imagens/logos e ausência de dados privados. Proteção de `main` e verificações obrigatórias devem ser concluídas após a primeira branch/check existir. Não criar tokens de acesso permanentes nem adicionar colaboradores sem necessidade e autorização.

## Direitos sobre os materiais

Nenhuma licença ampla foi escolhida nesta etapa. Código, textos, fotos, logos e artigos podem ter direitos distintos. A criação do repositório público não concede automaticamente licença para reutilização desses materiais. Definir a licença com o titular antes de anunciá-la; distribuir somente PDFs autorizados.

As instruções anteriores foram preservadas no [histórico do README](docs/README_HISTORY_2026-11-24.md).
