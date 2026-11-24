# Guia de instalação e atualização no Windows

## Pastas permanentes sugeridas

```text
Documentos/
└── Projetos/
    ├── edgar-academic-website/       <-- repositório público (este pacote)
    └── _edgar-website-privado/       <-- FORA do repositório, só no seu PC
        ├── lattes-xml/
        ├── fotos-originais/
        └── contatos-em-avaliacao/
```

Mantenha essa pasta em local com backup. Se sincronizar `Documentos` em nuvem, confira permissões dos diretórios privados. Preferencialmente use GitHub Desktop para preservar histórico e poder reverter erros.

## Como criar o repositório a partir dos arquivos do pacote

1. No GitHub web crie repositório público `edunb.github.io` na conta `EdUnB` se ele ainda não existir. Não marque `Initialize with README`, pois já fornecemos um.
2. No GitHub Desktop, escolha `File → Clone repository...`, escolha o repositório remoto e uma pasta fixa local. Se o repositório está vazio e o Desktop não conseguir clonar, use `File → New repository` com o mesmo nome e a opção `Publish repository` após copiar o pacote.
3. Copie todas as pastas e arquivos deste pacote **para dentro do repositório local**. Use a opção de mostrar arquivos ocultos do Windows para não perder `.github/` e `.gitignore`. Não copie a pasta privada, nem quaisquer XML/ZIP do Lattes.
4. No GitHub Desktop, confirme que apareceram `content/`, `site/`, `scripts/`, `tests/`, `docs/` e `.github/`. Não deve aparecer `dist/` nem exportações privadas.
5. `Commit to main` → `Push origin`.
6. No repositório, `Settings → Pages → Build and deployment → Source: GitHub Actions`.
7. Vá em `Actions`. Espere os jobs `Validate content and build` e `Publish to GitHub Pages` ficarem verdes; depois abra `https://edunb.github.io`.

Se preferir trabalhar sempre no GitHub Desktop, não precisa instalar ferramentas de programação para publicações simples. Para importar XML localmente, instale Python 3. O ChatGPT pode produzir os JSONs atualizados a partir do Lattes anexado, para você fazer commit.

## Conferência antes do lançamento público

- Testar Inglês e Português em computador e celular.
- Testar clique em país no mapa do mundo e marcadores no Brasil.
- Confirmar e-mail, links Lattes e ORCID.
- Confirmar nomes de professores e vínculo **histórico / institucional / individual**.
- Verificar todos os DOIs, autorização de PDFs e origens das fotos/logotipos.
- Validar resultado com `python -m unittest discover -s tests -v` quando tiver Python.
