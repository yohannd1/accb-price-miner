import * as React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';

// Telas
import Splash from './screens/splash_screen';
import Login from './screens/login';
import Coleta from './screens/coleta';
import Form from './screens/form';

const Stack = createStackNavigator();

function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{headerShown: false}}>
        <Stack.Screen name="Form" component={Form} />
        <Stack.Screen name="Home" component={Splash} />
        <Stack.Screen name="Login" component={Login} />
        <Stack.Screen name="Coleta" component={Coleta} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default App;
