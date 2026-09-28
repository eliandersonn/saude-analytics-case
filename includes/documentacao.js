// O catálogo é compartilhado pelo Dataform e pelo publicador de metadados do BigQuery.
const catalogo = require("./catalogo.json");

function tabela(nome, colunas) {
  if (!catalogo.tables[nome]) throw new Error(`Tabela sem descrição: ${nome}`);
  return {
    description: catalogo.tables[nome],
    columns: Object.fromEntries(colunas.map(coluna => {
      if (!catalogo.columns[coluna]) throw new Error(`Coluna sem descrição: ${coluna}`);
      const origem = nome.startsWith("raw_") ? " Origem preservada como STRING, sem conversão." : "";
      return [coluna, catalogo.columns[coluna] + origem];
    }))
  };
}

module.exports = { tabela, assertions: catalogo.assertions };
