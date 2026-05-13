import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet
} from 'react-native';

export default function App() {

  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [bmi, setBmi] = useState('');
  const [status, setStatus] = useState('');

  const calculateBMI = () => {

    const h = parseFloat(height) / 100;
    const w = parseFloat(weight);

    if (!h || !w) {
      setBmi('Invalid Input');
      setStatus('');
      return;
    }

    const bmiValue = (w / (h * h)).toFixed(2);
    setBmi(bmiValue);

    if (bmiValue < 18.5) {
      setStatus('Underweight');
    } else if (bmiValue >= 18.5 && bmiValue < 24.9) {
      setStatus('Normal Weight');
    } else if (bmiValue >= 25 && bmiValue < 29.9) {
      setStatus('Overweight');
    } else {
      setStatus('Obese');
    }
  };

  return (
    <View style={styles.container}>

      <Text style={styles.title}>
        BMI Calculator
      </Text>

      <TextInput
        style={styles.input}
        placeholder="Enter Weight (kg)"
        keyboardType="numeric"
        value={weight}
        onChangeText={setWeight}
      />

      <TextInput
        style={styles.input}
        placeholder="Enter Height (cm)"
        keyboardType="numeric"
        value={height}
        onChangeText={setHeight}
      />

      <TouchableOpacity
        style={styles.button}
        onPress={calculateBMI}
      >
        <Text style={styles.buttonText}>
          Calculate BMI
        </Text>
      </TouchableOpacity>

      <Text style={styles.result}>
        BMI: {bmi}
      </Text>

      <Text style={styles.status}>
        {status}
      </Text>

    </View>
  );
}

const styles = StyleSheet.create({

  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },

  title: {
    fontSize: 30,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
  },

  input: {
    borderWidth: 1,
    borderColor: '#999',
    borderRadius: 10,
    padding: 12,
    marginBottom: 15,
    backgroundColor: '#fff',
    fontSize: 18,
  },

  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },

  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },

  result: {
    fontSize: 24,
    textAlign: 'center',
    marginTop: 10,
    fontWeight: 'bold',
  },

  status: {
    fontSize: 22,
    textAlign: 'center',
    marginTop: 10,
    color: 'green',
    fontWeight: 'bold',
  },

});
