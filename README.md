# Samsara

Leitor e editor de aventuras no formato Samsara 1.0.

## Estrutura

- `index.html` — marcação da interface.
- `assets/css/styles.css` — estilos.
- `assets/img/` — imagens internas antes embutidas como Base64.
- `src/js/*.part.js` — fonte JavaScript dividida por domínio, concatenada em um único runtime para preservar o comportamento do monólito original.
- `scripts/build.mjs` — gera `dist/assets/js/app.js`.
- `.github/workflows/pages.yml` — valida e publica o diretório `dist` no GitHub Pages.

## Desenvolvimento

```bash
npm run check
```

O bundle em `dist/` é gerado e não deve ser editado diretamente.
