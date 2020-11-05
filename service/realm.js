import Realm from 'realm';

import Product from '../schemas/Schema';

export default function getRealm() {
  return Realm.open({
    schema: [Product],
  });
}
