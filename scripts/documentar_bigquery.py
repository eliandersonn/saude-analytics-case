# /// script
# requires-python = ">=3.10"
# dependencies = ["google-cloud-bigquery==3.42.1"]
# ///
"""Publica ou verifica o catálogo versionado, sem modificar dados, IAM ou retenção.

Executar após a carga raw e o Dataform. Declarations não publicam metadados na
origem; este passo também cobre datasets e views de assertions geradas pelo CLI.
"""
import argparse
import json
import re
from pathlib import Path

from google.cloud import bigquery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--location", default="southamerica-east1")
    parser.add_argument("--suffix", default="", help="Exemplo: repro; vazio usa o fluxo principal.")
    parser.add_argument("--apply", action="store_true", help="Sem esta opção, apenas verifica.")
    args = parser.parse_args()
    if args.suffix and not re.fullmatch(r"[A-Za-z0-9_]+", args.suffix):
        parser.error("Sufixo inválido.")

    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "includes/catalogo.json").read_text(encoding="utf-8"))
    client = bigquery.Client(project=args.project, location=args.location)
    suffix = "_" + args.suffix if args.suffix else ""
    environment = "reproducao" if suffix else "case"
    changes = []
    table_count = column_count = 0

    # Validar todos os objetos antes de qualquer escrita: não documentar tabelas desconhecidas.
    for layer, description in catalog["datasets"].items():
        dataset = client.get_dataset(f"{args.project}.{layer}{suffix}")
        if dataset.location.lower() != args.location.lower():
            raise ValueError(f"Localização inesperada: {dataset.dataset_id}")
        prefix = f"TESTE ISOLADO ({args.suffix}); não usado pelo BI principal. " if suffix else "FLUXO PRINCIPAL DO CASE. "
        wanted = prefix + description + " Responsável: autor da entrega. Carga manual; dados simulados."
        labels = dict(dataset.labels or {}, camada=layer, ambiente=environment)
        if dataset.description != wanted or dataset.labels != labels:
            dataset.description, dataset.labels = wanted, labels
            changes.append(("dataset", dataset, ["description", "labels"]))

        objects = list(client.list_tables(dataset.reference))
        expected = {name for name in catalog["tables"] if (
            name.startswith("raw_") if layer == "raw" else
            name.startswith("stg_") if layer == "staging" else
            name.startswith(("dim_", "fato_")) if layer == "analytics" else False
        )}
        if layer != "analytics_assertions" and {t.table_id for t in objects} != expected:
            raise ValueError(f"Inventário divergente em {dataset.dataset_id}")
        if layer == "analytics_assertions" and len(objects) != 24:
            raise ValueError("Esperadas 24 views de assertions; revisar o catálogo após mudar os testes.")

        for item in objects:
            table = client.get_table(item.reference)
            name = table.table_id
            if layer == "analytics_assertions":
                if table.table_type != "VIEW":
                    raise ValueError(f"Assertion não é view: {name}")
                description = catalog["assertions"].get(name)
                if description is None:
                    match = re.fullmatch(r"(?:analytics|staging)_(.+)_assertions_(rowConditions|uniqueKey_0)", name)
                    if not match or match[1] not in catalog["tables"]:
                        raise ValueError(f"Assertion desconhecida: {name}")
                    rule = "campos obrigatórios/condições" if match[2] == "rowConditions" else "unicidade da chave"
                    description = f"Valida {rule} de {match[1]}."
                description += " Diagnóstico: zero linhas significa aprovação; não é histórico de execução."
            else:
                description = catalog["tables"][name]

            # Preservar tipo, modo e demais atributos de cada campo ao alterar a descrição.
            schema = []
            for field in table.schema:
                field_description = catalog["columns"][field.name]
                if layer == "raw":
                    field_description += " Origem preservada como STRING, sem conversão."
                representation = field.to_api_repr()
                representation["description"] = field_description
                schema.append(bigquery.SchemaField.from_api_repr(representation))
            if table.description != description or table.schema != schema:
                table.description, table.schema = description, schema
                changes.append(("table", table, ["description", "schema"]))
            table_count += 1
            column_count += len(schema)

    print(f"Inventário: 4 datasets, {table_count} objetos, {column_count} colunas. Divergências: {len(changes)}.")
    if args.apply:
        for kind, resource, fields in changes:
            # Updates restritos aos metadados; o etag do recurso protege contra alterações concorrentes.
            if kind == "dataset":
                client.update_dataset(resource, fields)
            else:
                client.update_table(resource, fields)
        print("Descrições publicadas. Execute novamente sem --apply para conferir divergências zero.")
    elif changes:
        raise SystemExit("Catálogo divergente. Revise e use --apply para publicar.")


if __name__ == "__main__":
    main()
