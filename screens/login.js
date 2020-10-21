import React, {Component} from 'react';
import {View, Text, SafeAreaView, Image, TouchableOpacity} from 'react-native';
import Inputs from '../components/text_input';
import app from '../styles';
import {heightPercentageToDP} from 'react-native-responsive-screen';
import * as axios from 'axios';

export default class Login extends Component {
  componentDidMount() {
    axios
      .get('http://192.168.137.224:5000/request')
      .then(function (response) {
        console.log(response.data);
      })
      .catch(function (error) {
        if (error.response) {
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.header);
        } else {
          console.log('Error', error.message);
        }
        // console.log(error.config);
        console.log('Error:', error);
      });
  }

  request = () => {
    axios
      .get('http://192.168.137.224:5000/request')
      .then(function (response) {
        console.log(response.data);
      })
      .catch(function (error) {
        if (error.response) {
          console.log(error.response.data);
          console.log(error.response.status);
          console.log(error.response.header);
        } else {
          console.log('Error', error.message);
        }
        console.log(error.config);
      });
  };

  render() {
    const {replace} = this.props.navigation;

    return (
      <SafeAreaView style={{...app.one_color, flex: 1}}>
        <View
          style={{...app.container, marginTop: heightPercentageToDP('15%')}}>
          <Image styles={app.logo} source={require('../img/logo_2.png')} />
          <View style={app.text_wrapper}>
            <Text style={{...app.text}}>
              Bem Vindoª, para continuar com o acesso preencha os dados abaixo.
            </Text>
            <Inputs st={app.text_input} txt="Usuário" />
            <Inputs st={app.text_input} txt="Senha" />
            <TouchableOpacity
              style={{...app.button, ...app.white_color}}
              onPress={() => replace('Coleta')}>
              {/* onPress={() => replace('Coleta')}> */}
              <Text style={app.text_button}>ENTRAR</Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    );
  }
}
