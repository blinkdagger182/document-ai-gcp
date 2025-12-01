import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker'; // or react-native-image-picker

const API_URL = 'https://paddleocr-ui-builder-62nie56atq-uc.a.run.app';

// Component to upload image and get UI components
export const ImageToUIUploader = () => {
  const [loading, setLoading] = useState(false);
  const [components, setComponents] = useState([]);

  const pickAndProcessImage = async () => {
    try {
      // Pick image
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
      });

      if (result.canceled) return;

      setLoading(true);

      // Create FormData
      const formData = new FormData();
      formData.append('file', {
        uri: result.assets[0].uri,
        type: 'image/jpeg',
        name: 'screenshot.jpg',
      });

      // Upload to API
      const response = await fetch(`${API_URL}/ui/generate`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type - let fetch handle it
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      if (data.success && data.components) {
        setComponents(data.components);
        Alert.alert('Success', `Generated ${data.components.length} UI components!`);
      } else {
        throw new Error('No components generated');
      }
    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.uploadButton}
        onPress={pickAndProcessImage}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="white" />
        ) : (
          <Text style={styles.uploadButtonText}>
            📸 Upload Image & Generate UI
          </Text>
        )}
      </TouchableOpacity>

      {components.length > 0 && (
        <ScrollView style={styles.componentsContainer}>
          <Text style={styles.title}>Generated Components:</Text>
          <DynamicUIRenderer components={components} />
        </ScrollView>
      )}
    </View>
  );
};

// Component to render the generated UI
const DynamicUIRenderer = ({ components }) => {
  return (
    <View style={styles.rendererContainer}>
      {components.map((component) => {
        switch (component.type) {
          case 'heading':
            return (
              <Text
                key={component.id}
                style={[
                  styles.heading,
                  component.level === 1 ? styles.h1 : styles.h2,
                ]}
              >
                {component.text}
              </Text>
            );

          case 'input':
            return (
              <View key={component.id} style={styles.inputContainer}>
                {component.label && (
                  <Text style={styles.inputLabel}>{component.label}</Text>
                )}
                <TextInput
                  placeholder={component.placeholder}
                  keyboardType={
                    component.inputType === 'email'
                      ? 'email-address'
                      : 'default'
                  }
                  secureTextEntry={component.inputType === 'password'}
                  style={styles.input}
                />
              </View>
            );

          case 'button':
            return (
              <TouchableOpacity
                key={component.id}
                style={[
                  styles.button,
                  component.variant === 'primary'
                    ? styles.primaryButton
                    : styles.secondaryButton,
                ]}
                onPress={() => Alert.alert('Button Pressed', component.text)}
              >
                <Text style={styles.buttonText}>{component.text}</Text>
              </TouchableOpacity>
            );

          case 'checkbox':
            return (
              <View key={component.id} style={styles.checkboxContainer}>
                <View style={styles.checkbox} />
                <Text style={styles.checkboxLabel}>{component.text}</Text>
              </View>
            );

          case 'link':
            return (
              <TouchableOpacity key={component.id} style={styles.linkContainer}>
                <Text style={styles.link}>{component.text}</Text>
              </TouchableOpacity>
            );

          case 'text':
          default:
            return (
              <Text key={component.id} style={styles.text}>
                {component.text}
              </Text>
            );
        }
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  uploadButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  componentsContainer: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  rendererContainer: {
    backgroundColor: '#f9f9f9',
    padding: 15,
    borderRadius: 10,
  },
  heading: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  h1: {
    fontSize: 28,
  },
  h2: {
    fontSize: 22,
  },
  inputContainer: {
    marginBottom: 15,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 5,
    color: '#333',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 12,
    borderRadius: 8,
    fontSize: 16,
    backgroundColor: 'white',
  },
  button: {
    padding: 15,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#8E8E93',
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderRadius: 4,
    marginRight: 10,
  },
  checkboxLabel: {
    fontSize: 16,
  },
  linkContainer: {
    marginBottom: 12,
  },
  link: {
    color: '#007AFF',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
  text: {
    fontSize: 16,
    marginBottom: 10,
    lineHeight: 22,
  },
});

export default ImageToUIUploader;
