# Case de Analytics Engineering em Saúde

Modelo dimensional Kimball, transformação Dataform/BigQuery, qualidade, FinOps e governança, conforme o [enunciado](referencias/desafio_tecnico_analytics_engineering_candidato.pdf).

## Como avaliar

1. Ler a [solução técnica](docs/SOLUCAO_TECNICA.md): quatro partes do case, modelo, catálogo, resultados e limites conhecidos.
2. Inspecionar os [SQLX e testes](definitions/) e seguir o [guia de execução](docs/EXECUCAO.md) para reproduzir.
3. Abrir a [apresentação HTML](docs/APRESENTACAO.html) no navegador: oito slides para 24 minutos de conteúdo e seis de perguntas.

```text
dados/raw/       3 CSVs fornecidos no desafio
definitions/     transformações e assertions Dataform
includes/        catálogo de metadados compartilhado
package*.json    dependências do Dataform
workflow_settings.yaml  projeto e localização padrão
docs/            solução técnica, execução e apresentação
referencias/     PDF do desafio
scripts/         carga dos CSVs e publicação do catálogo
```

**Executado:** dez tabelas, 24 assertions aprovadas e 155 itens reconciliados. **Proposto:** arquitetura Snowflake e fluxo de CI/CD, sem implantação. As lacunas de cobertura dos testes estão explícitas na solução técnica.

**Governança:** catálogo versionado e descrições de datasets, tabelas e colunas no BigQuery. Fluxo principal: `raw → staging → analytics`, com testes em `analytics_assertions`. Datasets `_repro` são somente o ambiente isolado de reprodução. O guia inclui publicação e verificação dos metadados após a carga.

**Dataform no GCP:** repositório `saude-analytics-case`, região `southamerica-east1`, ligado à branch pública `main` no GitHub. A execução gerenciada concluiu 34 ações. O [guia](docs/EXECUCAO.md#dataform-no-console-gcp) explica o fluxo. Sem credencial, a conexão Git permite leitura; editar no GitHub/local e fazer pull no Dataform.

O HTML funciona sem internet, em formato de slides e sem botões: use as setas do teclado para navegar. Baixar o arquivo ou extrair o ZIP; a visualização de código do GitHub não executa HTML.

Entrega pelo [repositório público](https://github.com/eliandersonn/saude-analytics-case) ou ZIP. Acesso ao GitHub não concede acesso ao GCP; a reprodução exige projeto e permissões próprios. Dependências instaladas, credenciais e arquivos de trabalho não integram o pacote.
