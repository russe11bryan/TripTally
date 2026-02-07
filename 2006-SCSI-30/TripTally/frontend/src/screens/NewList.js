
import React,{useState} from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Card from '../components/Card';
import HeaderBackButton from '../components/HeaderBackButton';
import useThemedStyles from '../hooks/useThemedStyles';
import { useAuth } from '../context/AuthContext';
import { apiPost } from '../services/api';

export default function NewList({ route, navigation }){
  const { user } = useAuth();
  const returnPlace = route.params?.returnPlace; // Place to add after creating list
  const [name,setName]=useState('');
  const [loading, setLoading] = useState(false);
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root:{ flex:1, backgroundColor:colors.background, padding:16, paddingTop:48 },
    title:{ fontWeight:'800', fontSize:22, marginBottom:10, color: colors.text },
    input:{ padding:12, borderRadius:10, borderWidth:1, borderColor:colors.border, color: colors.text, backgroundColor: colors.card },
    button:{ backgroundColor: colors.accent, padding:12, borderRadius:10, alignItems:'center', marginTop:12 },
    buttonText:{ color:'#fff', fontWeight:'700' },
  }));

  const handleCreate = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a list name');
      return;
    }

    if (!user?.id) {
      Alert.alert('Error', 'You must be logged in to create a list');
      return;
    }

    try {
      setLoading(true);
      const newList = await apiPost('/saved/lists', {
        user_id: user.id,
        name: name.trim()
      });
      
      // If a place was passed, automatically add it to the new list
      if (returnPlace) {
        try {
          await apiPost('/saved/places', {
            list_id: newList.id,
            name: returnPlace.name,
            address: returnPlace.address,
            latitude: returnPlace.latitude,
            longitude: returnPlace.longitude,
          });

          Alert.alert(
            'Success!',
            `"${name.trim()}" has been created and "${returnPlace.name}" has been added to it.`,
            [
              {
                text: 'OK',
                onPress: () => navigation.navigate('SavePlace', { list: newList }),
              },
            ]
          );
        } catch (error) {
          console.error('Error adding place to new list:', error);
          Alert.alert('List Created', `"${name.trim()}" has been created, but failed to add the place. You can add it manually.`, [
            {
              text: 'OK',
              onPress: () => navigation.navigate('SavePlace', { list: newList }),
            },
          ]);
        }
      } else {
        // No place to add, ask user if they want to add places now
        Alert.alert(
          'List Created!',
          `"${name.trim()}" has been created. Would you like to add places to it now?`,
          [
            {
              text: 'Later',
              onPress: () => navigation.goBack(),
              style: 'cancel'
            },
            {
              text: 'Add Places',
              onPress: () => navigation.navigate('AddPlaceToList', { list: newList })
            }
          ]
        );
      }
    } catch (error) {
      console.error('Error creating list:', error);
      Alert.alert('Error', 'Failed to create list. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.root}>
      <HeaderBackButton onPress={() => navigation.goBack()} noLeftMargin />
      <Text style={styles.title}>New List</Text>
      <Card>
        <TextInput 
          value={name} 
          onChangeText={setName} 
          placeholder="Name the list" 
          placeholderTextColor={theme.colors.muted} 
          style={styles.input} 
          autoFocus
          editable={!loading}
        />
        <TouchableOpacity 
          onPress={handleCreate} 
          style={[styles.button, loading && { opacity: 0.5 }]}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Create</Text>
          )}
        </TouchableOpacity>
      </Card>
    </View>
  );
}
