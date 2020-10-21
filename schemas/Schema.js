// SCHEMA PRODUTO PARA BACKUP
export default class Produto {
  static schema = {
    name: 'Produtos',
    primaryKey: 'id',
    properties: {
      id: {type: 'int', indexed: true},
      nome: 'string',
    },
  };
}
