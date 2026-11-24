# Fluxo de atualização e governança de conteúdo

## Versão aprovada e publicação

A identidade visual e a organização **V2** são o baseline. Essa entrega reorganiza o projeto internamente, sem alterar o conceito visual. Mudanças em layout, conteúdo sensível ou identidade são revisadas antes de entrar no ramo `main`.

1. **Receber dados:** XML/ZIP do Lattes (privado), novos artigos, novos projetos, contatos institucionais confirmados ou fotografias autorizadas.
2. **Importar / preparar alterações:** `scripts/import_lattes.py` ou edição dos arquivos em `content/`. Não copiar o XML bruto.
3. **Revisar diferenças:** novos DOIs, títulos, autores, categorias, atribuição correta de parcerias e duplicados.
4. **Verificar:** `python -m unittest discover -s tests -v` e `python scripts/build.py`.
5. **Aprovar:** a pessoa titular do site confirma alterações em conteúdo e parceiros.
6. **Versionar e publicar:** commit Git claro, push. GitHub Actions valida e publica automaticamente se o push for ao ramo `main`.

### O que o Lattes atualiza automaticamente

Somente **artigos publicados e seus metadados públicos**: ano, título, periódico, autores, DOI e classificação temática sugerida. O script tenta preservar classificações manuais anteriores. O arquivo não cria links para PDFs editoriais.

### O que é editorialmente revisado

Histórico profissional, fotos, financiamentos, projetos, disciplinas, colaborações, pessoas e status de parcerias. Não inferir cooperação ativa somente por coautoria ou formação acadêmica. Atenção especial a relações institucionais do LEA, distintas de vínculos individuais.

### Segurança

A exportação XML do Lattes pode trazer dados cadastrais não destinados a publicação. Não armazene raw XML no GitHub público nem em pastas do site. Verifique o conteúdo antes de compartilhar em ambientes de colaboração. A publicação via GitHub Actions é automática após push, por isso a revisão deve ocorrer antes do commit no `main`.
