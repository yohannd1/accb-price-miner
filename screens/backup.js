import React, {Component} from 'react';
import {
  View,
  Text,
  SafeAreaView,
  Image,
  Modal,
  TouchableOpacity,
} from 'react-native';
import app from '../styles';
import {heightPercentageToDP as wp} from 'react-native-responsive-screen';
import Forms from '../components/formik.js';

export default class Form extends Component {
  constructor(props) {
    super(props);
    this.state = {
      modalVisible: true,
      values: [],
      products: [],
    };
  }

  product_info = (type) => {
    if (type == 1) {
      return (
        <View style={{...app.container_items, width: '44%'}}>
          <Text
            style={{
              ...app.text,
              margin: 3,
              backgroundColor: '#fff',
              borderRadius: 5,
              color: '#000',
            }}>
            PREÇO
          </Text>
          <Text
            style={{
              ...app.text,
              borderWidth: 1,
              borderColor: '#fff',
              margin: 3,
              borderRadius: 5,
            }}>
            15,30R$
          </Text>
        </View>
      );
    } else {
      return (
        <View style={{...app.container_items, width: '44%'}}>
          <Text
            style={{
              ...app.text,
              margin: 3,
              backgroundColor: '#fff',
              borderRadius: 5,
              color: '#000',
            }}>
            PREÇO
          </Text>
          <Text
            style={{
              ...app.text,
              borderWidth: 1,
              borderColor: '#fff',
              margin: 3,
              borderRadius: 5,
            }}>
            00,00 R$
          </Text>
        </View>
      );
    }
  };

  product_button = (text) => {
    return (
      <View style={{...app.button_wrap}}>
        <TouchableOpacity
          onPress={
            text == 'Carne' || text == 'Pão'
              ? () => {
                  this.setState({modalVisible: true});
                }
              : () => {
                  this.setState({modalVisible: true});
                }
          }>
          <Text
            style={
              text == 'Carne' || text == 'Pão'
                ? app.button_product
                : {
                    ...app.button_product,
                    color: 'black',
                    backgroundColor: '#fff',
                  }
            }>
            {text}
          </Text>
        </TouchableOpacity>
      </View>
    );
  };
  render() {
    const {navigate} = this.props.navigation;

    return (
      <SafeAreaView style={{...app.four_color, flex: 1}}>
        <View style={{...app.item_side, marginLeft: '5%'}}>
          <Image style={app.logo_small} source={require('../img/logo.png')} />
          <Image style={app.logo_small} source={require('../img/logo_2.png')} />
        </View>
        <View
          style={{
            ...app.container_banner,
          }}>
          <View style={app.text_wrapper}>
            <Text style={{...app.text_banner, ...app.one_color}}>
              {/* Bem vindo Mônica, abaixo você encontrará os produtos da atual
              coleta do mês de Outubro. Selecione um produto para preencher o
              formulário e realize uma ação para continuar.  */}
              (O formulário abaixo é um exemplo de itens não preenchidos, ou
              seja, os preenchidos coloridos e os não preenchidos sem cor de
              fundo).
            </Text>
          </View>
        </View>
        <View style={{...app.container_items}}>
          {this.product_button('Carne')}
          {this.product_button('Arroz')}
          {this.product_button('Pão')}
          {this.product_button('Café')}
          {this.product_button('Farinha')}
          {this.product_button('Leite')}
          {this.product_button('Manteiga')}
          {this.product_button('Óleo')}
          {this.product_button('Tomate')}
          {this.product_button('Manteiga')}
        </View>
        <View style={{...app.container_items, marginTop: wp('-7%')}}>
          <TouchableOpacity onPress={() => navigate('Coleta')}>
            <Text style={{...app.button_menu}}>Cancelar</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigate('Coleta')}>
            <Text style={{...app.button_menu}}>Salvar</Text>
          </TouchableOpacity>
        </View>
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
                Preços do Produto
              </Text>
              <View
                style={{
                  ...app.container_items,
                  marginTop: wp('5%'),
                  marginBottom: wp('5%'),
                  ...app.one_color,
                  paddingVertical: wp('3%'),
                }}>
                <Forms
                  close_modal={() =>
                    this.setState({
                      modalVisible: !this.state.modalVisible,
                    })
                  }
                />
              </View>
            </View>
          </View>
        </Modal>
        <Modal
          animationType="fade"
          transparent={true}
          visible={this.state.modalVisible1}
          onRequestClose={() => {
            this.setState({modalVisible1: false});
          }}>
          <View style={app.modal_view}>
            <View style={app.modal_content}>
              <Text style={{...app.modal_title, ...app.one_color}}>
                Preços do Produto
              </Text>
              <View
                style={{
                  ...app.container_items,
                  marginTop: wp('5%'),
                  marginBottom: wp('5%'),
                  ...app.one_color,
                  paddingVertical: wp('3%'),
                }}>
                {this.product_info(0)}
                {this.product_info(0)}
                {this.product_info(0)}
                {this.product_info(0)}
                {this.product_info(0)}
                {this.product_info(0)}
              </View>
              <View style={app.button_wrap}>
                <TouchableOpacity
                  style={{...app.open_button}}
                  onPress={() => {
                    this.setState({modalVisible1: !this.state.modalVisible1});
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
                </TouchableOpacity>
                <TouchableOpacity
                  style={{...app.open_button, marginLeft: 10}}
                  onPress={() => {
                    this.setState({modalVisible1: !this.state.modalVisible1});
                  }}>
                  <Text
                    style={{
                      textAlign: 'center',
                      color: '#fff',
                      fontFamily: 'times',
                      fontSize: 18,
                    }}>
                    Salvar
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    );
  }
}
