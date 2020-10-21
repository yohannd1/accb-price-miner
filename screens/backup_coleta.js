import React, {Component, useState} from 'react';
import {
  View,
  Text,
  SafeAreaView,
  Image,
  Modal,
  TouchableHighlight,
  FlatList,
} from 'react-native';

import Icon from 'react-native-vector-icons/FontAwesome';
import {Picker} from '@react-native-community/picker';
import {ScrollView} from 'react-native-gesture-handler';

import app from '../styles';
import {heightPercentageToDP as wp} from 'react-native-responsive-screen';

export default class Form extends Component {
  constructor(props) {
    super(props);
    this.state = {
      municipio: 'itabuna',
      estabelecimento: 'mercado',
      modalVisible: false,
    };
  }

  place_list = () => {
    return (
      <View>
        <View style={{...app.container_list}}>
          <Text style={{...app.text_list_first}}>Estabelecimento</Text>
          <Text style={{...app.text_list}}>Super Mercado Carisma</Text>
          <Text style={{...app.text_list_first}}>Bairro</Text>
          <Text style={{...app.text_list}}>Centro</Text>
          <Text style={{...app.text_list_first}}>Cidade</Text>
          <Text style={{...app.text_list}}>Itabuna</Text>
          <Text style={{...app.text_list_first}}>Data</Text>
          <Text style={{...app.text_list}}>04/08/2020</Text>
          <Text style={{...app.text_list_first}}>Preço Médio</Text>
          <Text style={{...app.text_list}}>Inexistente</Text>
        </View>
        <View>
          {this.icon_list(
            '',
            {name_1: 'unlock', name_2: 'shopping-cart', name_3: 'cart-plus'},
            ' ',
          )}
        </View>
      </View>
    );
  };

  picker_list = (text) => {
    return (
      <View style={app.picker_wrapper}>
        <Picker
          selectedValue={this.state.municipio}
          style={app.picker}
          onValueChange={(itemValue, itemIndex) =>
            this.setState({municipio: itemValue})
          }>
          {text.map((val) => {
            return <Picker.Item label={val} value={val} />;
          })}
        </Picker>
      </View>
    );
  };

  icon_list = (text, icon, type) => {
    const {navigate} = this.props.navigation;
    // MODAL
    if (type == 'text') {
      return (
        <View
          style={{
            width: wp('20%'),
            alignContent: 'center',
            justifyContent: 'center',
          }}>
          <Icon
            //   3B9CE2
            color={'#fff'}
            style={{textAlign: 'center'}}
            name={icon}
            size={40}></Icon>
          <Text style={{...app.text_icon, marginBottom: 10}}>{text}</Text>
        </View>
      );
    } else {
      return (
        <View
          style={{
            ...app.container_icon_button,
          }}>
          <Icon.Button
            style={{marginLeft: 10}}
            color={'#3B9CE2'}
            name={icon.name_1}
            size={35}
            backgroundColor={'rgba(255,255,255,0)'}></Icon.Button>
          <Icon.Button
            style={{marginLeft: 10}}
            color={'#3B9CE2'}
            name={icon.name_2}
            size={35}
            backgroundColor={'rgba(255,255,255,0)'}
            onPress={() => navigate('Form')}></Icon.Button>
          <Icon.Button
            style={{marginLeft: 10}}
            color={'#3B9CE2'}
            name={icon.name_3}
            size={35}
            backgroundColor={'rgba(255,255,255,0)'}
            onPress={() => navigate('Form')}></Icon.Button>
        </View>
      );
    }
  };

  render() {
    return (
      <SafeAreaView style={{...app.four_color, flex: 1}}>
        <View style={{...app.item_side, marginLeft: '5%'}}>
          <Image style={app.logo_small} source={require('../img/logo.png')} />
          <Image style={app.logo_small} source={require('../img/logo_2.png')} />
          <TouchableHighlight
            style={app.modal_button}
            onPress={() => {
              this.setState({modalVisible: true});
            }}>
            <Icon
              color={'rgba(255,255,255,0.8)'}
              name={'exclamation'}
              size={25}></Icon>
          </TouchableHighlight>
        </View>
        <View
          style={{
            ...app.container_banner,
            marginTop: wp('2%'),
          }}>
          <View style={app.text_wrapper}>
            <Text style={{...app.text_banner, ...app.one_color}}>
              Bem vinda Mônica, abaixo você encontrará os produtos da atual
              coleta do mês de outubro. Realize uma ação para continuar para o
              formulário do estabelecimento.
            </Text>
          </View>
        </View>
        <View style={{...app.container_items}}>
          {this.picker_list(['Itabuna', 'Ilhéus'])}
          {this.picker_list([
            'Supermercado Carisma',
            'Supermercado Meira',
            'Hiper Itão',
            'Supermercado Barateiro',
            'Supermercado Compre Bem',
          ])}
        </View>
        <ScrollView style={{...app.container_scroll}}>
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
          {this.place_list()}
        </ScrollView>
        <Modal
          animationType="fade"
          transparent={true}
          visible={this.state.modalVisible}
          onRequestClose={() => {
            this.setState({modalVisible: false});
          }}>
          <View style={app.modal_view}>
            <View style={app.modal_content}>
              <Text style={{...app.modal_title, ...app.one_color}}>
                Legenda Coleta
              </Text>
              <View
                style={{
                  ...app.container_items,
                  marginTop: wp('5%'),
                  marginBottom: wp('5%'),
                  ...app.one_color,
                  paddingVertical: wp('3%'),
                }}>
                {this.icon_list('Coleta encerrada.', 'lock', 'text')}
                {this.icon_list('Coleta em andamento.', 'unlock', 'text')}
                {this.icon_list('Coleta manual.', 'shopping-cart', 'text')}
                {this.icon_list('Coleta automática.', 'cart-plus', 'text')}
              </View>

              <TouchableHighlight
                style={{...app.open_button}}
                onPress={() => {
                  this.setState({modalVisible: !this.state.modalVisible});
                }}>
                <Text
                  style={{
                    textAlign: 'center',
                    color: '#fff',
                    fontFamily: 'times',
                    fontSize: 18,
                  }}>
                  Fechar
                </Text>
              </TouchableHighlight>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    );
  }
}
