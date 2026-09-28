# Executar o Dataform

O projeto cria três tabelas em `staging`, seis dimensões e uma fato em `analytics`, além de 24 assertions de qualidade. Dataform Core e CLI estão fixados em **3.0.71**. A execução usa tabelas completas, sem agendamento. Pode ser feita localmente pela CLI ou pelo serviço Dataform do GCP.

## 1. Pré-requisitos

- Git, Node.js e npm. Ambiente verificado: Node 22.20.0 e npm 10.9.3.
- Google Cloud CLI, incluindo `bq`, e PowerShell para os comandos abaixo.
- `uv` para executar o publicador de metadados em Python, com a dependência BigQuery fixada no próprio script.
- Projeto GCP com BigQuery habilitado, cota disponível e permissões para criar datasets, carregar/alterar tabelas e executar consultas. Se o projeto do avaliador exigir faturamento, essa configuração pertence à conta dele; a conexão ao GitHub público não usa Secret Manager.
- Acesso ao [repositório público](https://github.com/eliandersonn/saude-analytics-case) ou ao ZIP. Acesso ao GitHub não concede acesso ao GCP.

Clonar o repositório, ou extrair o ZIP e abrir um terminal na raiz:

```powershell
git clone https://github.com/eliandersonn/saude-analytics-case.git
cd saude-analytics-case
$CaseProject = 'SEU_PROJETO_GCP'
$CaseLocation = 'southamerica-east1'
```

Autenticar a CLI pelo fluxo de login da instalação do Google Cloud CLI. Para o Dataform, configurar também Application Default Credentials (ADC, credenciais usadas pela aplicação):

```powershell
gcloud auth application-default login --project=$CaseProject --quiet
```

O comando abre um fluxo interativo no navegador. Em Windows, usar `gcloud.cmd` se `gcloud` resolver para um arquivo sem extensão que não execute. O `bq` usa a autenticação da CLI; o Dataform usa ADC.

## 2. Criar datasets e carregar os CSVs

Criar os quatro datasets na mesma localização. Se já existirem, verificar a localização e pular a criação correspondente.

```powershell
bq --project_id=$CaseProject --location=$CaseLocation mk -d "${CaseProject}:raw"
bq --project_id=$CaseProject --location=$CaseLocation mk -d "${CaseProject}:staging"
bq --project_id=$CaseProject --location=$CaseLocation mk -d "${CaseProject}:analytics"
bq --project_id=$CaseProject --location=$CaseLocation mk -d "${CaseProject}:analytics_assertions"
./scripts/carregar_raw.ps1 -ProjectId $CaseProject -Location $CaseLocation
```

O script lê os cabeçalhos, carrega todas as colunas como `STRING` e ignora a primeira linha. **Reexecutar substitui as três tabelas raw de mesmo nome** pelos CSVs desta entrega. As conversões ficam nas tabelas `stg_*.sqlx`.

## 3. Compilar e executar

```powershell
@{ projectId = $CaseProject; location = $CaseLocation } | ConvertTo-Json | Set-Content -Encoding ASCII .df-credentials.json
npm ci
npx dataform compile . --default-database=$CaseProject --default-location=$CaseLocation
npx dataform run . --default-database=$CaseProject --default-location=$CaseLocation
```

Interromper se algum comando falhar. Os parâmetros substituem o projeto e a localização do `workflow_settings.yaml`, sem editar o arquivo. `.df-credentials.json` contém apenas identificação do projeto/localização e é ignorado pelo Git. Nunca copiar chaves privadas para o repositório.

## 4. Publicar e conferir o catálogo

Após a execução, publicar as descrições na raiz do repositório:

```powershell
uv run scripts/documentar_bigquery.py --project $CaseProject --location $CaseLocation --apply
uv run scripts/documentar_bigquery.py --project $CaseProject --location $CaseLocation
```

O segundo comando deve informar **zero divergências**. O catálogo em `includes/catalogo.json` é compartilhado pelos SQLX e pelo script. O Dataform documenta as dez tabelas de saída; o script completa datasets, origens declaradas e views de assertions. Repetir esse passo após recargas/execuções, pois objetos recriados podem perder metadados. Sem `--apply`, o script somente verifica e retorna erro se houver divergência. Não modifica dados, acessos ou expiração.

## 5. Conferir o resultado

Esperado: **34 ações concluídas, sendo dez tabelas e 24 assertions**, sem erros. As assertions retornam zero linhas quando aprovadas. Conferir no BigQuery:

| Verificação | Esperado |
| --- | --- |
| Atendimentos distintos na fato | 60 |
| Linhas da fato | 155 |
| Linhas da dimensão Paciente | 18, sendo cinco versões desconhecidas |
| Itens com histórico desconhecido | 20 |
| Soma bruto / desconto / líquido | R$ 41.285,00 / R$ 2.767,25 / R$ 38.517,75 |

## Dataform no console GCP

No [console Dataform](https://console.cloud.google.com/bigquery/dataform?project=saude-analytics), abrir o repositório **saude-analytics-case**, região **southamerica-east1**, e criar um workspace a partir da branch `main`. O grafo compilado contém três origens declaradas, dez tabelas e 24 assertions. Em **Workflow Execution Logs**, a execução gerenciada aprovou as 34 ações.

### Conexão GitHub pública sem faturamento

O repositório [eliandersonn/saude-analytics-case](https://github.com/eliandersonn/saude-analytics-case) é público. O Dataform está ligado por HTTPS à branch `main`, sem Secret Manager ou token. Os arquivos Dataform ficam na raiz do GitHub, como exige `workflow_settings.yaml`.

O serviço consegue ler `main` e compilar diretamente um commit remoto. No workspace, usar **Pull from Git** após cada push no GitHub e então compilar. Um push no GitHub não atualiza automaticamente o workspace já aberto. Esta conexão sem credencial é de **leitura**; edições feitas na interface não podem ser enviadas ao GitHub pelo Dataform. Fazer alterações e commits no repositório local/GitHub. Execução agendada e CI/CD continuam fora do case.

O Dataform compilou o commit remoto sem erros. [Documentação de conexão Git](https://docs.cloud.google.com/dataform/docs/connect-repository).

## Teste isolado opcional

Criar `raw_repro`, `staging_repro`, `analytics_repro` e `analytics_assertions_repro` no projeto de teste. Na raiz, carregar com `-RawDataset raw_repro`. Acrescentar **os dois parâmetros** aos comandos de compilação e execução:

```powershell
npx dataform compile . --default-database=$CaseProject --default-location=$CaseLocation --schema-suffix=repro --vars=rawDataset=raw_repro
npx dataform run . --default-database=$CaseProject --default-location=$CaseLocation --schema-suffix=repro --vars=rawDataset=raw_repro
```

O sufixo isola as saídas; a variável seleciona a origem. Não alterar apenas `--default-schema`, pois os SQLX declaram seus schemas explicitamente. Em CI, usar projeto de testes e identidade sem escrita em produção.

Na raiz, documentar/verificar esse ambiente acrescentando `--suffix repro` ao script de metadados. Os quatro datasets `_repro` são opcionais e não alimentam o BI principal. Na entrega atual, permanecem identificados como teste isolado; não são uma segunda camada de produção. Sua remoção após a avaliação deve ser uma ação explícita, restrita a esse ambiente.

## Decisões e limites

- `raw_*.sqlx`: origens; `stg_*.sqlx`: tipos; `dim_*.sqlx`: dimensões; `fato_*.sqlx`: rateio e medidas; `assert_*.sqlx`: validações adicionais.
- Reconstrução completa pode renumerar SKs quando chega histórico anterior. Fato e dimensões são reconstruídas no fluxo, sem transação única. Carga incremental permanente exigiria persistir a atribuição de SKs.
- Datas sem fuso são interpretadas como UTC. Confirmar essa premissa em produção.
- Todos os status permanecem. Indicadores financeiros exigem filtro explícito.
- Se ocorrer `Access Denied`, revisar as permissões do executor. Para `Not found` ou erro de localização, revisar projeto, região e carga raw. Compilar com sucesso não substitui executar e verificar as assertions.

Referência: [Dataform CLI](https://docs.cloud.google.com/dataform/docs/use-dataform-cli). Resultados, decisões e lacunas conhecidas estão na [solução técnica](SOLUCAO_TECNICA.md).
