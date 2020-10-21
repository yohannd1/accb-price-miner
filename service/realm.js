import Realm from 'realm';

import Produto from '../schemas/Schema';

export default function getRealm() {
  return Realm.open({
    schema: [Produto],
  });
}
