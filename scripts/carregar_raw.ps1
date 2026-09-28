# Objetivo: carregar os tres CSVs originais no BigQuery para o Dataform tratar os tipos.
# Parametros explicitam o projeto, a regiao e o dataset que receberao os dados.
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9-]{4,28}[a-z0-9]$')]
    [string]$ProjectId,
    [string]$Location = 'southamerica-east1',
    [ValidatePattern('^[A-Za-z_][A-Za-z0-9_]*$')]
    [string]$RawDataset = 'raw'
)

# O dataset deve existir. Reexecutar substitui somente as tres tabelas abaixo.
$ErrorActionPreference = 'Stop'
# Preferir o executavel Windows; usar bq quando o ambiente disponibilizar esse comando.
$bqCommand = (Get-Command bq.cmd -ErrorAction SilentlyContinue).Source
if (-not $bqCommand) { $bqCommand = (Get-Command bq -ErrorAction Stop).Source }
# Resolver a origem a partir do script permite executa-lo de qualquer pasta.
$rawPath = Join-Path $PSScriptRoot '../dados/raw'
$tables = @('raw_atendimentos', 'raw_procedimentos_itens', 'raw_cadastro_pacientes')

foreach ($table in $tables) {
    $csvPath = (Resolve-Path (Join-Path $rawPath "$table.csv")).Path
    # Usar o cabecalho para montar o schema, preservando todos os valores como texto.
    $columns = (Get-Content -LiteralPath $csvPath -Encoding UTF8 -TotalCount 1).Split(',')
    $schema = ($columns | ForEach-Object { "${_}:STRING" }) -join ','
    # Substituir a tabela para evitar duplicidade na recarga e ignorar a linha do cabecalho.
    & $bqCommand "--project_id=$ProjectId" "--location=$Location" load --replace --source_format=CSV --skip_leading_rows=1 "${ProjectId}:${RawDataset}.${table}" $csvPath $schema
    # Interromper a carga se o comando externo falhar, sem continuar com origem incompleta.
    if ($LASTEXITCODE -ne 0) { throw "Falha ao carregar $table (codigo $LASTEXITCODE)." }
}
