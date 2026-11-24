# Contribuir e manter o site

Leia `AGENTS.md` e `docs/PROJECT_CONTEXT.md` antes de alterar o projeto. Preserve a identidade visual e use `content/` para dados editoriais, `site/` para apresentação. Não editar `dist/`.

## Fluxo de revisão

1. Criar uma branch de trabalho a partir de `main`.
2. Manter o escopo claro: conteúdo, tradução, interface ou manutenção técnica.
3. Para novos dados acadêmicos, registrar a fonte e obter aprovação editorial antes de incluí-los no catálogo. Não enviar XMLs, propostas privadas ou credenciais.
4. Executar `python -B -m unittest discover -s tests -v` e `python -B scripts/build.py --check`. Alterações de interface exigem build e auditoria de navegador nos quatro idiomas, teclado e celular.
5. Abrir pull request com problema, mudança, validação e eventuais pendências. A revisão deve distinguir coautoria, parceria institucional, formação histórica e negociação.
6. Integrar somente após validação e aprovação do titular. Preferir squash merge para um histórico conciso; branches de PR integradas podem ser removidas automaticamente pelo GitHub.

Atualizações do Lattes usam primeiro simulação/revisão privada. Não inferir orientação/coorientação, DOIs, anos ou vínculos; preservar correções editoriais. Títulos acadêmicos permanecem no idioma original.

## Privacidade e publicação

Issues e pull requests deste repositório são públicos. Não incluir dados de estudantes não aprovados, títulos provisórios, manuscritos, senhas, tokens, documentos pessoais ou exportações do Lattes. O e-mail institucional público do titular está na seção de contato do site.

Push e publicação são decisões diferentes. `PAGES_DEPLOY_ENABLED` ausente/false bloqueia o deploy; sua ativação e qualquer envio que dispare publicação exigem autorização. Consulte o README atual.
