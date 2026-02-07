import React, {useState, useRef, useEffect} from 'react';
import { View, Text, TouchableOpacity, TextInput, Image, Alert, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import HeaderBackButton from '../components/HeaderBackButton';
import useThemedStyles from '../hooks/useThemedStyles';
import { apiPost } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function RoadIncidentPage({ navigation }) {
  const { user } = useAuth();
  const [incidentType, setIncidentType] = useState(''); // Changed from description to incidentType
  const [photoUri, setPhotoUri] = useState(null);
  const [location, setLocation] = useState(null); // Store incident location
  const [userLocation, setUserLocation] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [region, setRegion] = useState({
    latitude: 1.3483,
    longitude: 103.6831,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const mapRef = useRef(null); // Reference to the map
  
  // Get user location
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') return;

        const loc = await Location.getCurrentPositionAsync({});
        const currentPos = {
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
        };
        setUserLocation(currentPos);
        setRegion({
          ...currentPos,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        });
      } catch (error) {
        console.error('Error getting location:', error);
      }
    })();
  }, []);
  
  // Incident type options with icons
  const incidentTypes = [
    { label: 'Traffic', icon: 'car-outline', color: '#FF6B35' },
    { label: 'Accident', icon: 'warning-outline', color: '#E63946' },
    { label: 'Road Closure', icon: 'close-circle-outline', color: '#9D4EDD' },
    { label: 'Police', icon: 'shield-checkmark-outline', color: '#0077B6' }
  ];
  
  const { styles, theme } = useThemedStyles(({ colors }) => ({
    root:{flex:1, backgroundColor:colors.background, paddingTop:48 },
    scrollContent: { paddingBottom: 24 },
    title:{ fontWeight: "700", fontSize: 32, marginLeft: 16, marginBottom: 10, color: colors.text },
    mapContainer: {
      marginHorizontal: 16,
      height: 300,
      borderRadius: 16,
      overflow: 'hidden',
      marginBottom: 16,
      borderWidth: 2,
      borderColor: colors.accent,
      position: 'relative',
    },
    map: {
      flex: 1,
    },
    zoomButtons: {
      position: 'absolute',
      right: 10,
      top: 10,
      gap: 8,
    },
    zoomButton: {
      backgroundColor: colors.card,
      width: 36,
      height: 36,
      borderRadius: 18,
      justifyContent: 'center',
      alignItems: 'center',
      borderWidth: 1,
      borderColor: colors.border,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
      elevation: 5,
    },
    zoomButtonText: {
      fontSize: 20,
      fontWeight: '700',
      color: colors.text,
    },
    locationText: {
      marginHorizontal: 16,
      marginBottom: 8,
      fontSize: 14,
      color: colors.muted,
      fontWeight: '600',
    },
    uploadBox:{
      marginHorizontal: 16,
      height: 160,
      borderWidth: 2,
      borderColor: colors.accent,
      borderRadius: 10,
      backgroundColor: colors.card,
      justifyContent: "center",
      alignItems: "center",
      marginBottom: 24
    },
    uploadPlus:{fontSize:40, color: colors.text },
    descTitle:{ fontWeight: "700", fontSize: 32, marginLeft: 16, marginBottom: 16, color: colors.text },
    incidentTypesContainer: {
      marginHorizontal: 16,
      marginBottom: 24,
      gap: 12,
    },
    incidentTypeButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      paddingHorizontal: 16,
      borderRadius: 12,
      borderWidth: 2,
      borderColor: colors.border,
      backgroundColor: colors.card,
    },
    incidentTypeButtonSelected: {
      borderColor: colors.accent,
      backgroundColor: colors.accent + '15',
    },
    incidentTypeIconContainer: {
      width: 32,
      height: 32,
      borderRadius: 16,
      justifyContent: 'center',
      alignItems: 'center',
      marginRight: 10,
    },
    incidentTypeText: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    incidentTypeTextSelected: {
      color: colors.accent,
      fontWeight: '700',
    },
    descBox:{
      marginHorizontal: 16,
      height: 120,
      backgroundColor: colors.card,
      borderRadius: 16,
      marginBottom: 24,
      padding: 12,
      borderWidth:1,
      borderColor: colors.border,
    },
    descInput:{fontSize:18, color: colors.text, flex:1, textAlignVertical:'top'},
    uploadButton:{
      backgroundColor:colors.accent,
      paddingVertical:12,
      paddingHorizontal:38,
      borderRadius:32,
      alignSelf: 'center',
      marginTop: 16,
      marginBottom: 24,
      flexDirection: 'row',
      alignItems: 'center',
      gap:8,
    },
    uploadIcon:{fontSize:20, color:'#fff'},
    uploadLabel:{fontSize:20, fontWeight:'700', color:"#fff"},
  }));

  // Photo picker simulation (implement with Expo ImagePicker or similar)
  const pickPhoto = async () => {
    // let result = await ImagePicker.launchImageLibraryAsync();
    // if (!result.cancelled) setPhotoUri(result.uri);
    alert('Open photo picker here');
  };

  // Handle map press to set incident location
  const handleMapPress = (event) => {
    const { coordinate } = event.nativeEvent;
    setLocation(coordinate);
  };

  // Zoom in function
  const zoomIn = () => {
    const newRegion = {
      ...region,
      latitudeDelta: region.latitudeDelta / 2,
      longitudeDelta: region.longitudeDelta / 2,
    };
    setRegion(newRegion);
    if (mapRef.current) {
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  // Zoom out function
  const zoomOut = () => {
    const newRegion = {
      ...region,
      latitudeDelta: region.latitudeDelta * 2,
      longitudeDelta: region.longitudeDelta * 2,
    };
    setRegion(newRegion);
    if (mapRef.current) {
      mapRef.current.animateToRegion(newRegion, 300);
    }
  };

  // Update region when user pans the map
  const handleRegionChangeComplete = (newRegion) => {
    setRegion(newRegion);
  };

  // Handle upload functionality
  const handleUpload = async () => {
    if (!location) {
      Alert.alert(
        "Location Required",
        "Please tap on the map to indicate where the incident occurred.",
        [{ text: "OK" }]
      );
      return;
    }

    if (!incidentType) {
      Alert.alert(
        "Incident Type Required",
        "Please select the type of incident.",
        [{ text: "OK" }]
      );
      return;
    }

    setUploading(true);

    try {
      // Submit to backend
      await apiPost('/traffic-alerts', {
        obstruction_type: incidentType,
        latitude: location.latitude,
        longitude: location.longitude,
        location_name: null, // Could add location name if needed
        reported_by: user?.id || null,
      });

      Alert.alert(
        "Success",
        `${incidentType} has been reported successfully!`,
        [
          {
            text: "OK",
            onPress: () => {
              // Reset form
              setIncidentType('');
              setLocation(null);
              setPhotoUri(null);
              
              // Navigate back to MainTabs and go to Explore tab with refresh param
              navigation.reset({
                index: 0,
                routes: [
                  {
                    name: 'MainTabs',
                    params: {
                      screen: 'Explore',
                      params: { refresh: Date.now() }
                    }
                  }
                ]
              });
            }
          }
        ]
      );
    } catch (error) {
      // Check if it's a road proximity error
      const errorMessage = error.message || 'Unknown error';
      
      if (errorMessage.includes('not near any road') || errorMessage.includes('near a road')) {
        // Don't log this error - it's expected validation
        Alert.alert(
          "Invalid Location",
          "The selected location is not near any road. Please tap on or near a road to report a traffic incident.",
          [{ text: "OK" }]
        );
      } else {
        // Log unexpected errors
        console.error('Error reporting incident:', error);
        Alert.alert(
          "Error",
          errorMessage || "Failed to report incident. Please try again.",
          [{ text: "OK" }]
        );
      }
    } finally {
      setUploading(false);
    }
  };

  // Handle back button
  const handleBack = () => {
    navigation.goBack();
  };

  return (
    <View style={styles.root}>
      {/* Back button */}
      <HeaderBackButton onPress={handleBack} />

      <ScrollView style={{ flex: 1 }} contentContainerStyle={styles.scrollContent}>
        {/* Location Map */}
        <Text style={styles.descTitle}>Incident Location</Text>
        <Text style={styles.locationText}>
          {location 
            ? `Selected: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` 
            : 'Tap on the map to mark the incident location'}
        </Text>
        <View style={styles.mapContainer}>
          <MapView
            provider={PROVIDER_GOOGLE}
            ref={mapRef}
            style={styles.map}
            region={region}
            onPress={handleMapPress}
            onRegionChangeComplete={handleRegionChangeComplete}
            zoomEnabled={true}
            zoomControlEnabled={false}
            scrollEnabled={true}
            pitchEnabled={true}
            rotateEnabled={true}
            showsUserLocation
            showsMyLocationButton={false}
          >
            {location && (
              <Marker
                coordinate={location}
                title="Incident Location"
                pinColor="red"
              />
            )}
          </MapView>
          
          {/* Zoom Controls */}
          <View style={styles.zoomButtons}>
            <TouchableOpacity 
              style={styles.zoomButton} 
              onPress={zoomIn}
              activeOpacity={0.7}
            >
              <Text style={styles.zoomButtonText}>+</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.zoomButton} 
              onPress={zoomOut}
              activeOpacity={0.7}
            >
              <Text style={styles.zoomButtonText}>−</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Title */}
        {/* <Text style={styles.title}>Add Photos</Text> */}

        {/* Photo upload box */}
        {/* <TouchableOpacity
          style={styles.uploadBox}
          onPress={pickPhoto}
          activeOpacity={0.7}
        >
          {
            photoUri ? (
              <Image source={{uri: photoUri}} style={{width: "95%", height: "95%", borderRadius: 6}} />
            ) : (
              <Text style={styles.uploadPlus}>{'＋'}</Text>
            )
          }
        </TouchableOpacity> */}

        {/* Description */}
        <Text style={styles.descTitle}>Incident Type</Text>
        <View style={styles.incidentTypesContainer}>
          {incidentTypes.map((type) => {
            const isSelected = incidentType === type.label;
            return (
              <TouchableOpacity
                key={type.label}
                style={[
                  styles.incidentTypeButton,
                  isSelected && styles.incidentTypeButtonSelected
                ]}
                onPress={() => setIncidentType(type.label)}
                activeOpacity={0.7}
              >
                <View style={styles.incidentTypeIconContainer}>
                  <Ionicons
                    name={type.icon}
                    size={24}
                    color={isSelected ? theme.colors.accent : type.color}
                  />
                </View>
                <Text style={[
                  styles.incidentTypeText,
                  isSelected && styles.incidentTypeTextSelected
                ]}>
                  {type.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Upload Button */}
        <TouchableOpacity
          style={[styles.uploadButton, uploading && { opacity: 0.6 }]}
          onPress={handleUpload}
          disabled={uploading}
        >
          {uploading ? (
            <>
              <ActivityIndicator color="#fff" />
              <Text style={styles.uploadLabel}>Reporting...</Text>
            </>
          ) : (
            <Text style={styles.uploadLabel}>Upload</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}
