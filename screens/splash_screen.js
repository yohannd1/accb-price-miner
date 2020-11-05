import React, {Component} from 'react';
import {View, Text, SafeAreaView, Image} from 'react-native';
import app from '../styles';
import {heightPercentageToDP} from 'react-native-responsive-screen';

export default class Splash extends Component {
  componentDidMount() {
    const {replace} = this.props.navigation;
    // console.log(this.props);
    setTimeout(() => {
      replace('Login');
    }, 2000);
  }

  render() {
    return (
      <SafeAreaView style={{...app.four_color, flex: 1}}>
        <View
          style={{...app.container, marginTop: heightPercentageToDP('15%')}}>
          <View style={{flexDirection: 'row'}}>
            <Image style={app.logo} source={require('../img/logo.png')} />
            <Image style={app.logo} source={require('../img/logo_2.png')} />
          </View>
          <View style={{...app.one_color, padding: 15, width: '100%'}}>
            <Text style={{...app.text_small, textAlign: 'center'}}>
              Acompanhamento do Custo da Cesta Básica {'\n'}
              {'\n'} Coleta de Preços
              {'\n'}
              {'\n'}Projeto Mobile - PIBITI 2020
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }
}
