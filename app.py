function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
      .setTitle('Questionário de Matemática - Prof. Carlos REI')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// Função para buscar os dados de uma planilha do Google (caso queira puxar as abas B- e S- dinamicamente)
function obterAbasPlanilha() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheets = ss.getSheets();
    var abasBasicas = [];
    var abasSuperior = [];
    
    for (var i = 0; i < sheets.length; i++) {
      var nome = sheets[i].getName();
      if (nome.indexOf("B-") === 0) {
        abasBasicas.push(nome);
      } else if (nome.indexOf("S-") === 0) {
        abasSuperior.push(nome);
      }
    }
    return { basica: abasBasicas, superior: abasSuperior };
  } catch (e) {
    // Retorno padrão caso não esteja vinculado a uma planilha específica com abas
    return { 
      basica: ["B-TABUADA DO 2 AO 9", "B-MATEMATICA BASICA"], 
      superior: ["S-LEGISLACAO EDUCACIONAL", "S-MATEMATICA SUPERIOR"] 
    };
  }
}
