# 🇧🇷 Lista M3U Brasil otimizada para SS IPTV

Lista de canais brasileiros gerada automaticamente a partir de [iptvcat.com/brazil__10](https://iptvcat.com/brazil__10/).

## Características

- ✅ Atualização automática a cada **6 horas** (GitHub Actions)
- ✅ **Não apaga** canais que ainda funcionam
- ✅ Só remove um canal se ele **falhar em 3 atualizações consecutivas**
- ✅ Canais separados por categorias (`group-title`)
- ✅ Formato otimizado para **SS IPTV**
- ✅ Mantém `tvg-logo` quando disponível

## Link direto da lista (após publicar no GitHub)

```
https://raw.githubusercontent.com/SEU-USUARIO/SEU-REPO/main/brazil_ssiptv.m3u
```

## Como usar no SS IPTV

1. Abra o **SS IPTV**
2. Vá em **Playlist** → **Adicionar playlist**
3. Cole o link acima **ou** selecione o arquivo `brazil_ssiptv.m3u`

## Categorias

| Categoria          | Exemplos                          |
|--------------------|-----------------------------------|
| Notícias           | Record News, Bandnews             |
| Esportes           | FIFA+ Portuguese                  |
| Infantil           | Gloob, Nickelodeon, Gospel Cartoon|
| Religiosos         | Boas Novas, Canção Nova, RIT, IURD|
| Filmes & Séries    | Pluto TV Cine, TV Series          |
| Música             | MTV, KpopTV                       |
| Geral / Variedades | Band, Record, Amazon Sat, etc.    |

## Como implantar no GitHub (atualização automática)

1. Crie um **repositório público** no GitHub
2. Faça upload de **todos os arquivos** desta pasta (incluindo a pasta `.github`)
3. Vá em **Settings → Actions → General** e permita workflows
4. Vá em **Actions** → **Update Brazil M3U every 6h** → **Run workflow** (primeira vez)
5. Pronto! A lista será atualizada automaticamente a cada 6 horas

### Arquivos importantes

| Arquivo                        | Função                                      |
|--------------------------------|---------------------------------------------|
| `update_playlist.py`           | Script principal de atualização             |
| `brazil_ssiptv.m3u`             | Lista M3U pronta para uso                   |
| `state.json`                   | Estado dos canais (contagem de falhas)      |
| `.github/workflows/update.yml` | Agendamento automático (cron 6h)            |
| `requirements.txt`             | Dependências Python                         |

## Executar localmente

```bash
pip install -r requirements.txt
python update_playlist.py
```

## Aviso

- Os streams são públicos e re-compartilhados pelo iptvcat.com.
- Alguns canais podem estar geo-bloqueados ou offline temporariamente.
- A lógica de 3 falhas consecutivas evita remoção prematura de canais intermitentes.

---
Gerado automaticamente • Fonte: iptvcat.com/brazil__10
