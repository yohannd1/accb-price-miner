import React from 'react';
import {TouchableOpacity, TextInput, View, Text} from 'react-native';
import app from '../styles';
import {Formik} from 'formik';
import {widthPercentageToDP as wp} from 'react-native-responsive-screen';

export default function ReviewForm(prop) {
  return (
    <Formik
      initialValues={{
        value_1: '',
        value_2: '',
        value_3: '',
        value_4: '',
        value_5: '',
      }}
      onSubmit={(values) => {
        prop.close_modal();
        // const array = [];
        // array.push(values.value_1);
        // array.push(values.value_2);
        // array.push(values.value_3);
        // array.push(values.value_4);
        // array.push(values.value_5);
        console.log(values);
        prop.save(values);
      }}>
      {(props) => (
        <View
          style={{
            ...app.container_items,
            marginTop: wp('5%'),
            marginBottom: wp('5%'),
            ...app.one_color,
            paddingVertical: wp('3%'),
          }}>
          <TextInput
            style={app.input_modal}
            placeholder="0,00 R$"
            onChangeText={props.handleChange('value_1')}
            value={props.values.value_1}
            keyboardType={'numeric'}
          />
          <TextInput
            style={app.input_modal}
            placeholder="0,00 R$"
            onChangeText={props.handleChange('value_2')}
            value={props.values.value_2}
            keyboardType={'numeric'}
          />
          <TextInput
            style={app.input_modal}
            placeholder="0,00 R$"
            onChangeText={props.handleChange('value_3')}
            value={props.values.value_3}
            keyboardType={'numeric'}
          />
          <TextInput
            style={app.input_modal}
            placeholder="0,00 R$"
            onChangeText={props.handleChange('value_4')}
            value={props.values.value_4}
            keyboardType={'numeric'}
          />
          <TextInput
            style={app.input_modal}
            placeholder="0,00 R$"
            onChangeText={props.handleChange('value_5')}
            value={props.values.value_5}
            keyboardType={'numeric'}
          />
          <View style={{...app.button_wrap, marginTop: wp('2%	')}}>
            <TouchableOpacity
              title="Submit"
              onPress={() => props.handleSubmit()}
              style={{...app.open_button}}>
              <Text
                style={{
                  textAlign: 'center',
                  color: '#2196F3',
                  fontFamily: 'times',
                  fontSize: 18,
                }}>
                Fechar
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => props.handleSubmit()}
              style={{...app.open_button, marginLeft: 10}}>
              <Text
                style={{
                  textAlign: 'center',
                  color: '#2196F3',
                  fontFamily: 'times',
                  fontSize: 18,
                }}>
                Salvar
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </Formik>
  );
}
