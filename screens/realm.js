import React, {useState} from 'react';
import {View, Text, TouchableHighlight, Alert} from 'react-native';
import Reactotron from 'reactotron-react-native';

import Realm from '../service/realm';
import * as axios from 'axios';

const debug = (title, data) =>
  Reactotron.display({
    name: title,
    value: data,
    preview: JSON.stringify(data).substr(0, 50),
  });

const save_product = async (product) => {
  const realm = await Realm();
  try {
    realm.write(() => {
      realm.create(
        'Produtos',
        {id: parseInt(product.id), nome: String(product.name)},
        'modified',
      );
    });
  } catch (e) {
    console.log('Error on creation');
  }
};

const delete_product = async () => {
  const realm = await Realm();

  let product = realm.objects('Produtos');
  realm.write(() => {
    realm.delete(product);
  });
};

const get_product = () => {
  Alert.alert('sure');
  axios
    .get('http://192.168.137.224:80/request/accb_mobile.php/?PRODUCT')
    .then(function (response) {
      // delete_product();
      response.data.map((value) => {
        save_product(value);
      });
      list_product();
    })
    .catch(function (error) {
      if (error.response) {
        console.log(error.response.data);
      } else {
        console.log('Error BATATA', error.message);
      }
    });
};

const list_product = async () => {
  const realm = await Realm();
  console.log('Realm');
  const data = realm.objects('Produtos');
  data.map((value) => {
    console.log(value.nomeqq);
  });
};

const Product = (props) => {
  return (
    <View style={{flex: 1}}>
      <TouchableHighlight
        style={{
          padding: 10,
          backgroundColor: 'black',
          borderWidth: 1,
          borderColor: 'yellow',
        }}
        onPress={() => get_product()}>
        <Text style={{color: '#fff', textAlign: 'center'}}> meu ovo </Text>
      </TouchableHighlight>
    </View>
  );
};

export default Product;
