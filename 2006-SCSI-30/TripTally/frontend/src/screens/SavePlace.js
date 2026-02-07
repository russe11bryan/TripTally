
import React, { useMemo, useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList, ScrollView, ActivityIndicator, Alert } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import BottomDragTab from '../components/BottomDragTab';
import { useTheme } from '../context/ThemeContext';
import { apiGet, apiDelete } from '../services/api';

export default function SavePlace({ route }) {
  const navigation = useNavigation();
  const list = route?.params?.list;
  const { theme } = useTheme();
  const styles = useMemo(() => createStyles(theme.colors), [theme]);
  const mapRef = useRef(null);

  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlace, setSelectedPlace] = useState(null);

  const fetchPlaces = async () => {
    if (!list?.id) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const data = await apiGet(`/saved/places/list/${list.id}`);
      setPlaces(data);
    } catch (error) {
      console.error('Error fetching places:', error);
      setPlaces([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch places when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      fetchPlaces();
    }, [list?.id])
  );

  const handlePlacePress = (place) => {
    setSelectedPlace(place);
    
    // Animate map to the selected place
    if (mapRef.current) {
      mapRef.current.animateToRegion({
        latitude: place.latitude,
        longitude: place.longitude,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      }, 1000);
    }
  };

  const handleDeletePlace = (place) => {
    Alert.alert(
      'Delete Place',
      `Are you sure you want to remove "${place.name}" from this list?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              await apiDelete(`/saved/places/${place.id}`);
              // Remove from local state
              setPlaces(prev => prev.filter(p => p.id !== place.id));
              if (selectedPlace?.id === place.id) {
                setSelectedPlace(null);
              }
            } catch (error) {
              console.error('Error deleting place:', error);
              Alert.alert('Error', 'Failed to delete place. Please try again.');
            }
          }
        }
      ]
    );
  };

  const handleGetDirections = (place) => {
    navigation.navigate('Directions', {
      destination: {
        latitude: place.latitude,
        longitude: place.longitude,
        name: place.name
      }
    });
  };

  return (
    <View style={{ flex: 1 }}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={{ flex: 1 }}
        initialRegion={{
          latitude: 1.3483,
          longitude: 103.6831,
          latitudeDelta: 0.1,
          longitudeDelta: 0.1,
        }}
      >
        {/* Show marker only for selected place */}
        {selectedPlace && (
          <Marker
            coordinate={{
              latitude: selectedPlace.latitude,
              longitude: selectedPlace.longitude,
            }}
            title={selectedPlace.name}
            description={selectedPlace.address}
          />
        )}
      </MapView>

      {/* Back Button */}
      <TouchableOpacity
        style={styles.closeButton}
        onPress={() => navigation.navigate('Saved')}
      >
        <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
      </TouchableOpacity>

      {/* Add Place Button */}
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => navigation.navigate('AddPlaceToList', { list })}
      >
        <Ionicons name="add" size={28} color={theme.colors.card} />
      </TouchableOpacity>

      {/* Bottom Drag Tab */}
      <BottomDragTab
        initialPosition={300}
        collapsedHeight={80}
        maxHeight={450}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.title}>{list?.name ?? 'Favourites'}</Text>
          <Text style={styles.countBadge}>{places.length} {places.length === 1 ? 'place' : 'places'}</Text>
        </View>
        
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.colors.accent} />
          </View>
        ) : places.length > 0 ? (
          <ScrollView style={styles.placesList} contentContainerStyle={styles.placesListContent} showsVerticalScrollIndicator={false}>
            {places.map((place, index) => (
              <View key={place.id} style={styles.placeItem}>
                <TouchableOpacity
                  style={styles.placeMainContent}
                  onPress={() => handlePlacePress(place)}
                >
                  <View style={styles.placeIconContainer}>
                    <Ionicons 
                      name="location" 
                      size={20} 
                      color={selectedPlace?.id === place.id ? theme.colors.accent : theme.colors.muted} 
                    />
                  </View>
                  <View style={styles.placeInfo}>
                    <Text style={[styles.placeName, selectedPlace?.id === place.id && { color: theme.colors.accent }]}>
                      {place.name}
                    </Text>
                    <Text style={styles.placeAddress}>{place.address}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={20} color={theme.colors.muted} />
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.actionButton}
                  onPress={() => handleGetDirections(place)}
                >
                  <Ionicons name="navigate" size={20} color={theme.colors.accent} />
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.deleteButton}
                  onPress={() => handleDeletePlace(place)}
                >
                  <Ionicons name="trash-outline" size={20} color="#EF4444" />
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="location-outline" size={48} color={theme.colors.muted} />
            <Text style={styles.emptyText}>No places saved yet</Text>
            <Text style={styles.emptySubtext}>Tap the + button to add places</Text>
          </View>
        )}
      </BottomDragTab>
    </View>
  );
}

const createStyles = (colors) =>
  StyleSheet.create({
    closeButton:{
      position:'absolute',
      top:50,
      left:20,
      backgroundColor: colors.card,
      borderRadius:20,
      padding:8,
      elevation:3,
      shadowColor:'#000',
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
      shadowRadius:6,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.border,
      zIndex: 10,
    },
    addButton: {
      position: 'absolute',
      top: 50,
      right: 20,
      backgroundColor: colors.accent,
      borderRadius: 20,
      width: 44,
      height: 44,
      justifyContent: 'center',
      alignItems: 'center',
      elevation: 3,
      shadowColor: '#000',
      shadowOpacity: colors.mode === 'dark' ? 0.3 : 0.15,
      shadowRadius: 6,
      zIndex: 10,
    },
    cardHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 12,
    },
    title:{
      fontWeight:'800',
      fontSize: 20,
      color: colors.text,
    },
    countBadge: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.accent,
      backgroundColor: colors.accent + '20',
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 12,
    },
    placesList: {
      flex: 1,
    },
    placesListContent: {
      flexGrow: 1,
      paddingBottom: 16,
    },
    placeItem: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: colors.border,
    },
    placeMainContent: {
      flexDirection: 'row',
      alignItems: 'center',
      flex: 1,
    },
    actionButton: {
      padding: 8,
      marginLeft: 8,
    },
    deleteButton: {
      padding: 8,
      marginLeft: 8,
    },
    placeIconContainer: {
      width: 36,
      height: 36,
      borderRadius: 18,
      backgroundColor: colors.pillAlt,
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 12,
    },
    placeInfo: {
      flex: 1,
    },
    placeName: {
      fontWeight: '700',
      fontSize: 16,
      color: colors.text,
      marginBottom: 2,
    },
    placeAddress: {
      fontSize: 14,
      color: colors.muted,
    },
    emptyState: {
      alignItems: 'center',
      paddingVertical: 32,
    },
    emptyText: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginTop: 12,
    },
    emptySubtext: {
      fontSize: 14,
      color: colors.muted,
      marginTop: 4,
    },
    loadingContainer: {
      paddingVertical: 32,
      justifyContent: 'center',
      alignItems: 'center',
    },
  });
