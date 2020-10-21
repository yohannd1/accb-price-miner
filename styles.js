import {StyleSheet, Dimensions} from 'react-native';

import {
  widthPercentageToDP as wp,
  heightPercentageToDP as hp,
  listenOrientationChange as loc,
  removeOrientationListener as rol,
} from 'react-native-responsive-screen';

const width_x = Dimensions.get('window').width;
// const heigth_y = Dimensions.get('window').heigth;

const app = StyleSheet.create({
  //   MAIN STYLES
  container: {
    alignItems: 'center',
    flex: 1,
  },
  container_banner: {
    alignItems: 'center',
    width: wp('100%'),
    marginBottom: '5%',
  },
  container_items: {
    alignContent: 'space-between',
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: wp('100%'),
    justifyContent: 'center',
  },
  container_scroll: {
    width: wp('100%'),
    marginBottom: hp('1%'),
    marginTop: hp('1%'),
  },

  container_list: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: wp('85%'),
    height: hp('20%'),
    backgroundColor: 'rgba(255,255,255,0.5)',
    marginTop: 15,
    marginLeft: wp('7.5%'),
  },
  container_icon: {
    padding: 10,
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: wp('50%'),
  },
  container_icon_button: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.5)',
    marginBottom: hp('1%'),
    width: wp('85%'),
    marginLeft: wp('7.5%'),
    borderRadius: 3,
    marginTop: hp('1%'),
  },
  modal_view: {
    width: wp('100%'),
    height: hp('110%'),
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal_content: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: hp('4%'),
    backgroundColor: 'rgba(255,255,255,0.8)',
  },
  modal_title: {
    marginTop: hp('-4%'),
    width: wp('100%'),
    padding: 25,
    fontSize: wp('4%'),
    color: '#fff',
    textAlign: 'center',
    fontFamily: 'times',
    fontWeight: 'bold',
  },
  item_side: {
    width: wp('100%'),
    alignContent: 'space-between',
    flexDirection: 'row',
  },
  text_wrapper: {
    width: wp('100%'),
    alignItems: 'center',
    alignContent: 'center',
    textAlign: 'center',
  },
  text_title: {
    fontSize: hp('5%'),
  },
  text_button: {
    fontSize: hp('2.5%'),
    color: '#3B9CE2',
    fontFamily: 'Georgia',
  },
  text: {
    padding: 10,
    fontSize: wp('4%'),
    color: '#fff',
    textAlign: 'center',
    fontFamily: 'times',
  },
  text_banner: {
    fontSize: wp('4%'),
    color: '#fff',
    textAlign: 'center',
    fontFamily: 'times',
    paddingHorizontal: '2%',
    paddingVertical: '4%',
  },
  text_small: {
    fontSize: wp('3.5%'),
    color: '#fff',
    textAlign: 'center',
    fontFamily: 'times',
    fontWeight: 'bold',
  },
  text_icon: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: wp('3.1%'),
    marginTop: hp('1.5%'),
    marginLeft: hp('1%'),
    textAlign: 'center',
  },
  text_list: {
    color: '#000',
    fontSize: wp('3%'),
    marginTop: hp('1.5%'),
    marginLeft: hp('5%'),
    width: wp('35%'),
  },
  text_list_first: {
    color: '#000',
    fontSize: wp('3%'),
    marginTop: hp('1.5%'),
    marginLeft: hp('5%'),
    width: wp('25%'),
  },
  one_color: {
    backgroundColor: '#3B9CE2',
  },
  two_color: {
    backgroundColor: '#4AACCF',
  },
  white_color: {
    backgroundColor: '#fff',
  },
  three_color: {
    backgroundColor: '#D1E2EE',
  },
  four_color: {
    backgroundColor: '#7AACCF',
  },
  //   LOGO
  logo: {
    width: 100,
    height: 115,
    resizeMode: 'stretch',
    marginBottom: 15,
  },
  logo_small: {
    width: hp('6%'),
    height: hp('6%'),
    resizeMode: 'stretch',
    marginBottom: 15,
    marginTop: hp('2%'),
  },
  //   BOTÕES
  button: {
    borderRadius: 3,
    alignItems: 'center',
    padding: 5,
    marginTop: 10,
    width: wp('50%'),
  },
  open_button: {
    width: wp('30%'),
    borderRadius: 5,
    padding: 10,
    elevation: 2,
    textAlign: 'center',
    backgroundColor: '#2196F3',
  },
  modal_button: {
    right: wp('10%'),
    top: hp('2%'),
    position: 'absolute',
    width: wp('8%'),
    borderRadius: 5,
    padding: wp('3%'),
    textAlign: 'center',
    backgroundColor: '#2196F3',
  },
  button_wrap: {
    alignContent: 'space-between',
    flexDirection: 'row',
  },
  button_product: {
    borderRadius: 5,
    alignItems: 'center',
    paddingVertical: '3%',
    paddingHorizontal: '5%',
    margin: 11,
    fontSize: wp('4%'),
    borderWidth: 1,
    borderColor: '#fff',
    fontFamily: 'times',
    color: '#fff',
    width: wp('33.33%'),
    textAlign: 'center',
  },
  button_item: {
    textAlign: 'center',
    borderRadius: 5,
    padding: '3%',
    marginTop: hp('1.5%'),
    marginBottom: hp('1.7%'),
    borderWidth: 1,
    fontWeight: 'bold',
    borderColor: '#fff',
  },
  button_menu: {
    textAlign: 'center',
    borderRadius: 5,
    alignItems: 'center',
    paddingVertical: '3%',
    paddingHorizontal: '5%',
    margin: 11,
    marginTop: hp('10%'),
    fontSize: wp('4%'),
    borderWidth: 1,
    borderColor: '#fff',
    backgroundColor: '#fff',
    width: wp('33.33%'),
    fontFamily: 'times',
  },
  //   INPUT
  text_input: {
    height: 40,
    padding: wp('3%'),
    borderColor: 'white',
    borderWidth: 1,
    marginBottom: 10,
    marginTop: 10,
    fontFamily: 'times',
    color: '#fff',
    width: wp('80%'),
  },
  picker_wrapper: {
    padding: wp('1%'),
    margin: wp('1%'),
    borderRadius: 5,
    backgroundColor: 'rgba(255,255,255,0.7)',
  },
  picker: {
    height: hp('5%'),
    width: wp('40%'),
    fontSize: wp('5%'),
    color: '#000',
  },
});

export default app;
