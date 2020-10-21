import React, {Component} from 'react';
import {View, Text, SafeAreaView, Image} from 'react-native';
import app from '../styles';
import {heightPercentageToDP} from 'react-native-responsive-screen';

const Realm = require('realm');

export default class Splash extends Component {
  constructor(props) {wW
    super(props);
    this.state = {realm: null};
  }

  componentDidMount() {
    Realm.open({
      schema: [{name: 'Dog', properties: {name: 'string'}}],
    }).then((realm) => {
      realm.write(() => {
        realm.create('Dog', {name: 'Rex'});
      });
      this.setState({realm});
    });
  }

  componentWillUnmount() {
    // Close the realm if there is one open.
    const {realm} = this.state;
    if (realm !== null && !realm.isClosed) {
      realm.close();
    }
  }

  render() {
    const info = this.state.realm
      ? 'Number of dogs in this Realm: ' +
        this.state.realm.objects('Dog').length
      : 'Loading...';

    return (
      <View style={{flex: 1}}>
        <Text style={{color: 'black'}}>{info}</Text>
      </View>
    );
  }
}
