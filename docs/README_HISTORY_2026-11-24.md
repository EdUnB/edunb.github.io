# Histórico do README anterior à organização no GitHub

Preservado em 24/11/2026. Este documento registra instruções anteriores, algumas superadas. Para executar comandos e publicar, siga o [README atual](../README.md). Em particular, o deploy agora depende de autorização e da variável `PAGES_DEPLOY_ENABLED`.

---

# Edgar A. Silveira — Academic Website

**Fonte oficial do site acadêmico multilíngue (EN/PT/FR/中文)** de Edgar Amaral Silveira. Repositório recomendado: **`EdUnB/edunb.github.io`**. O site foi preparado para GitHub Pages e não precisa de plano pago, backend, banco de dados, npm ou chave de API.

**Situação atual:** código e pipeline prontos para o repositório; **não está publicado** enquanto você não criar o repositório e configurar GitHub Pages. Conteúdo aprovado localmente: 50 publicações, 27 orientações de pós-graduação (13 concluídas e 14 em andamento), 4 vínculos documentados, 4 temas/projetos e 7 registros de atuação editorial e revisão. Dois artigos de 2027 permanecem em revisão. A aprovação dos registros para divulgação pública continua sob responsabilidade do pesquisador.

## Estrutura para manter permanentemente

```text
edgar-academic-website/
├── content/                  # OS ARQUIVOS QUE VOCÊ ATUALIZA
│   ├── profile.json          # perfil, e-mail, links, URL do site
│   ├── publications.json     # artigos (preenchidos via XML Lattes ou manualmente)
│   ├── projects.json         # projetos e linhas de pesquisa, EN/PT
│   ├── collaborations.json   # instituições e pesquisadores no mapa
│   └── translations.json     # textos gerais do site, EN/PT
├── site/                     # Design V2 aprovado + código de apresentação
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── site-data.js          # mapa interativo, publicações
│   ├── project-cards.js      # projetos a partir de JSON
│   └── assets/               # ícones, imagens autorizadas, documentos públicos
├── scripts/
│   ├── build.py              # valida conteúdo e monta o site final
│   └── import_lattes.py      # XML/ZIP privado -> metadados públicos
├── tests/                    # testes de integridade e privacidade
├── docs/                     # guias permanentes e regras editoriais
├── .github/workflows/pages.yml # GitHub Actions, testes e publicação
├── dist/                     # gerado automaticamente; NÃO editar
├── .gitignore
├── CHANGELOG.md
└── README.md
```

## Primeira publicação (GitHub Pages)

1. Tenha uma conta GitHub (sua captura mostra **EdUnB**). O repositório de usuário para esse endereço deverá se chamar **`edunb.github.io`** (minúsculas). Crie-o **público**.
2. Instale [GitHub Desktop](https://desktop.github.com/) em seu computador Windows. Faça login no GitHub Desktop; crie o repositório local na pasta fixa em **Documentos\\Projetos\\edgar-academic-website** (File → New repository; nome `edunb.github.io` se quiser usar o endereço raiz). Se já existir o repositório remoto, faça clone e copie o conteúdo do pacote nele. O nome da pasta local pode ser diferente do repositório, mas mantenha um diretório fixo.
3. Coloque o conteúdo **do pacote inteiro na raiz do repositório** (a raiz deve conter `README.md`, `content/`, `site/`, `.github/`). O arquivo `site/index.html` fica em `site/` — o GitHub Actions gera `dist/index.html` automaticamente. **Não use a instrução antiga de enviar somente `index.html` para a raiz.**
4. No GitHub Desktop, visualize as alterações e use `Commit to main` seguido de `Push origin` / `Publish repository` com a opção **public**.
5. No repositório GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions** (não `Deploy from a branch`). A workflow `.github/workflows/pages.yml` faz os testes, gera `dist/` e publica.
6. Acesse **https://edunb.github.io/** após o status verde em **Actions**. O nome do endereço depende da conta e disponibilidade do repositório.

> **Atenção:** o site estático pronto fica em `dist/`. Essa pasta é gerada e ignorada pelo Git; NÃO a adicione ao repositório. O GitHub Actions faz isso no servidor.

## Testar localmente (Windows, Python instalado)

```powershell
python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Abra http://127.0.0.1:8000 no navegador. Para parar o servidor, pressione Ctrl+C.

## Atualizações simples

- **Artigos:** envie XML/ZIP do Lattes **somente neste projeto privado do ChatGPT ou execute localmente** `python scripts/import_lattes.py "C:\\...\\Curriculo.zip" --dry-run`; depois execute sem `--dry-run` para atualizar `content/publications.json`. O importador preserva categorias corrigidas e itens manuais. Faça revisão e teste antes do commit.
- **Novos parceiros:** atualize `content/collaborations.json`. Um registro com `public: true` só deve ser incluído depois de confirmar os dados e autorizar publicação. O mapa mundial e o do Brasil leem a mesma lista.
- **Projetos:** atualize `content/projects.json` (campos `en` e `pt`).
- **Textos:** atualize `content/translations.json` (EN e PT com as mesmas chaves).
- **Perfil:** atualize `content/profile.json`. O `site_url` deve ter o endereço do GitHub Pages realmente publicado.

Depois de editar: `python scripts/build.py --check`, revise alterações no GitHub Desktop, faça commit, clique **Push origin**. O GitHub Actions validará e republicará, sem precisar de upload manual de arquivos HTML.

## Segurança e direitos autorais

- **Nunca envie o XML/ZIP original do Lattes para o repositório público.** Guarde-o em uma pasta privada fora do repositório. A `.gitignore` bloqueia extensões comuns, e o teste de CI identifica exportações acidentalmente colocadas nas pastas públicas.
- **Só publique contatos institucionais e nomes de colaboradores após confirmação e autorização apropriadas.** Projetos em prospecção não são parcerias firmadas.
- **PDFs de artigos:** forneça links DOI e, para download, somente versões permitidas pelas políticas dos periódicos ou repositórios institucionais.
- **Deploy automático:** alterações enviadas ao ramo `main` aparecem publicamente depois dos testes. Use commits claros e revise previamente.

Veja `docs/GUIA_WINDOWS.md`, `docs/FLUXO_ATUALIZACAO.md` e `docs/INSTRUCOES_PROJETO_CHATGPT.md`.

## Revisão de navegação V2.7

O grupo “Academic Activities / Atuação Acadêmica” reúne Orientações e Atuação Editorial. A busca bibliográfica combina texto, categoria e ano. Os filtros e seleções são preservados ao trocar EN/PT. O filtro de área das orientações fica desativado enquanto não houver áreas atribuídas aos registros aprovados.

Após gerar o build e iniciar o servidor local, execute o teste de navegador com Node.js e Chrome instalados.

```powershell
node tests/browser_navigation.cjs http://127.0.0.1:8000/
```

Para testar no Edge, defina `BROWSER_EXE` como caminho do executável. Para guardar capturas, defina `AUDIT_SCREENSHOTS` como diretório existente fora do repositório. O teste usa um perfil temporário e verifica EN/PT, teclado, toque, filtros, mapas, integridade das âncoras e larguras de 320 a 1920 pixels.

## CV acadêmico resumido

A arquitetura de atualização conjunta com os catálogos revisados está descrita em [docs/SHORT_CV.md](docs/SHORT_CV.md). O CV permanece em revisão editorial e não aparece no site enquanto não for aprovado. A prévia é gerada fora do repositório com `python -B scripts/preview_cv.py --output "PASTA_EXTERNA/cv-review"`.

## Atualização coordenada das fontes

Consulte [docs/UPDATE_WORKFLOW.md](docs/UPDATE_WORKFLOW.md). A entrada `python -B scripts/update_sources.py --review-dir "PASTA_PRIVADA/revisoes"` prepara a revisão sem modificar catálogos. O conector Scopus automático aguarda configuração e validação do acesso API institucional.
