import React, {Component} from 'react';
import {View, Text} from 'react-native';

import Realm from '../service/realm';
import * as axios from 'axios';

export default class Splash extends Component {
  constructor(props) {
    super(props);
    this.state = {
      products: undefined,
    };
  }

  save_product = async (product) => {
    const realm = await Realm();

    realm.write(() => {
      realm.create('Produto', product, 'modified');
    });
  };

  get_product = async () => {
    axios
      .get('http://192.168.137.224:80/request/accb_mobile.php/?PRODUCT')
      .then(function (response) {
        response.data.map((value) => {
          console.log(value);
        });
      })
      .catch(function (error) {
        if (error.response) {
          console.log(error.response.data);
        } else {
          console.log('Error BATATA', error.message);
          return error.response;
        }
      });
  };

  render() {
    return (
      <View style={{flex: 1}}>
        <Text stwyle={{color: 'black'}}>{this.get_product()}</Text>
      </View>
    );
  }
}
