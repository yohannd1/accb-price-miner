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
      places: undefined,
      places_all: [],
      places_backup: [],
      placeholder: [],
    };
  }

  render_places = ({item}) => (
    <View key={item.estab}>
      <View style={{...app.container_list}}>
        <Text style={{...app.text_list_first}}>Estabelecimento</Text>
        <Text style={{...app.text_list}}>{item.estab}</Text>
        <Text style={{...app.text_list_first}}>Bairro</Text>
        <Text style={{...app.text_list}}>{item.bairro}</Text>
        <Text style={{...app.text_list_first}}>Cidade</Text>
        <Text style={{...app.text_list}}>{item.cidade}</Text>
        <Text style={{...app.text_list_first}}>Data</Text>
        <Text style={{...app.text_list}}>{item.data}</Text>
        <Text style={{...app.text_list_first}}>Preço Médio</Text>
        <Text style={{...app.text_list}}>{item.preço}</Text>
      </View>
      <View key={item.estab + 1}>
        {this.icon_list(
          '',
          {name_1: 'unlock', name_2: 'shopping-cart', name_3: 'cart-plus'},
          ' ',
        )}
      </View>
    </View>
  );

  search_place = (value) => {
    if (value == 'ALL') {
      this.setState({places: this.state.places_backup, estabelecimento: value});
    } else {
      const new_places = this.state.places_backup.filter((place) => {
        let lower_place = place.estab.toLowerCase();

        let lower_filter = value.toLowerCase();

        return lower_place.indexOf(lower_filter) > -1;
      });
      this.setState({places: new_places, estabelecimento: value});
    }
  };

  set_place_holder = (item) => {
    let placeholder = item.map((value) => {
      return value.estab;
    });
    this.setState({placeholder: placeholder});
  };

  search_city = (value) => {
    this.setState({municipio: value});
    let places;

    this.state.places_all.map((val) => {
      if (val[value] != undefined) {
        places = val[value];
        return;
      }
    });

    this.set_place_holder(places);
    this.setState({places: places, places_backup: places, municipio: value});
  };

  picker_list = (text, type) => {
    if (type == 2) {
      return (
        <View key={'Estabelecimento'} style={app.picker_wrapper}>
          <Picker
            selectedValue={this.state.estabelecimento}
            style={app.picker}
            onValueChange={(value) => this.search_place(value)}>
            <Picker.Item key={'ALL'} label={'Todos'} value={'ALL'} />
            {text.map((val) => {
              return <Picker.Item key={val + val} label={val} value={val} />;
            })}
          </Picker>
        </View>
      );
    } else {
      return (
        <View key={'Cidade'} style={app.picker_wrapper}>
          <Picker
            selectedValue={this.state.municipio}
            style={app.picker}
            onValueChange={(value) => this.search_city(value)}>
            {text.map((val) => {
              return <Picker.Item key={val + val} label={val} value={val} />;
            })}
          </Picker>
        </View>
      );
    }
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

  componentDidMount() {
    let places = [
      {
        estab: 'Supermercado Carisma',
        cidade: 'Itabuna',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Supermercado Meira',
        cidade: 'Itabuna',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Hiper Itão',
        cidade: 'Itabuna',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Supermercado Barateiro',
        cidade: 'Itabuna',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Supermercado Compre Bem',
        cidade: 'Itabuna',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
    ];

    let places_2 = [
      {
        estab: 'Supermercado Carisma',
        cidade: 'Ilhéus',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Supermercado Meira',
        cidade: 'Ilhéus',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
      {
        estab: 'Hiper Itão',
        cidade: 'Ilhéus',
        bairro: 'Centro',
        preço: 'Inexistente',
        data: '04/08/2020',
      },
    ];

    let arr_merge = [];
    arr_merge.push({Itabuna: places});
    arr_merge.push({Ilhéus: places_2});

    this.set_place_holder(places);

    this.setState({
      places: places,
      places_backup: places,
      places_all: arr_merge,
    });
  }

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
          {this.picker_list(['Itabuna', 'Ilhéus'], 1)}
          {this.picker_list(this.state.placeholder, 2)}
        </View>
        <View style={{...app.container_scroll, flex: 1}}>
          <FlatList
            data={this.state.places}
            renderItem={this.render_places}
            keyExtractor={(item, index) =>
              item.estab + (index * 100).toString()
            }
            ListEmptyComponent={() => (
              <View
                style={{
                  flex: 1,
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: 50,
                }}>
                <Text style={{color: 'red', fontSize: 15}}>
                  Nenhum estabelecimento encontrado.
                </Text>
              </View>
            )}
          />
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
