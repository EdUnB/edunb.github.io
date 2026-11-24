# Decisões técnicas permanentes

## 1. Arquitetura

- Site estático: HTML sem frameworks, CSS responsivo, JS com DOM seguro e SVG acessível nos mapas. Não há banco de dados, API paga, dependências npm, chaves secretas ou serviço servidor.
- Conteúdo público em arquivos JSON editáveis, com validador no build Python.
- `site/` contém o design, e `dist/` é artefato compilado. A apresentação pública é sempre gerada com `scripts/build.py`.
- Lattes XML/ZIP original não é versionado: o importador é executado localmente ou o arquivo privado é enviado a um espaço de trabalho autorizado para revisão. Apenas metadados bibliográficos entram em `content/publications.json`.
- GitHub Desktop é recomendação operacional no Windows. GitHub Actions publica o artefato, sem inserir `dist/` no Git.

## 2. Idiomas

- `en` é padrão; `pt` é alternativo. As traduções principais vivem em `content/translations.json`.
- Projetos usam campos bilíngues. Colaborações têm `institution_en`, `relation_en` e `relation_pt`.
- Títulos de artigos permanecem conforme publicados na revista.

## 3. Governança

- A apresentação V2 é baseline até revisão aprovada.
- Os vínculos são atribuídos a escopo (`research`, `academic`, `institutional`) e status (`documented`, `historical`), sem inferir que todos são ativos.
- Somente registros `public:true` são enviados ao navegador. **Atenção:** o JSON-fonte dentro do repositório é público mesmo para registros `public:false`; não registre dados sigilosos nem pessoais não autorizados nesse arquivo, mesmo quando marcados `false`.
- Nenhuma atualização é publicada sem `push` ao `main`. Para mudanças sensíveis, criar branch e pull request, revisar e aprovar merge.

## 4. Evolução

- Adicionar mais países: país ISO-3 em `collaborations.json`, verificação de coordenadas; o mapa do mundo já contém contornos SVG. Incluir nomes traduzidos no mapa ao ampliar a rede.
- Adicionar fotos e logotipos somente após autorização de uso e com qualidade adequada. Colocar arquivos otimizados em `site/assets/`, evitando logos reconstruídos ou extraídos de fontes não oficiais.
- Conteúdo de artigos não deve ser publicado no repositório antes de verificar direitos de distribuição; prefira DOI, repositório institucional ou versão permitida.
