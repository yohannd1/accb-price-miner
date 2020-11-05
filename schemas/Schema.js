// SCHEMA PRODUTO PARA BACKUP
export default class Product {
  static schema = {
    name: 'Produtos',
    primaryKey: 'id',
    properties: {
      id: {type: 'int', indexed: true},
      nome: 'string',
    },
  };
}

// export default class Colect {
//   static schema = {
//     name: 'Coletas',
//     primaryKey: 'coleta_id',
//     properties: {
//       coleta_id: {type: 'int', indexed: true},
//       estabelecimento_id: 'int',
//       coleta_data: 'data',
//       coleta_fechada: 'int',
//       pesquisa_id: 'int',
//     },
//   };
// }

// export default class Search {
//   static schema = {
//     name: 'Pesquisas',
//     primaryKey: 'pesquisa_id',
//     properties: {
//       pesquisa_id: {type: 'int', indexed: true},
//       estabelecimento_id: 'int',
//       pesquisa_data: 'data',
//       pesquisa_fechada: 'int',
//       pesquisa_id: 'int',
//       salario_id: 'int',
//     },
//   };
// }

// export default class Form {
//   static schema = {
//     name: 'Formulario',
//     primaryKey: 'form_id',
//     properties: {
//       form_id: {type: 'int', indexed: true},
//       values: '[]',
//       pesquisa_id: 'int',
//       coleta_id: 'int',
//     },
//   };
// }
