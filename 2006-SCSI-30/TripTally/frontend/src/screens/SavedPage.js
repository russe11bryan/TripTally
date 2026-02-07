import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, FlatList, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';
import Card from '../components/Card';
import useThemedStyles from '../hooks/useThemedStyles';
import { useAuth } from '../context/AuthContext';
import { apiGet, apiDelete, apiPut } from '../services/api';

export default function SavedPage({ navigation }){
  const { user } = useAuth();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userLocations, setUserLocations] = useState({ home: null, work: null });

  const fetchUserLocations = async () => {
    if (!user?.id) return;
    
    try {
      const userData = await apiGet(`/users/${user.id}`);
      setUserLocations({
        home: userData.home_latitude && userData.home_longitude ? {
          latitude: userData.home_latitude,
          longitude: userData.home_longitude,
          address: userData.home_address,
        } : null,
        work: userData.work_latitude && userData.work_longitude ? {
          latitude: userData.work_latitude,
          longitude: userData.work_longitude,
          address: userData.work_address,
        } : null,
      });
    } catch (error) {
      console.error('Error fetching user locations:', error);
    }
  };

  const fetchLists = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const data = await apiGet(`/saved/lists/user/${user.id}`);
      setLists(data);
    } catch (error) {
      console.error('Error fetching saved lists:', error);
      // Keep existing data on error
    } finally {
      setLoading(false);
    }
  };

  // Fetch lists and locations when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      fetchLists();
      fetchUserLocations();
    }, [user?.id])
  );

  const handleEditLocation = (locationType) => {
    navigation.navigate('SetLocation', { locationType });
  };

  const handleRemoveLocation = (locationType) => {
    const locationName = locationType === 'home' ? 'Home' : 'Work';
    
    Alert.alert(
      `Remove ${locationName}`,
      `Are you sure you want to remove your ${locationName.toLowerCase()} location?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => removeLocation(locationType)
        }
      ]
    );
  };

  const removeLocation = async (locationType) => {
    if (!user?.id) return;
    
    try {
      const updateData = locationType === 'home' ? {
        home_latitude: null,
        home_longitude: null,
        home_address: null,
      } : {
        work_latitude: null,
        work_longitude: null,
        work_address: null,
      };
      
      await apiPut(`/users/${user.id}/locations`, updateData);
      
      // Refetch user locations to ensure UI is in sync with backend
      await fetchUserLocations();
      
      Alert.alert('Success', `${locationType === 'home' ? 'Home' : 'Work'} location removed.`);
    } catch (error) {
      console.error(`Error removing ${locationType} location:`, error);
      Alert.alert('Error', `Failed to remove ${locationType} location. Please try again.`);
    }
  };

  const handleDeleteList = (list) => {
    const placeCount = list.place_count || 0;
    
    if (placeCount > 0) {
      // List has places, show confirmation
      Alert.alert(
        'Delete List',
        `"${list.name}" contains ${placeCount} ${placeCount === 1 ? 'place' : 'places'}. Are you sure you want to delete it? This action cannot be undone.`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: () => deleteList(list.id)
          }
        ]
      );
    } else {
      // List is empty, show simpler confirmation
      Alert.alert(
        'Delete List',
        `Are you sure you want to delete "${list.name}"?`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Delete',
            style: 'destructive',
            onPress: () => deleteList(list.id)
          }
        ]
      );
    }
  };

  const deleteList = async (listId) => {
    try {
      await apiDelete(`/saved/lists/${listId}`);
      // Remove from local state
      setLists(prev => prev.filter(list => list.id !== listId));
    } catch (error) {
      console.error('Error deleting list:', error);
      Alert.alert('Error', 'Failed to delete list. Please try again.');
    }
  };

  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root: {
      flex:1,
      backgroundColor: colors.background,
      paddingTop:60,
    },
    header: {
      flexDirection:'row',
      justifyContent:'space-between',
      paddingHorizontal:16,
      marginBottom:10,
      alignItems:'center',
    },
    title: {
      fontWeight:'800',
      fontSize:22,
      color: colors.text,
    },
    newList: {
      color: colors.accent,
      fontWeight:'600',
    },
    listTitle: {
      fontWeight:'700',
      color: colors.text,
      flex: 1,
    },
    listMeta: {
      color: colors.muted,
      marginTop:4,
      flex: 1,
    },
    listContainer: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    listInfo: {
      flex: 1,
    },
    addButton: {
      backgroundColor: colors.accent,
      borderRadius: 15,
      width: 28,
      height: 28,
      justifyContent: 'center',
      alignItems: 'center',
      marginLeft: 12,
    },
    deleteButton: {
      padding: 8,
      marginLeft: 8,
    },
    listActions: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    locationSection: {
      marginHorizontal: 16,
      marginBottom: 16,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
      marginBottom: 8,
      paddingHorizontal: 4,
    },
    locationCard: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: 12,
      marginBottom: 8,
    },
    locationInfo: {
      flex: 1,
    },
    locationName: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 2,
    },
    locationAddress: {
      fontSize: 14,
      color: colors.muted,
    },
    locationNotSet: {
      fontSize: 14,
      color: colors.muted,
      fontStyle: 'italic',
    },
    editButton: {
      padding: 8,
      marginLeft: 8,
    },
  }));

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>Saved</Text>
        <TouchableOpacity onPress={()=>navigation.navigate('NewList')}>
          <Text style={styles.newList}>+ New List</Text>
        </TouchableOpacity>
      </View>

      {/* Home and Work Locations Section */}
      <View style={styles.locationSection}>
        <Text style={styles.sectionTitle}>Quick Access</Text>
        
        {/* Home Location */}
        <Card style={styles.locationCard}>
          <Ionicons name="home" size={24} color={theme.colors.accent} />
          <View style={[styles.locationInfo, { marginLeft: 12 }]}>
            <Text style={styles.locationName}>Home</Text>
            {userLocations.home ? (
              <Text style={styles.locationAddress} numberOfLines={1}>
                {userLocations.home.address}
              </Text>
            ) : (
              <Text style={styles.locationNotSet}>Not set</Text>
            )}
          </View>
          <View style={styles.listActions}>
            <TouchableOpacity 
              style={styles.editButton}
              onPress={() => handleEditLocation('home')}
            >
              <Ionicons 
                name={userLocations.home ? "create-outline" : "add-circle-outline"} 
                size={22} 
                color={theme.colors.accent} 
              />
            </TouchableOpacity>
            {userLocations.home && (
              <TouchableOpacity 
                style={styles.deleteButton}
                onPress={() => handleRemoveLocation('home')}
              >
                <Ionicons name="trash-outline" size={20} color="#EF4444" />
              </TouchableOpacity>
            )}
          </View>
        </Card>

        {/* Work Location */}
        <Card style={styles.locationCard}>
          <Ionicons name="briefcase" size={24} color={theme.colors.accent} />
          <View style={[styles.locationInfo, { marginLeft: 12 }]}>
            <Text style={styles.locationName}>Work</Text>
            {userLocations.work ? (
              <Text style={styles.locationAddress} numberOfLines={1}>
                {userLocations.work.address}
              </Text>
            ) : (
              <Text style={styles.locationNotSet}>Not set</Text>
            )}
          </View>
          <View style={styles.listActions}>
            <TouchableOpacity 
              style={styles.editButton}
              onPress={() => handleEditLocation('work')}
            >
              <Ionicons 
                name={userLocations.work ? "create-outline" : "add-circle-outline"} 
                size={22} 
                color={theme.colors.accent} 
              />
            </TouchableOpacity>
            {userLocations.work && (
              <TouchableOpacity 
                style={styles.deleteButton}
                onPress={() => handleRemoveLocation('work')}
              >
                <Ionicons name="trash-outline" size={20} color="#EF4444" />
              </TouchableOpacity>
            )}
          </View>
        </Card>
      </View>

      {/* Saved Lists Section */}
      <Text style={[styles.sectionTitle, { marginHorizontal: 20, marginBottom: 8 }]}>My Lists</Text>
      
      {loading ? (
        <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
          <ActivityIndicator size="large" color={theme.colors.accent} />
        </View>
      ) : lists.length === 0 ? (
        <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 32}}>
          <Text style={{color: theme.colors.muted, textAlign: 'center', fontSize: 16}}>
            No saved lists yet. Create your first list to get started!
          </Text>
        </View>
      ) : (
        <FlatList data={lists} keyExtractor={i=>i.id.toString()}
          renderItem={({item}) => (
            <Card style={{marginHorizontal:16, marginBottom:10, padding: 12}}>
              <View style={styles.listContainer}>
                <TouchableOpacity 
                  style={styles.listInfo}
                  onPress={()=>navigation.navigate('SavePlace', {list:item})}
                >
                  <Text style={styles.listTitle}>{item.name}</Text>
                  <Text style={styles.listMeta}>{item.place_count || 0} places</Text>
                </TouchableOpacity>
                
                <View style={styles.listActions}>
                  <TouchableOpacity 
                    style={styles.addButton}
                    onPress={() => navigation.navigate('AddPlaceToList', { list: item })}
                  >
                    <Ionicons name="add" size={16} color="#fff" />
                  </TouchableOpacity>
                  
                  <TouchableOpacity 
                    style={styles.deleteButton}
                    onPress={() => handleDeleteList(item)}
                  >
                    <Ionicons name="trash-outline" size={20} color="#EF4444" />
                  </TouchableOpacity>
                </View>
              </View>
            </Card>
          )}
        />
      )}
    </View>
  );
}
